"""
Merge project rows that describe the same asset under different names.

Reports name one asset several ways — "Ixtaca", "Ixtaca Project", "Ixtaca
Gold-Silver Project", "Ixtaca (Tuligtic Property)" — and extract_resources
originally matched project names exactly, so each variant created its own
Project. Almaden's single Ixtaca deposit ended up as six rows, which duplicated
it through Grade Ranker and made Resource Growth read as six one-report
projects.

Projects are grouped per company by their identifying tokens (parentheticals,
punctuation and generic words like "project"/"gold" removed), merging a group
when the token sets are equal or one is a strict subset of another. That keeps
"True North Gold Mine" and "True North Gold Project" together while leaving
genuinely different names — "Ixtaca" and "Tuligtic" — apart, because
over-merging two real projects is worse than leaving two rows for one.

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
    'project', 'property', 'properties', 'deposit', 'deposits', 'mine',
    'mines', 'complex', 'claims', 'claim', 'gold', 'silver', 'copper',
    'zinc', 'lead', 'nickel', 'lithium', 'uranium', 'the', 'and',
}


def identity_tokens(name):
    text = re.sub(r'\([^)]*\)', ' ', name or '')
    text = re.sub(r'[^a-z0-9\s]', ' ', text.lower())
    return frozenset(t for t in text.split() if t and t not in NOISE_WORDS)


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

        # Union-find over the equal-or-subset relation, so a chain of variants
        # ("north", "true north", "true north gold mine") lands in one group.
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
                if ta == tb or ta < tb or tb < ta:
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
