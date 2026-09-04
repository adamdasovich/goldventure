"""
Target-directed technical-report hunter.

A NewsReportFlag records a news release whose *title* mentions a technical
report. The release is an announcement; the document we need in Docling and
ChromaDB is a separate 200-400 page NI 43-101 that lives somewhere else. Only
19 of 218 pending flags have a news URL that is itself a PDF, and only 107 have
any full_text stored, so link extraction alone resolves a minority.

crawl_technical_documents() in website_crawler.py sweeps a company for every PDF
on its technical pages. That is undirected: given "DLP Announces Positive PEA
for the Aurora Project" it returns every PDF on the site with no way to pick the
right one. This module is the directed counterpart — it takes a specific flag,
derives what document to look for, finds candidates, and ranks them.

Three things shape the design:

  * NI 43-101 s.4.2 gives an issuer 45 days from announcing results to file the
    technical report. For a release that announces results, the document
    frequently does not exist yet on the day we flag it, so a single attempt is
    guaranteed to fail. Hunts retry on a backoff until the filing window closes.

  * Some flagged releases imply no document at all ("Commences PEA at Clarence
    Stream", "Targets October Update to Roger MRE"). Those are triaged out
    before any browser starts, rather than re-crawled every cycle.

  * 218 pending flags belong to only 113 companies. Candidates are gathered per
    company and scored against every flag for that company, which removes 105
    redundant site crawls.
"""

import asyncio
import logging
import re
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# NI 43-101 s.4.2: the technical report must be filed within 45 days of first
# disclosing the results. Grace covers late filers and slow website updates —
# the report reaching SEDAR does not mean it reached the company's own site the
# same day, and the company site is the only source we search.
FILING_WINDOW_DAYS = 45
FILING_GRACE_DAYS = 30

# Stop hunting a flag after this many attempts even if the window is still open.
MAX_HUNT_ATTEMPTS = 6

# Backoff between attempts, indexed by attempt number. A report filed on day 45
# should be picked up within a few days of appearing without us crawling the
# same site nightly for six weeks.
HUNT_BACKOFF_DAYS = [1, 3, 7, 14, 21, 30]

# Score at or above which the top candidate is queued to the GPU without review.
AUTO_QUEUE_THRESHOLD = 70

# --------------------------------------------------------------------------
# Triage
# --------------------------------------------------------------------------

# Order matters: "Announces Filing of NI 43-101 Technical Report" is a filing,
# not a results announcement, so FILED is tested before RESULTS.
_FILED_PATTERNS = re.compile(
    r'\b(files?|filed|filing|has\s+filed|available\s+on\s+sedar|posted\s+(?:on|to)|'
    r'publishes|published|releases\s+the\s+technical\s+report)\b',
    re.IGNORECASE,
)

# Forward-looking: the report is intended, commissioned or in progress. There is
# no document to find, so these never reach a browser.
_FORWARD_PATTERNS = re.compile(
    r'\b(toward|towards|commenc\w*|engag\w*|award\w*|retain\w*|initiat\w*|'
    r'plans?\s+to|intends?\s+to|expects?\s+to|upcoming|targets?|'
    r'is\s+preparing|will\s+(?:complete|deliver|prepare)|on\s+track\s+(?:to|for))\b',
    re.IGNORECASE,
)

_RESULTS_PATTERNS = re.compile(
    r'\b(announc\w*|report\w*|deliver\w*|complet\w*|positive|results?\s+of|'
    r'receives?|provides?)\b',
    re.IGNORECASE,
)

# Corporate actions that are unambiguously not technical reports, whatever else
# the title says. Checked before everything: "White Gold Announces Filing of
# Management Information Circular ..." reads as a filing to the pattern above,
# and hunting it would crawl a site looking for a document that does not exist.
_NON_REPORT_CORPORATE = re.compile(
    r'\b(management\s+information\s+circular|information\s+circular|'
    r'court\s+approval|plan\s+of\s+arrangement|spin[\s-]?(?:out|off)|'
    r'annual\s+general\s+meeting|\bagm\b|private\s+placement|bought\s+deal|'
    r'financial\s+statements?|md&a|proxy|warrant\s+exercise|stock\s+option|'
    r'name\s+change|share\s+consolidation|listing\s+application)\b',
    re.IGNORECASE,
)

# Drill and assay results. These routinely mention a resource estimate in
# passing ("... as it advances toward a maiden resource estimate"), which is why
# they land in the flag queue at all, but the release announces assays, not a
# report. Checked after FILED so "Files NI 43-101 on the drill program" still
# counts as a filing.
_DRILL_RESULTS = re.compile(
    r'\b(intersects?|intercepts?|drills?|drilling|assays?|'
    r'\d+(?:\.\d+)?\s*g/t|grams?\s+per\s+tonne|'
    r'metres?\s+of\s+\d|meters?\s+of\s+\d|drill\s+(?:hole|program|results)|'
    r'step[\s-]out|infill)\b',
    re.IGNORECASE,
)

