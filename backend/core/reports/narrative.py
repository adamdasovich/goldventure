"""
Claude narrative generation for the weekly industry report.

Single API call produces the executive summary plus a one-sentence
"why it moved" gloss for each of the top developments, grounded in the
release/report/financing already attached to each candidate by scoring.py.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import anthropic
from django.conf import settings


logger = logging.getLogger(__name__)

NARRATIVE_MODEL = 'claude-sonnet-4-6'

SYSTEM_PROMPT = (
    "You are a mining-industry analyst writing the executive section of a "
    "weekly market report for institutional investors and mining "
    "professionals. Output must be factual, sourced from the provided data, "
    "and free of speculation, marketing language, or generic commentary. "
    "Do not invent numbers. If a data point isn't provided, omit the claim."
)


def _digest_for_prompt(data: dict[str, Any]) -> dict[str, Any]:
    """
    Trim the full data_snapshot to just what narrative needs. Keeps the
    prompt small and deterministic.
    """
    return {
        'week_ending': data.get('week_ending'),
        'metals': [
            {
                'label': m['label'],
                'end_price': m['end_price'],
                'unit': m['unit'],
                'wow_change_pct': m['wow_change_pct'],
                'trend_4w': m['trend_4w'],
            }
            for m in data.get('metals', [])
        ],
        'financings_summary': {
            'count': data.get('financings', {}).get('count', 0),
            'total_amount_usd': data.get('financings', {}).get('total_amount_usd', 0),
            'by_commodity': data.get('financings', {}).get('by_commodity', []),
        },
        'technical_reports_count': len(data.get('technical_reports', [])),
        'material_releases_count': len(data.get('material_releases', [])),
        'emerging_themes': [
            {'token': t['token'], 'count_this_week': t['count_this_week'],
             'is_new': t['is_new']}
            for t in data.get('emerging_themes', [])[:5]
        ],
        'top_developments': [
            {
                'rank': i + 1,
                'company_name': d.get('company_name'),
                'ticker': d.get('ticker'),
                'weekly_return_pct': d.get('weekly_return_pct'),
                'primary_commodity': d.get('primary_commodity'),
                'sector_zscore': d.get('sector_zscore'),
                'catalyst': d.get('catalyst'),
            }
            for i, d in enumerate(data.get('top_developments', []))
        ],
    }


USER_PROMPT_TEMPLATE = """Below is the structured data for this week's mining industry report.

Generate a JSON response with EXACTLY this shape:
{{
  "executive_summary": "<2-3 sentence overview covering the dominant metal move, broad junior performance, and most notable catalyst class. Reference specific numbers from the data only.>",
  "development_glosses": [
    {{"rank": 1, "gloss": "<one sentence explaining why this company moved, citing its catalyst>"}},
    ...
  ],
  "theme_note": "<one optional sentence on the strongest emerging theme, or null if none stand out>"
}}

Rules:
- Use exact ticker symbols and numeric values from the data; do not round to different precision.
- If a top development has no catalyst, the gloss should say so plainly ("no material release in window — move appears technical").
- The executive_summary must NOT use generic phrases like "the mining sector saw mixed action".
- Reply with JSON only, no markdown fences, no prose before or after.

DATA:
{data_json}
"""


def _empty_narrative(reason: str) -> dict[str, Any]:
    return {
        'executive_summary': f'(narrative generation skipped: {reason})',
        'development_glosses': [],
        'theme_note': None,
    }


def generate_narrative(data: dict[str, Any]) -> dict[str, Any]:
    """
    Call Claude to produce executive summary + per-development glosses.
    Returns a dict with keys: executive_summary, development_glosses, theme_note.

    Failure-tolerant: any error returns a stub so the report still renders.
    """
    api_key = getattr(settings, 'ANTHROPIC_API_KEY', '') or ''
    if not api_key:
        logger.warning("ANTHROPIC_API_KEY missing — skipping narrative generation")
        return _empty_narrative('ANTHROPIC_API_KEY missing')

    digest = _digest_for_prompt(data)
    if not digest['top_developments']:
        return _empty_narrative('no top developments to narrate')

    prompt = USER_PROMPT_TEMPLATE.format(data_json=json.dumps(digest, indent=2))

    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=NARRATIVE_MODEL,
            max_tokens=1500,
            system=SYSTEM_PROMPT,
            messages=[{'role': 'user', 'content': prompt}],
        )
        text = ''.join(
            block.text for block in response.content
            if getattr(block, 'type', None) == 'text'
        ).strip()

        # Strip accidental fences just in case the model adds them
        if text.startswith('```'):
            text = text.split('\n', 1)[1].rsplit('```', 1)[0].strip()
            if text.startswith('json'):
                text = text[4:].lstrip()

        parsed = json.loads(text)
        # Coerce expected shape
        return {
            'executive_summary': str(parsed.get('executive_summary', '')).strip(),
            'development_glosses': [
                {'rank': int(g.get('rank', 0)), 'gloss': str(g.get('gloss', '')).strip()}
                for g in parsed.get('development_glosses', []) or []
            ],
            'theme_note': (parsed.get('theme_note') or None),
        }

    except json.JSONDecodeError as e:
        logger.error("Narrative JSON parse failed: %s; raw=%r", e, text[:500])
        return _empty_narrative('LLM returned non-JSON')
    except Exception as e:
        logger.exception("Narrative generation failed")
        return _empty_narrative(f'API error: {type(e).__name__}')


def attach_narrative(data: dict[str, Any]) -> dict[str, Any]:
    """Returns a new dict with `narrative` populated."""
    return {**data, 'narrative': generate_narrative(data)}
