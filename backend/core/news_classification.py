"""
News-release classification.

Maps a press-release title to a NI 43-101 ``RELEASE_TYPES`` code so the
catalyst-impact analytics, the daily-briefing tool and other features can
group company news by what kind of event it is.

Pure-Python (no Django imports) so it is safe to import from Celery tasks,
the GPU worker, and management commands alike.

Background: the scrapers never set a real release type — every NewsRelease
was stored with the literal string ``'news_release'`` (not even a valid
choice), collapsing every catalyst study into a single bucket.
"""

# The valid NewsRelease.RELEASE_TYPES codes. Kept in sync with the model.
VALID_RELEASE_TYPES = frozenset({
    'drill_results', 'financing', 'resource_update', 'study_results',
    'corporate', 'acquisition', 'management', 'other',
})

# Ordered most-specific-first; the first bucket with a keyword hit wins.
# Keywords are matched as case-insensitive substrings of the title.
_CLASSIFICATION_RULES = [
    ('drill_results', [
        'drill result', 'drilling result', 'drill hole', 'drill program',
        'drilling program', 'drilling update', 'assay result', 'assays',
        'assay', 'intercept', 'intersects', 'intersection', 'metres of',
        'meters of', 'g/t gold', 'g/t au', 'high-grade', 'high grade',
        'channel sample', 'step-out', 'step out', 'drilling commences',
        'drill results', 'exploration results', 'exploration update',
        'commences drilling', 'commences exploration', 'expands drill',
        'extends mineralization', 'trenching', 'soil sampling',
        'geophysical', 'ip survey', 'discovers', 'discovery',
    ]),
    ('resource_update', [
        'resource estimate', 'mineral resource', 'resource update',
        'updated resource', 'maiden resource', 'resource expansion',
        'increases resource', 'expands resource', 'reserve estimate',
        'mineral reserve',
    ]),
    ('study_results', [
        'preliminary economic assessment', 'feasibility study',
        'pre-feasibility', 'prefeasibility', 'economic assessment',
        'scoping study', 'metallurgical result', 'metallurgical test',
        'mine plan', 'positive pea', '(pea)', ' pea ', ' pfs ',
    ]),
    ('financing', [
        'private placement', 'bought deal', 'bought-deal', 'flow-through',
        'flow through', 'financing', 'closes offering', 'public offering',
        'unit offering', 'brokered offering', 'non-brokered', 'prospectus',
        'closes c$', 'closes $', 'closing of', 'overallotment',
        'over-allotment', 'subscription receipt', 'raises c$', 'raises $',
        'debenture', 'credit facility',
    ]),
    ('acquisition', [
        'acquisition', 'acquires', 'to acquire', 'option agreement',
        'earn-in', 'earn in', 'joint venture', 'definitive agreement',
        'arrangement agreement', 'merger', 'merges', 'divest',
        'completes sale', 'sells', 'letter of intent', 'option to acquire',
        'consolidates ownership',
    ]),
    ('management', [
        'appoint', 'appointment', 'resign', 'resignation', 'steps down',
        'new ceo', 'new cfo', 'new president', 'board of directors',
        'to the board', 'management change', 'strengthens board',
        'advisory board', 'names ', 'hires',
    ]),
    ('corporate', [
        'annual general meeting', ' agm', 'corporate update',
        'shares for debt', 'stock option', 'grant of options',
        'option grant', 'commences trading', 'begins trading',
        'name change', 'share consolidation', 'voting results',
        'financial results', 'annual report', 'year-end results',
        'quarterly results', 'corporate presentation', 'listing',
        'to present at', 'present at', 'conference', 'webinar',
        'investor', 'provides update', 'provides an update',
        'operational update', 'operations update', 'business update',
        'project update', 'company update', 'awarded', 'receives permit',
        'permitting', 'environmental',
    ]),
]


def classify_release_type(title: str) -> str:
    """
    Classify a press-release title into a NewsRelease release-type code.

    Returns one of the ``VALID_RELEASE_TYPES`` codes; falls back to ``'other'``
    when no keyword matches. This is a heuristic — it is far better than the
    previous "everything is the same type" behaviour, but is not perfect.
    """
    if not title:
        return 'other'
    text = title.lower()
    for release_type, keywords in _CLASSIFICATION_RULES:
        if any(keyword in text for keyword in keywords):
            return release_type
    return 'other'