# Report nouns, used to test what a filing verb is actually filing.
_REPORT_NOUN = re.compile(
    r'ni\s*43-?101|43-101|technical\s+report|preliminary\s+economic\s+assessment|'
    r'pre-?feasibility|feasibility\s+study|mineral\s+resource\s+estimate|'
    r'resource\s+estimate|mineral\s+reserve|scoping\s+study|'
    r'(?<![a-z0-9])(?:pea|pfs|dfs|mre)(?![a-z0-9])',
    re.IGNORECASE,
)

# How far from a filing verb a report noun still counts as its object. Wide
# enough for "Filing of Management Information Circular and Technical Report",
# narrow enough that "Elects to File ... Financial Statements" does not reach a
# report mentioned at the far end of a long headline.
_FILING_PROXIMITY_AFTER = 70
_FILING_PROXIMITY_BEFORE = 40


def _is_report_filing(title: str) -> bool:
    """
    True when a filing verb in the title is actually filing a technical report.

    Presence of both a filing verb and a report noun is not enough on its own —
    mining headlines bundle several announcements, and a release can file
    financial statements while merely mentioning a PEA elsewhere. Proximity is
    what distinguishes "Files NI 43-101 Technical Report" from "Elects to File
    Semi-annual Interim Financial Statements".
    """
    for verb in _FILED_PATTERNS.finditer(title):
        window = title[max(0, verb.start() - _FILING_PROXIMITY_BEFORE):
                       verb.end() + _FILING_PROXIMITY_AFTER]
        if _REPORT_NOUN.search(window):
            return True
    return False


CATEGORY_FILED = 'filed'
CATEGORY_RESULTS = 'results'
CATEGORY_FORWARD = 'forward'
CATEGORY_UNKNOWN = 'unknown'

# Categories worth spending a browser on.
HUNTABLE_CATEGORIES = {CATEGORY_FILED, CATEGORY_RESULTS, CATEGORY_UNKNOWN}


def classify_release(title: str) -> str:
    """
    Decide what a flagged release implies about the document's existence.

    'filed'   -> the report exists now; hunt immediately.
    'results' -> results disclosed, report due within 45 days; hunt and retry.
    'forward' -> report intended or in progress; nothing to find, do not hunt.
    'unknown' -> no signal either way; hunt, but at lower priority.
    """
    if not title:
        return CATEGORY_UNKNOWN
    # A genuine filing wins over everything, including a corporate action named
    # in the same headline. Releases routinely bundle them: "Abasca Files NI
    # 43-101 Technical Report, Commences Summer Exploration Program ... and
    # Elects to File Semi-annual Interim Financial Statements" both files a
    # technical report and announces financials, and "White Gold Announces
    # Filing of Management Information Circular and Technical Report" files a
    # report alongside the circular. Suppressing those on the corporate mention
    # discarded two real reports out of a 45-flag sample.
    if _is_report_filing(title):
        return CATEGORY_FILED
    # Corporate actions with only an incidental report mention — e.g. a
    # placement raised to fund a PEA. Nothing is being filed.
    if _NON_REPORT_CORPORATE.search(title):
        return CATEGORY_FORWARD
    # Drill/assay releases mention resource estimates in passing; the release
    # itself is not a report and there is nothing on the site to find.
    if _DRILL_RESULTS.search(title):
        return CATEGORY_FORWARD
    if _FORWARD_PATTERNS.search(title):
        return CATEGORY_FORWARD
    if _RESULTS_PATTERNS.search(title):
        return CATEGORY_RESULTS
    return CATEGORY_UNKNOWN


# --------------------------------------------------------------------------
# Report type
# --------------------------------------------------------------------------

# Ordered most specific first — 'feasibility study' must not win on a title that
# says 'prefeasibility study'.
_REPORT_TYPE_PATTERNS = [
    ('pea', re.compile(r'preliminary\s+economic\s+assessment|(?<![a-z0-9])pea(?![a-z0-9])', re.I)),
    # pre[\s-]? rather than pre-?: titles write "Pre Feasibility" with a space,
    # and the separator-collapsed comparison view turns "pre-feasibility" into
    # exactly that — a hyphen-only pattern classified those as dfs.
    ('pfs', re.compile(r'pre[\s-]?feasibility|(?<![a-z0-9])pfs(?![a-z0-9])', re.I)),
    ('dfs', re.compile(r'definitive\s+feasibility|(?<!pre)(?<!pre-)(?<!pre )feasibility\s+study|(?<![a-z0-9])dfs(?![a-z0-9])', re.I)),
    ('mre', re.compile(r'mineral\s+resource\s+estimate|resource\s+estimate|mineral\s+reserve|(?<![a-z0-9])mre(?![a-z0-9])', re.I)),
    ('ni43101', re.compile(r'ni\s*43-?101|43-101|technical\s+report', re.I)),
]


