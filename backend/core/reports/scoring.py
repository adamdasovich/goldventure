"""
Composite scoring for the weekly industry report.

Selects "top developments" by combining stock-move magnitude, volume spike,
material-event weight, and market-cap floor — then links each top mover to
the highest-weight material press release in the window.

Inputs come from `collect_weekly_data()` (frozen dict). Output is added back
into the same dict under `top_developments`.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any


# Weight per NewsRelease.release_type when correlating moves to catalysts.
RELEASE_TYPE_WEIGHTS: dict[str, float] = {
    'study_results': 1.00,      # PEA/PFS/DFS results — highest impact
    'resource_update': 0.90,    # new MRE
    'drill_results': 0.85,
    'acquisition': 0.75,
    'financing': 0.70,
    'corporate': 0.30,
    'management': 0.25,
    'other': 0.20,
}

TECHNICAL_REPORT_WEIGHT = 1.00  # Document of type ni43101 in window
FINANCING_CLOSED_WEIGHT = 0.80  # Financing record in window (independent of release)

TOP_N_DEVELOPMENTS = 5

# Composite weights
W_RETURN = 0.40
W_VOLUME = 0.25
W_EVENT = 0.20
W_MCAP = 0.15


def _minmax(values: list[float]) -> list[float]:
    """Min-max scale to [0, 1]. Returns all-zeros if no variance."""
    if not values:
        return []
    lo, hi = min(values), max(values)
    if hi == lo:
        return [0.0 for _ in values]
    return [(v - lo) / (hi - lo) for v in values]


def _index_by_company(items: list[dict[str, Any]]) -> dict[int, list[dict[str, Any]]]:
    out: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for it in items:
        cid = it.get('company_id')
        if cid is not None:
            out[cid].append(it)
    return out


def _best_event_for_company(
    company_id: int,
    releases_by_company: dict[int, list[dict[str, Any]]],
    reports_by_company: dict[int, list[dict[str, Any]]],
    financings_by_company: dict[int, list[dict[str, Any]]],
) -> tuple[float, dict[str, Any] | None]:
    """
    Returns (event_weight, event_dict) — picks the highest-weight catalyst
    associated with the company in the window, or (0.0, None).
    """
    best_weight = 0.0
    best_event: dict[str, Any] | None = None

    for release in releases_by_company.get(company_id, []):
        w = RELEASE_TYPE_WEIGHTS.get(release.get('release_type'), 0.20)
        if w > best_weight:
            best_weight = w
            best_event = {
                'kind': 'release',
                'title': release.get('title'),
                'release_type': release.get('release_type'),
                'date': release.get('release_date'),
                'url': release.get('url'),
                'summary': release.get('summary', ''),
            }

    if TECHNICAL_REPORT_WEIGHT > best_weight and reports_by_company.get(company_id):
        # Most recent in window
        doc = max(
            reports_by_company[company_id],
            key=lambda d: d.get('document_date', ''),
        )
        best_weight = TECHNICAL_REPORT_WEIGHT
        best_event = {
            'kind': 'technical_report',
            'title': doc.get('title'),
            'document_type': doc.get('document_type'),
            'date': doc.get('document_date'),
            'url': doc.get('file_url'),
            'economics': doc.get('economics'),
            'project_name': doc.get('project_name'),
        }

    if FINANCING_CLOSED_WEIGHT > best_weight and financings_by_company.get(company_id):
        fin = max(
            financings_by_company[company_id],
            key=lambda f: f.get('amount_raised_usd', 0) or 0,
        )
        best_weight = FINANCING_CLOSED_WEIGHT
        best_event = {
            'kind': 'financing',
            'title': f"{fin.get('financing_type', '').replace('_', ' ').title()}: "
                     f"${(fin.get('amount_raised_usd') or 0)/1e6:.1f}M",
            'financing_type': fin.get('financing_type'),
            'amount_raised_usd': fin.get('amount_raised_usd'),
            'date': fin.get('announced_date'),
            'url': fin.get('press_release_url'),
            'lead_agent': fin.get('lead_agent'),
        }

    return best_weight, best_event


def rank_top_developments(
    data: dict[str, Any],
    top_n: int = TOP_N_DEVELOPMENTS,
) -> list[dict[str, Any]]:
    """
    Build the ranked list of top developments from a `collect_weekly_data`
    result. Pure function — does not mutate input.

    Movers without an event still compete on price/volume/mcap. Companies
    with strong material events but small moves are surfaced through the
    event component.
    """
    movers: list[dict[str, Any]] = list(data.get('stock_movers', []))
    if not movers:
        return []

    releases_by_company = _index_by_company(data.get('material_releases', []))
    reports_by_company = _index_by_company(data.get('technical_reports', []))
    financings_by_company = _index_by_company(
        data.get('financings', {}).get('items', [])
    )

    # Component values per candidate
    abs_returns = [abs(m.get('weekly_return_pct') or 0) for m in movers]
    volumes = [m.get('avg_weekly_dollar_volume_cad') or 0 for m in movers]
    mcaps = [m.get('market_cap_usd') or 0 for m in movers]

    event_weights: list[float] = []
    events: list[dict[str, Any] | None] = []
    for m in movers:
        w, ev = _best_event_for_company(
            m['company_id'], releases_by_company,
            reports_by_company, financings_by_company,
        )
        event_weights.append(w)
        events.append(ev)

    norm_ret = _minmax(abs_returns)
    norm_vol = _minmax(volumes)
    norm_event = event_weights  # already in [0, 1]
    norm_mcap = _minmax(mcaps)

    scored = []
    for i, mover in enumerate(movers):
        score = (
            W_RETURN * norm_ret[i]
            + W_VOLUME * norm_vol[i]
            + W_EVENT * norm_event[i]
            + W_MCAP * norm_mcap[i]
        )
        scored.append({
            **mover,
            'composite_score': round(score, 4),
            'event_weight': round(event_weights[i], 2),
            'catalyst': events[i],
            'component_scores': {
                'return': round(norm_ret[i], 3),
                'volume': round(norm_vol[i], 3),
                'event': round(norm_event[i], 3),
                'market_cap': round(norm_mcap[i], 3),
            },
        })

    scored.sort(key=lambda r: r['composite_score'], reverse=True)
    return scored[:top_n]


def annotate(data: dict[str, Any]) -> dict[str, Any]:
    """
    Returns a new dict with `top_developments` populated. Used by the
    Celery task between `collect_weekly_data()` and narrative generation.
    """
    return {**data, 'top_developments': rank_top_developments(data)}
