"""
Tier entitlements - the single source of truth for what a plan unlocks.

Server-side enforcement for the paid platform tiers. Free and anonymous callers
get a truncated "teaser" payload rather than a hard 403, mirroring the pattern
already established by the open financings list (core/views/open_financings.py):
enough to see what exists, not enough to use it.
"""

import functools


PAID_TIERS = ('prospector', 'miner')

# Tiers are cumulative: Miner gets everything Prospector gets.
TIER_RANK = {'explorer': 0, 'prospector': 1, 'miner': 2}

# The tool split is the substance of the paid tiers, so it is defined here once
# and read by the model's feature flags, the public tiers endpoint and the
# decorators on the views. Anything not listed is Prospector-and-up.
FREE_TOOLS = ('grade-ranker', 'sector-pulse')
# Only tools introduced *after* the early-access welcome email of 2026-08-04
# may sit behind Miner. That email told recipients Prospector included "All 10
# tools", and property-valuation, portfolio-xray and due-diligence all existed
# at the time, so they are inside that promise. Warrant Radar shipped on
# 2026-08-11 and was never promised.
MINER_TOOLS = (
    'warrant-radar',
)

# Chat messages per day. 0 means unlimited.
# The same email promised 'Unlimited on Prospector', so Prospector is
# unlimited and chat volume cannot be a Miner differentiator.
CHAT_LIMITS = {'explorer': 5, 'prospector': 0, 'miner': 0}


def meets_tier(user, required='prospector') -> bool:
    """True if `user`'s effective tier is at or above `required`."""
    return TIER_RANK.get(resolve_effective_tier(user), 0) >= TIER_RANK.get(required, 1)

# How many rows a free caller sees in full before the teaser cuts in.
FREE_PREVIEW_COUNT = 3

# Trailing points kept for continuous time series. Cutting one to
# FREE_PREVIEW_COUNT leaves a chart too sparse to render as anything but
# broken, so series keep a recent window instead - clearly limited, still legible.
FREE_WINDOW_SIZE = 30

# A redacted row keeps only enough to identify its subject. Every other field
# is nulled out, so the shape stays stable for the frontend.
IDENTITY_FIELDS = frozenset({
    'id', 'slug', 'name', 'title', 'symbol', 'ticker', 'exchange',
    'ticker_symbol', 'company_id', 'company_slug', 'company_name',
    'company_ticker', 'company_exchange',
})


def resolve_effective_tier(user) -> str:
    """Return the tier `user` should be treated as right now.

    'explorer' for anonymous users and for anyone with no subscription row.
    Delegates to PlatformSubscription.effective_tier, which already handles
    superusers, lapsed paid plans and expired comp grants.
    """
    from .models import PlatformSubscription

    if not user or not getattr(user, 'is_authenticated', False):
        return 'explorer'
    try:
        return user.platform_subscription.effective_tier
    except PlatformSubscription.DoesNotExist:
        return 'explorer'


def is_paid(user) -> bool:
    """True if `user` is on a paid tier right now."""
    return resolve_effective_tier(user) in PAID_TIERS


def locked_row(row):
    """Redact one result row down to its identifying fields.

    Returns None for anything that isn't a dict - the caller drops those, since
    there's nothing meaningful left to show.
    """
    if not isinstance(row, dict):
        return None
    stub = {k: (v if k in IDENTITY_FIELDS else None) for k, v in row.items()}
    stub['is_locked'] = True
    return stub


def tier_gated(*, stub=(), truncate=(), window=(), requires='prospector',
               free_count=FREE_PREVIEW_COUNT, window_size=FREE_WINDOW_SIZE):
    """Truncate a tool's response for callers below Prospector.

    ``stub``     keys holding row lists whose rows carry identity fields. The
                 first `free_count` rows survive intact; the rest are redacted
                 to identity only, so the upgrade prompt can still name what's
                 being withheld.
    ``truncate`` keys holding discrete lists that can't be redacted
                 field-by-field. Everything past `free_count` is dropped.
    ``window``   keys holding a continuous time series. The most recent
                 `window_size` points are kept so the chart still renders.

    Gate every key that exposes the same subject. A tool returning parallel
    lists (say `series` and `summary`, one row per company) leaks the withheld
    rows through whichever list you forget.

    Apply this closest to the view function so it wraps *every* exit path,
    including the early ``return Response(cached)`` returns. Non-200 responses
    pass through untouched.

    The response dict is shallow-copied and gated lists are rebuilt rather than
    mutated, so gating a cache hit never writes back into the cached object.
    """
    def decorator(view):
        @functools.wraps(view)
        def wrapper(request, *args, **kwargs):
            response = view(request, *args, **kwargs)

            if meets_tier(getattr(request, 'user', None), requires):
                return response
            if getattr(response, 'status_code', 200) != 200:
                return response

            data = getattr(response, 'data', None)
            if not isinstance(data, dict):
                return response

            gated = dict(data)
            locked_total = 0

            for key in stub:
                rows = gated.get(key)
                if not isinstance(rows, list):
                    continue
                locked_total += max(0, len(rows) - free_count)
                kept = []
                for i, row in enumerate(rows):
                    if i < free_count:
                        kept.append(row)
                        continue
                    redacted = locked_row(row)
                    if redacted is not None:
                        kept.append(redacted)
                gated[key] = kept

            for key in truncate:
                rows = gated.get(key)
                if not isinstance(rows, list):
                    continue
                locked_total += max(0, len(rows) - free_count)
                gated[key] = rows[:free_count]

            for key in window:
                rows = gated.get(key)
                if not isinstance(rows, list):
                    continue
                # Deliberately not added to locked_total: these are datapoints
                # trimmed off a chart, not withheld results, and counting them
                # would have the banner claim "341 more results" for what is
                # really one company's price history.
                gated[key] = rows[-window_size:]

            gated['is_locked'] = True
            gated['required_tier'] = requires
            gated['preview_count'] = free_count
            gated['locked_count'] = locked_total

            response.data = gated
            return response

        return wrapper
    return decorator


def requires_tier(required='prospector'):
    """Hard-block a view for callers below `required`.

    Companion to ``tier_gated``, for *actions* rather than reads. Truncating a
    GET into a teaser is the house pattern and the better one, but there is no
    partial version of registering interest in a financing — the write either
    happens or it does not — so the honest answer is a 403 that names what is
    missing, rather than a half-completed action or a silently dropped one.

    Prefer ``tier_gated`` for anything that returns data. Reach for this only
    where a teaser is meaningless.

    Returns the structured payload the frontend already understands from the
    tool teasers, so an upgrade prompt can be rendered without special-casing.
    """
    def decorator(view):
        @functools.wraps(view)
        def wrapper(request, *args, **kwargs):
            user = getattr(request, 'user', None)
            if meets_tier(user, required):
                return view(request, *args, **kwargs)

            from rest_framework.response import Response
            from rest_framework import status

            current = resolve_effective_tier(user)
            return Response(
                {
                    'error': 'upgrade_required',
                    'detail': (
                        'This action is available on the Prospector plan and above.'
                        if required == 'prospector'
                        else f'This action requires the {required.title()} plan.'
                    ),
                    'required_tier': required,
                    'current_tier': current,
                    'is_locked': True,
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        return wrapper
    return decorator