def detect_report_type(title: str) -> str:
    """Best-guess report type from the release title, for candidate scoring."""
    for name, pattern in _REPORT_TYPE_PATTERNS:
        if pattern.search(title or ''):
            return name
    return 'ni43101'


# --------------------------------------------------------------------------
# Project identification
# --------------------------------------------------------------------------

# Project names in the DB carry list numbering and commodity/type suffixes:
# "3. Black Point Project", "Valeriano Copper-Gold Project".
_PROJECT_PREFIX = re.compile(r'^\s*\d+[\.\)]\s*')
_PROJECT_SUFFIX = re.compile(
    r'\s+(?:gold|silver|copper|zinc|lead|nickel|lithium|uranium|antimony|'
    r'cobalt|graphite|moly(?:bdenum)?|rare\s+earths?|polymetallic|'
    r'precious\s+metals?)?[\s-]*(?:project|property|mine|deposit)s?\s*$',
    re.IGNORECASE,
)


# Normalized names that identify nothing on their own.
#
# The suffix stripper reduces "Silver Project" to "silver", "Gold Property" to
# "gold" and "North Deposit" to "north". Those then match their own word in any
# release title and in most candidate filenames — and project_matched gates
# auto-queueing, so a spurious match can send an unrelated document to the GPU
# without review. Three real projects normalize this way today ('Silver
# Project', and two 'Victory' variants which are distinctive enough to keep).
_GENERIC_PROJECT_NAMES = {
    # commodities
    'gold', 'silver', 'copper', 'zinc', 'lead', 'nickel', 'lithium', 'uranium',
    'cobalt', 'graphite', 'antimony', 'molybdenum', 'moly', 'platinum',
    'palladium', 'iron', 'tin', 'tungsten', 'potash', 'phosphate', 'coal',
    'diamond', 'diamonds', 'rare earth', 'rare earths', 'precious metals',
    'base metals', 'critical minerals', 'polymetallic',
    # generic mining nouns left behind when a suffix does not strip cleanly
    'project', 'projects', 'property', 'properties', 'mine', 'mines',
    'deposit', 'deposits', 'claims', 'concession', 'target', 'targets',
    'district', 'land package', 'portfolio',
    # bare directions and positions
    'north', 'south', 'east', 'west', 'central', 'main', 'upper', 'lower',
}


def _collapse(text: str) -> str:
    """Punctuation to single spaces, for separator-insensitive comparison."""
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9]+', ' ', (text or '').lower())).strip()


def normalize_project_name(name: str) -> str:
    """Reduce a stored Project.name to the distinctive part used for matching."""
    if not name:
        return ''
    cleaned = _PROJECT_PREFIX.sub('', name)
    cleaned = _PROJECT_SUFFIX.sub('', cleaned)
    cleaned = re.sub(r'[^\w\s-]', ' ', cleaned)
    return re.sub(r'\s+', ' ', cleaned).strip().lower()


def match_project(title: str, project_names: List[str], company_name: str = '') -> str:
    """
    Find which of the company's known projects a release refers to.

    Matching against real Project rows beats parsing the title, because 390 of
    396 companies have project records and the stored names are authoritative.
    The longest match wins: a company with both "Clarence" and "Clarence Stream"
    should resolve the more specific one.

    A project whose name is already part of the company's name is skipped.
    "White Gold Corp" owns the "White Gold Project" and "Prince Silver Corp."
    the "Prince" property, so those names appear in every release the company
    issues and identify nothing. Matching them would attach a project to
    releases that never mentioned one and then score candidates against it.
    """
    if not title:
        return ''
    title_lower = title.lower()
    # Separator-insensitive view, so a project stored as "Loki Flake" still
    # matches a title writing it "Loki-Flake". Scoring already compares this
    # way; matching did not, which made the two inconsistent.
    title_collapsed = _collapse(title)
    company_collapsed = _collapse(company_name)

    best = ''
    for raw in project_names:
        normalized = normalize_project_name(raw)
        # One-word names below 4 characters match too much to be useful.
        if len(normalized) < 4:
            continue
        # A commodity or generic noun is not an identifier. See
        # _GENERIC_PROJECT_NAMES.
        if normalized in _GENERIC_PROJECT_NAMES:
            continue
        # A project whose name is inside the company's name identifies nothing.
        if company_collapsed and _collapse(normalized) in company_collapsed:
            continue
        pattern = r'(?<![a-z0-9])' + re.escape(normalized) + r'(?![a-z0-9])'
        collapsed_pattern = (r'(?<![a-z0-9])'
                             + re.escape(_collapse(normalized)) + r'(?![a-z0-9])')
        if (re.search(pattern, title_lower)
                or re.search(collapsed_pattern, title_collapsed)):
            if len(normalized) > len(best):
                best = normalized
    return best


