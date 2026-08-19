"""
Merge project rows that describe the same asset under different names.

Reports name one asset several ways — "Ixtaca", "Ixtaca Project", "Ixtaca
Gold-Silver Project", "Ixtaca (Tuligtic Property)" — and extract_resources
originally matched project names exactly, so each variant created its own
Project. Almaden's single Ixtaca deposit ended up as six rows, which duplicated
it through Grade Ranker and made Resource Growth read as six one-report
projects.

Projects are grouped per company by their identifying tokens (parentheticals,
punctuation and structural words like "project"/"property" removed), merging
only when the token sets are *equal*. That keeps "True North Gold Mine" and
"True North Gold Project" together while leaving genuinely different names —
"Ixtaca" and "Tuligtic" — apart.

An earlier version also merged on strict subset. It over-merged: "Uravan
Properties" reduces to {uravan}, a subset of all three of Urano's Northern,
Central and Southern Uravan Districts, so union-find pulled three distinct
districts into one row. Equality-only leaves a few variants unmerged
("Ixtaca Gold-Silver Project" keeps its own row) — the right trade, since
merging two real projects destroys data while a leftover duplicate does not.

Within a group the survivor is the project with the most resource estimates,
tie-broken by lowest id, so the longest history wins.

Usage:
    python manage.py merge_duplicate_projects --dry-run
    python manage.py merge_duplicate_projects
"""

import re
from collections import defaultdict

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count

from core.models import (
    Company, Document, EconomicStudy, Project, ResourceEstimate,
)

NOISE_WORDS = {
    # Structural words only. Commodity names are deliberately NOT noise:
    # stripping them collapsed "Nickel Island Property" to "Island", which then
    # matched "Rice Island Property" — two unrelated Wolfden assets.
    'project', 'projects', 'property', 'properties', 'deposit', 'deposits',
    'mine', 'mines', 'complex', 'claims', 'claim', 'the', 'and',
}


def identity_tokens(name):
    text = re.sub(r'\([^)]*\)', ' ', name or '')
    text = re.sub(r'[^a-z0-9\s]', ' ', text.lower())
    return frozenset(t for t in text.split() if t and t not in NOISE_WORDS)


# Cases where one asset is reported under names that share no identifying token,
# so no automatic rule can connect them without also merging real neighbours.
# Each entry is (company name, [names that are the same asset]); the names are
# matched case-insensitively and exactly, so this cannot drift onto a new
# project. Add an entry only after confirming the asset from the reports —
# Erdene's "Bayan Khundii" and "Bayan Khundii and Dark Horse" are deliberately
# absent, because Dark Horse is a separate deposit.
CURATED_ALIASES = [
    # Ixtaca is the deposit; Tuligtic is the property that hosts it.
    ('Almaden Minerals', [
        'Ixtaca Project',
        'Ixtaca Gold-Silver Project',
        'Tuligtic Project',
    ]),
    # 1911 Gold's True North mine and mill are reported as both "Mine" and
    # "Complex". Ogama-Rockland is a separate deposit and stays out.
    ('1911 Gold Corporation', [
        'True North Gold Mine',
        'True North Complex',
    ]),
]


class Command(BaseCommand):
    help = "Merge duplicate Project rows created from naming variants."

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **opts):
        dry_run = opts['dry_run']
        merged_groups = merged_rows = 0

        for company in Company.objects.filter(is_deleted=False).iterator():
            projects = list(Project.objects.filter(company=company))
            if len(projects) < 2:
                continue

            groups = self._group(projects)
            for survivor, duplicates in groups:
                if not duplicates:
                    continue
                merged_groups += 1
                merged_rows += len(duplicates)

                names = ', '.join(f'"{p.name}"' for p in duplicates)
                self.stdout.write(
                    f'  {company.name[:28]:28s} keep "{survivor.name}" '
                    f'<- {len(duplicates)} dup(s): {names}'
                )
                if dry_run:
                    continue

                with transaction.atomic():
                    ids = [p.id for p in duplicates]
                    ResourceEstimate.objects.filter(project_id__in=ids).update(project=survivor)
                    EconomicStudy.objects.filter(project_id__in=ids).update(project=survivor)
                    Document.objects.filter(project_id__in=ids).update(project=survivor)
                    Project.objects.filter(id__in=ids).delete()

        self.stdout.write(self.style.SUCCESS(
            f'\n{merged_groups} group(s), {merged_rows} duplicate project(s) '
            f'{"would be" if dry_run else ""} merged'
        ))
        if dry_run:
            self.stdout.write(self.style.NOTICE('Dry run — nothing written.'))

    def _group(self, projects):
        """Return [(survivor, [duplicates])] for one company."""
        tokenized = [(p, identity_tokens(p.name)) for p in projects]
        tokenized = [(p, t) for p, t in tokenized if t]

        # A curated alias forces one shared token set across its listed names,
        # which then flows through the normal equality grouping below.
        company_name = projects[0].company.name
        for alias_company, names in CURATED_ALIASES:
            if alias_company.lower() != company_name.lower():
                continue
            lowered = {n.lower() for n in names}
            shared = frozenset({'curated-alias', alias_company.lower(), names[0].lower()})
            tokenized = [(p, shared if p.name.lower() in lowered else t)
                         for p, t in tokenized]

        # Union-find over token-set equality. Equality is transitive, so this is
        # just a grouping; it stays as union-find only so a looser relation
        # can be reintroduced later without restructuring.
        parent = {p.id: p.id for p, _ in tokenized}

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(a, b):
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[rb] = ra

        for i, (pa, ta) in enumerate(tokenized):
            for pb, tb in tokenized[i + 1:]:
                # Equality only. The subset rule let a short generic name
                # ("Uravan Properties") bridge three distinct districts through
                # union-find, and produced 131 merges where many were wrong.
                if ta == tb:
                    union(pa.id, pb.id)

        clusters = defaultdict(list)
        by_id = {p.id: p for p, _ in tokenized}
        for pid in parent:
            clusters[find(pid)].append(by_id[pid])

        counts = {
            row['project_id']: row['n']
            for row in ResourceEstimate.objects
            .filter(project_id__in=by_id)
            .values('project_id')
            .annotate(n=Count('id'))
        }

        result = []
        for members in clusters.values():
            if len(members) < 2:
                continue
            members.sort(key=lambda p: (-counts.get(p.id, 0), p.id))
            result.append((members[0], members[1:]))
        return result