# --------------------------------------------------------------------------
# Hunt target
# --------------------------------------------------------------------------


@dataclass
class HuntTarget:
    """What a single flag is looking for."""
    flag_id: int
    title: str
    news_url: str
    release_date: object          # datetime.date
    category: str
    report_type: str
    project: str
    company_name: str
    company_website: str
    candidates: List[Dict] = field(default_factory=list)


def build_target(flag, project_names: List[str]) -> HuntTarget:
    """Derive a search target from a NewsReportFlag."""
    news = flag.news_release
    title = news.title or ''
    return HuntTarget(
        flag_id=flag.id,
        title=title,
        news_url=news.url or '',
        release_date=news.release_date,
        category=classify_release(title),
        report_type=detect_report_type(title),
        project=match_project(title, project_names, news.company.name),
        company_name=news.company.name,
        company_website=news.company.website or '',
    )


# --------------------------------------------------------------------------
# Candidate extraction
# --------------------------------------------------------------------------

# Links that are documents even though the href has no .pdf extension —
# download handlers and viewer routes are common on IR platforms.
_DOWNLOAD_HREF = re.compile(
    r'/(?:download|getfile|get-file|document|documents|file|attachment|viewer)'
    r'[/?=]|[?&](?:file|doc|document|id|attachment)=',
    re.IGNORECASE,
)

_DOC_TEXT_HINT = re.compile(
    r'ni\s*43-?101|43-101|technical\s+report|feasibility|preliminary\s+economic|'
    r'resource\s+estimate|mineral\s+reserve|scoping\s+study|'
    # 'mre' included: companies label reports "CLARENCE STREAM - MRE 2026", and
    # this pattern also gates whether a non-.pdf download link counts as a
    # document at all, so omitting it dropped those links entirely.
    r'(?<![a-z0-9])(?:pea|pfs|dfs|mre)(?![a-z0-9])',
    re.IGNORECASE,
)

_NEGATIVE_HINT = re.compile(
    r'presentation|fact\s*sheet|factsheet|corporate\s+deck|financial\s+statement|'
    # Short tokens need boundaries: bare 'aif' matched inside "Waif" and
    # "Kaifeng", and 'mda' inside any word containing it, disqualifying
    # legitimate technical reports from auto-queue.
    r'annual\s+report|(?<![a-z])interim(?![a-z])|md&a|(?<![a-z])mda(?![a-z])|'
    r'(?<![a-z])proxy(?![a-z])|circular|(?<![a-z])aif(?![a-z])|news\s+release|'
    r'press\s+release|subscribe|privacy|(?<![a-z])terms(?![a-z])|'
    # Investor-relations news-release filenames: ABA_NR-2026-11_..., NR_2026_04.
    r'(?<![a-z0-9])nr[\s-]\d{2,4}[\s-]\d+',
    re.IGNORECASE,
)

# Bounded on both sides: an unbounded (19|20)\d{2} pulled '2080' out of the
# filename '72080004-0-estrades-pea.pdf' and scored that document as newer
# than the release announcing it.
_YEAR = re.compile(r'(?<!\d)(19|20)\d{2}(?!\d)')


def normalize_url(url: str) -> str:
    """Strip query/fragment and trailing slash so candidates dedupe cleanly."""
    try:
        p = urlparse(url)
        return urlunparse((p.scheme, p.netloc, p.path, '', '', '')).rstrip('/').lower()
    except Exception:
        return (url or '').rstrip('/').lower()


def extract_candidates(html: str, base_url: str) -> List[Dict]:
    """
    Pull document links out of a page.

    Takes .pdf hrefs plus download-handler links whose text reads like a
    technical document. The existing crawler only accepts hrefs containing
    '.pdf', which silently misses every site that serves documents through a
    download route.
    """
    out = []
    try:
        soup = BeautifulSoup(html or '', 'html.parser')
    except Exception as e:
        logger.warning(f"[HUNT] Could not parse page {base_url}: {e}")
        return out

    for link in soup.find_all('a', href=True):
        href = (link.get('href') or '').strip()
        if not href or href.startswith(('#', 'mailto:', 'tel:', 'javascript:')):
            continue

        text = re.sub(r'\s+', ' ', link.get_text(strip=True) or '')[:300]
        is_pdf = '.pdf' in href.lower()
        is_download = bool(_DOWNLOAD_HREF.search(href)) and bool(_DOC_TEXT_HINT.search(text))
        if not (is_pdf or is_download):
            continue

        try:
            full_url = urljoin(base_url, href)
        except Exception:
            continue
        if not full_url.lower().startswith(('http://', 'https://')):
            continue

        out.append({
            'url': full_url,
            'text': text,
            'source_page': base_url,
            'is_pdf': is_pdf,
        })
    return out


# --------------------------------------------------------------------------
# Scoring
# --------------------------------------------------------------------------

_TYPE_MATCH_PATTERNS = {
    'pea': re.compile(r'preliminary\s+economic|(?<![a-z0-9])pea(?![a-z0-9])', re.I),
    'pfs': re.compile(r'pre[\s-]?feasibility|(?<![a-z0-9])pfs(?![a-z0-9])', re.I),
    # Three lookbehinds, one per separator, so a prefeasibility study does not
    # satisfy a definitive feasibility target. Bare 'feasibility' matched
    # inside 'prefeasibility', which let a PFS document auto-queue against a
    # DFS announcement — and after that was guarded with (?<!pre)(?<!pre-),
    # the separator-collapsed haystack reopened it: _hit() also searches a
    # view where 'Pre-Feasibility-Study.pdf' reads 'pre feasibility study',
    # which neither lookbehind covered. (?<!pre ) closes that channel.
    'dfs': re.compile(r'(?<!pre)(?<!pre-)(?<!pre )feasibility|(?<![a-z0-9])dfs(?![a-z0-9])', re.I),
    'mre': re.compile(r'resource\s+estimate|mineral\s+reserve|(?<![a-z0-9])mre(?![a-z0-9])', re.I),
    'ni43101': re.compile(r'ni\s*43-?101|43-101|technical\s+report', re.I),
}


def score_candidate(candidate: Dict, target: HuntTarget) -> Dict:
    """
    Rank one candidate document against what the flag is looking for.

    Returns the candidate annotated with 'score' and 'score_reasons' so a
    reviewer can see why something ranked where it did rather than being handed
    an opaque number.
    """
    haystack = f"{candidate.get('text', '')} {candidate.get('url', '')}".lower()
    # Separator-normalized view of the same text. URLs join words with hyphens
    # and underscores, so a literal comparison misses what is plainly there:
    # the project 'loki flake' did not match
    # '...for-the-Loki-Flake-Graphite-Deposit.pdf' and that candidate was scored
    # "does not mention project 'loki flake'". Since a project match now gates
    # auto-queueing, the miss silently suppressed correct documents wherever the
    # link text was generic — and "Technical Report (PDF)" is very common link
    # text. Patterns are tried against both views and either may match.
    haystack_norm = re.sub(r'[^a-z0-9]+', ' ', haystack)

    def _hit(pattern) -> bool:
        return bool(pattern.search(haystack) or pattern.search(haystack_norm))

    score = 0
    reasons = []

    # The document must look like a technical report at all.
    if _hit(_DOC_TEXT_HINT):
        score += 20
        reasons.append('reads as a technical document (+20)')

    # Right project. The strongest signal available: a company publishes one
    # technical report per project, so the project name usually disambiguates.
    #
    # 'project_matched' gates auto-queueing, separately from the score. A full
    # match is the only thing that counts: a partial match on the first token,
    # or a flag with no project identified at all, leaves the decision to a
    # human. Roughly a third of huntable flags resolve no project, and for a
    # company with several technical reports there is then nothing to tell them
    # apart — the score alone would happily queue the wrong one.
    project_matched = False
    if target.project and (target.project in haystack
                           or target.project in haystack_norm):
        score += 40
        project_matched = True
        reasons.append(f"project '{target.project}' matches (+40)")
    elif target.project:
        # Partial match on the distinctive first token.
        first = target.project.split()[0]
        if len(first) >= 5 and (first in haystack or first in haystack_norm):
            score += 15
            reasons.append(f"partial project match on '{first}' (+15)")
        else:
            # We know which project this report covers and this document is not
            # it. Without this penalty a different project's report scores on
            # type, size and being linked from the announcement alone: Galway's
            # "ESTRADES - MRE 2024" reached 90 against a Clarence Stream flag,
            # over the auto-queue threshold, which would have put the wrong
            # project's report into the vector store unreviewed.
            score -= 25
            reasons.append(f"does not mention project '{target.project}' (-25)")

    # Right kind of report. Recorded as well as scored, because a type mismatch
    # means this is a different report from the one announced, and that must
    # block auto-queueing rather than merely cost points: a PEA announcement
    # queued last year's mineral resource estimate for the same project on
    # project and size alone.
    type_matched = False
    type_pattern = _TYPE_MATCH_PATTERNS.get(target.report_type)
    if type_pattern and _hit(type_pattern):
        score += 25
        type_matched = True
        reasons.append(f'report type {target.report_type} matches (+25)')
    else:
        reasons.append(f'report type {target.report_type} not confirmed')

    # Right vintage. The report cannot predate the release that announced it,
    # allowing one year of slack for effective-date vs filing-date drift.
    if target.release_date:
        years = [int(m.group(0)) for m in _YEAR.finditer(haystack)]
        if years:
            newest = max(years)
            if newest >= target.release_date.year:
                score += 15
                reasons.append(f'dated {newest}, at or after the release (+15)')
            elif newest < target.release_date.year - 1:
                score -= 25
                reasons.append(f'dated {newest}, predates the release (-25)')

    # Found on the announcement page itself — strong, since a release that links
    # a document is almost always linking the one it is announcing.
    if candidate.get('source_page') and target.news_url:
        if normalize_url(candidate['source_page']) == normalize_url(target.news_url):
            score += 25
            reasons.append('linked from the announcement itself (+25)')

    # Wrong kind of document.
    is_negative = _hit(_NEGATIVE_HINT)
    if is_negative:
        score -= 35
        reasons.append('reads as a presentation/financial/news document (-35)')

    # A real technical report is megabytes; a summary or a placeholder is not.
    size_mb = candidate.get('size_mb')
    if size_mb is not None:
        if size_mb >= 5:
            score += 20
            reasons.append(f'{size_mb:.1f}MB, consistent with a full report (+20)')
        elif size_mb >= 1.5:
            score += 8
            reasons.append(f'{size_mb:.1f}MB (+8)')
        elif size_mb < 0.4:
            score -= 20
            reasons.append(f'{size_mb:.1f}MB, too small for a technical report (-20)')

    if not candidate.get('is_pdf'):
        score -= 5
        reasons.append('not a direct PDF link (-5)')

    candidate = dict(candidate)
    candidate['score'] = score
    candidate['score_reasons'] = reasons
    candidate['project_matched'] = project_matched
    candidate['type_matched'] = type_matched
    candidate['is_negative'] = is_negative
    return candidate


def is_auto_queueable(candidate: Dict) -> bool:
    """
    Whether a candidate may go to the GPU without a human looking at it.

    Four conditions, all required. Score alone was not enough — a document can
    reach the threshold on report type, file size and being linked from the
    announcement while belonging to a different project entirely, and the
    resulting chunks would answer questions in the mining assistant as though
    they described the project the release was about. The report type must
    match too, or a PEA announcement queues that project's older resource
    estimate. And a news release, presentation or financial statement is never
    the report, whatever it scores.
    """
    return (
        candidate.get('score', 0) >= AUTO_QUEUE_THRESHOLD
        and bool(candidate.get('project_matched'))
        and bool(candidate.get('type_matched'))
        # A document that reads as a news release, presentation or financial
        # statement is never the technical report, whatever it scores. This has
        # to disqualify rather than deduct: once separators are normalized, a
        # release's own PDF filename
        # ('ABA_NR-2026-11_ABA-Announces-Positive-Preliminary-Economic-
        # Assessment-for-the-Loki-Flake-Graphite-Deposit.pdf') contains the
        # project and the report type, so it matched both gates and still
        # cleared the threshold at 90 despite the -35.
        and not candidate.get('is_negative')
    )


# Per-host verdict cache for the SSRF gate. is_safe_url resolves DNS by
# default, and rank_candidates gates every raw candidate — one Galway hunt
# produced 149 candidates spread across two hostnames, shared by every flag of
# the company, which meant hundreds of blocking DNS lookups for two answers.
# Scheme+host is the right key: the private-IP and metadata checks depend on
# nothing else, and a poisoned path cannot change the verdict.
_SAFE_HOST_CACHE: Dict[str, bool] = {}
_SAFE_HOST_CACHE_MAX = 512


def is_safe_candidate_url(url: str) -> bool:
    """
    SSRF gate for any URL scraped off a page before we make a request to it.

    These URLs come from third-party HTML, so they are attacker-influenced in
    the ordinary sense: a compromised or hostile investor-relations page can
    link anywhere, including cloud metadata endpoints and internal services.
    Django's checker is imported lazily so this module stays importable outside
    a configured Django process.
    """
    try:
        parsed = urlparse(url or '')
        cache_key = f'{parsed.scheme}://{(parsed.hostname or "").lower()}'
    except Exception:
        return False
    if not parsed.hostname:
        return False

    cached = _SAFE_HOST_CACHE.get(cache_key)
    if cached is not None:
        return cached

    try:
        from core.security_utils import is_safe_url
    except Exception:  # pragma: no cover - only outside Django
        logger.warning('[HUNT] SSRF checker unavailable; refusing %s', url[:80])
        return False
    try:
        ok, _reason = is_safe_url(url)
        verdict = bool(ok)
    except Exception:
        verdict = False

    if len(_SAFE_HOST_CACHE) >= _SAFE_HOST_CACHE_MAX:
        _SAFE_HOST_CACHE.clear()  # crude, but a hunt never nears this many hosts
    _SAFE_HOST_CACHE[cache_key] = verdict
    return verdict


def head_size_mb(url: str, timeout: int = 12) -> Optional[float]:
    """
    Content-Length via HEAD, used to separate full reports from summaries.

    Cheap relative to a browser fetch, but still a network round trip, so the
    caller only runs it on candidates that already scored well.

    The URL is SSRF-checked first and redirects are NOT followed. This is a
    request to an address taken from a scraped page, and it previously ran
    unchecked with allow_redirects=True — so a link (or a redirect from one)
    could point at an internal host and we would dial it. Size only nudges the
    score, so refusing to chase redirects costs a little accuracy and removes
    the whole class of problem.
    """
    if not is_safe_candidate_url(url):
        return None
    try:
        resp = requests.head(url, timeout=timeout, allow_redirects=False,
                             headers={'User-Agent': 'Mozilla/5.0 (compatible; GoldVentureBot/1.0)'})
        # >= 300, not >= 400. With redirects off, a 301/302 response passed a
        # 400-only check and its OWN Content-Length — the redirect stub's few
        # bytes, not the report's — was returned as the document size. A real
        # 20MB report behind a www or https redirect then took the "-20 too
        # small" penalty. A redirect means the size is unknown, so say so.
        if resp.status_code >= 300:
            return None
        length = resp.headers.get('Content-Length')
        if length and length.isdigit():
            return int(length) / (1024 * 1024)
    except Exception:
        return None
    return None


# --------------------------------------------------------------------------
# Crawling
# --------------------------------------------------------------------------

# Where technical reports live on a mining IR site. Ordered by hit rate.
_TECH_PAGE_PATTERNS = [
    '/technical-reports/',
    '/technical-documents/',
    '/ni-43-101/',
    '/43-101/',
    '/reports/',
    '/investors/technical-reports/',
    '/investors/reports/',
    '/investor-relations/technical-reports/',
    '/investor-relations/reports/',
    '/projects/',
]

# crawl4ai defaults page_timeout to 60s, which costs a full minute per dead URL
# pattern. Most of the patterns above miss on any given site, so the default
# turns a speculative sweep into minutes of wall clock for nothing.
_PAGE_TIMEOUT_MS = 25000

# Hard ceiling on pages fetched per company, so one site with a large project
# tree cannot monopolise the scrape queue.
_MAX_PAGES_PER_COMPANY = 14


async def _fetch(crawler, url: str, config) -> Optional[str]:
    """Fetch one page, returning HTML or None. Never raises."""
    try:
        result = await crawler.arun(url=url, config=config)
        if result and getattr(result, 'success', False):
            return result.html
    except Exception as e:
        logger.debug(f"[HUNT] fetch failed {url}: {e}")
    return None


def _discover_tech_pages(home_html: str, base_url: str, project: str) -> List[str]:
    """
    Find on-site pages likely to hold technical documents.

    Pages whose link text or href mentions the flag's project are returned
    first: a company with fifteen project pages should have the relevant one
    crawled before the ceiling is reached.
    """
    prioritized, general = [], []
    try:
        soup = BeautifulSoup(home_html or '', 'html.parser')
    except Exception:
        return []

    host = urlparse(base_url).netloc
    for link in soup.find_all('a', href=True):
        href = (link.get('href') or '').strip()
        text = (link.get_text(strip=True) or '').lower()
        blob = f'{href.lower()} {text}'
        if not any(kw in blob for kw in
                   ('technical', 'report', '43-101', 'project', 'document', 'resource')):
            continue
        try:
            full = urljoin(base_url, href)
        except Exception:
            continue
        if urlparse(full).netloc != host:
            continue
        # Compare with separators collapsed: the project is stored normalized
        # ("loki flake") while hrefs write it "loki-flake", so a literal
        # substring test never prioritized the hyphenated project URL — and
        # prioritization is the whole point, since the page budget can run out
        # before an unprioritized project page is reached.
        if project and project in _collapse(blob):
            prioritized.append(full)
        else:
            general.append(full)

    ordered, seen = [], set()
    for u in prioritized + general:
        key = normalize_url(u)
        if key not in seen:
            seen.add(key)
            ordered.append(u)
    return ordered


async def gather_company_candidates(website: str, targets: List[HuntTarget]) -> Dict[int, List[Dict]]:
    """
    Collect candidate documents for every flag belonging to one company.

    Two stages. First each flag's own announcement page, because a release that
    links a PDF is almost certainly linking the report it announces. Then the
    company's technical and project pages, shared across all of that company's
    flags — which is the whole reason hunts are batched per company rather than
    run per flag.
    """
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

    per_flag: Dict[int, List[Dict]] = {t.flag_id: [] for t in targets}
    if not website:
        return per_flag

    browser_config = BrowserConfig(headless=True, verbose=False)
    crawler_config = CrawlerRunConfig(cache_mode="bypass", page_timeout=_PAGE_TIMEOUT_MS)
    pages_fetched = 0

    async with AsyncWebCrawler(config=browser_config) as crawler:
        # Stage 1 — each announcement page.
        for target in targets:
            if not target.news_url or target.news_url.lower().endswith('.pdf'):
                continue
            if pages_fetched >= _MAX_PAGES_PER_COMPANY:
                break
            html = await _fetch(crawler, target.news_url, crawler_config)
            pages_fetched += 1
            if html:
                found = extract_candidates(html, target.news_url)
                per_flag[target.flag_id].extend(found)
                logger.info(f"[HUNT] {target.company_name}: {len(found)} candidate(s) on the release page")

        # Stage 2 — company technical/project pages, shared by all flags here.
        shared: List[Dict] = []
        project_hint = next((t.project for t in targets if t.project), '')
        home_html = None
        if pages_fetched < _MAX_PAGES_PER_COMPANY:
            home_html = await _fetch(crawler, website, crawler_config)
            pages_fetched += 1

        page_urls: List[str] = []
        if home_html:
            page_urls.extend(_discover_tech_pages(home_html, website, project_hint))
        # Fall back to the conventional paths when the homepage yields nothing.
        page_urls.extend(urljoin(website.rstrip('/') + '/', p.lstrip('/'))
                         for p in _TECH_PAGE_PATTERNS)

        seen_pages = set()
        for page_url in page_urls:
            if pages_fetched >= _MAX_PAGES_PER_COMPANY:
                break
            key = normalize_url(page_url)
            if key in seen_pages:
                continue
            seen_pages.add(key)
            html = await _fetch(crawler, page_url, crawler_config)
            pages_fetched += 1
            if html:
                shared.extend(extract_candidates(html, page_url))

        if shared and targets:
            logger.info(f"[HUNT] {targets[0].company_name}: {len(shared)} candidate(s) "
                        f"across {len(seen_pages)} site page(s)")
        for target in targets:
            per_flag[target.flag_id].extend(shared)

    return per_flag


def rank_candidates(raw: List[Dict], target: HuntTarget, top_n: int = 5) -> List[Dict]:
    """
    Score, deduplicate and rank candidates for one flag.

    Size is only fetched for the leaders: a HEAD per candidate would multiply
    the network cost of a hunt for information that rarely changes the order
    outside the top few.
    """
    deduped, seen = [], set()
    for cand in raw:
        key = normalize_url(cand.get('url', ''))
        if not key or key in seen:
            continue
        # SSRF-gate before a candidate can occupy a slot, be fetched for its
        # size, be shown to a reviewer as a one-click submit, or be queued.
        # The caller checks again before storing; this keeps unsafe URLs out of
        # the ranking altogether rather than relying on that single point.
        if not is_safe_candidate_url(cand.get('url', '')):
            continue
        seen.add(key)
        deduped.append(cand)

    scored = sorted((score_candidate(c, target) for c in deduped),
                    key=lambda c: c['score'], reverse=True)

    # Refine the leaders with a size check, then re-sort.
    for cand in scored[:3]:
        if cand['score'] <= 0:
            continue
        size = head_size_mb(cand['url'])
        if size is not None:
            cand['size_mb'] = round(size, 2)
            refreshed = score_candidate(cand, target)
            cand['score'] = refreshed['score']
            cand['score_reasons'] = refreshed['score_reasons']
    scored.sort(key=lambda c: c['score'], reverse=True)
    return scored[:top_n]
