"""
Reject query parameters an endpoint does not understand.

The bug this exists for: /api/financings/?status=open silently dropped the
filter and returned all 297 rows. Nothing errored, so "297 open financings"
went into page copy, a pricing rationale and Google Ads assets. There were 21.
A filter that quietly does nothing is worse than one that fails, because the
caller believes the answer.

Two modes, because enforcing everywhere at once risks 400ing a working page:

    strict=True   unknown parameter -> 400 naming it. Use once the endpoint's
                  real parameter set has been verified against its callers.
    strict=False  unknown parameter -> logged, request proceeds. Use to learn
                  what callers actually send before enforcing.

Work out the allow-list from ALL of these, not just the first:
  * query_params.get(...) in the view — note get('x', 'default') too
  * filterset_fields / search_fields / ordering_fields on the ViewSet, which
    DjangoFilterBackend and friends consume declaratively. /glossary/ honours
    ?category= entirely through filterset_fields and reads it nowhere.
  * DRF infrastructure: page, page_size, search, ordering, format.
"""

import logging

from rest_framework import status
from rest_framework.response import Response

logger = logging.getLogger(__name__)

# Pagination, search, ordering and the format suffix are handled by DRF itself
# and are valid on any list endpoint.
DRF_PARAMS = frozenset({"page", "page_size", "search", "ordering", "format"})


def unknown_params(request, allowed):
    """Parameters present on the request that nothing will act on."""
    return sorted(set(request.query_params) - set(allowed) - DRF_PARAMS)


def rejection_response(unknown, allowed):
    return Response(
        {
            "error": "unknown_query_parameter",
            "detail": (
                "Unrecognised query parameter(s): "
                + ", ".join(unknown)
                + ". This endpoint would otherwise ignore them and return an "
                "unfiltered result, which reads as a filtered one."
            ),
            "unknown": unknown,
            "supported": sorted(set(allowed) | DRF_PARAMS),
        },
        status=status.HTTP_400_BAD_REQUEST,
    )


def guard_query_params(*allowed, strict=True):
    """Decorate a list view so unknown parameters cannot pass silently.

    Apply closest to the view so it wraps every exit path.
    """
    allowed = frozenset(allowed)

    def decorator(view):
        from functools import wraps

        @wraps(view)
        def wrapper(request, *args, **kwargs):
            unknown = unknown_params(request, allowed)
            if unknown:
                if strict:
                    return rejection_response(unknown, allowed)
                # Not an error the caller sees — a breadcrumb for us, so the
                # allow-list can be widened before this is switched to strict.
                logger.warning(
                    "Ignored query parameter(s) on %s: %s (allowed: %s)",
                    request.path, ", ".join(unknown), ", ".join(sorted(allowed)),
                )
            return view(request, *args, **kwargs)

        return wrapper

    return decorator


class GuardedListParamsMixin:
    """ViewSet counterpart to guard_query_params.

    Most list endpoints here are ViewSets, where a decorator on a function is
    not available. Mix this in ahead of the ViewSet base and declare:

        class ThingViewSet(GuardedListParamsMixin, viewsets.ModelViewSet):
            ALLOWED_LIST_PARAMS = frozenset({'commodity', 'ticker'})
            STRICT_LIST_PARAMS = False   # log first, enforce once verified

    Only `list` is guarded. Detail routes take their argument from the URL, so
    a stray query parameter there cannot be mistaken for a filter that worked.

    Work the allow-list out from the view code AND from filterset_fields /
    search_fields / ordering_fields, which the DRF filter backends consume
    without the view ever calling query_params.get. Missing those is how a
    working parameter gets mistaken for a silently-ignored one.
    """

    ALLOWED_LIST_PARAMS: frozenset = frozenset()
    # Default False on purpose: a wrong allow-list 400s a page that works, and
    # the logs tell you what callers really send before you commit to enforcing.
    STRICT_LIST_PARAMS: bool = False

    def list(self, request, *args, **kwargs):
        allowed = set(self.ALLOWED_LIST_PARAMS)
        # Anything the filter backends are configured to honour is legitimate.
        for attr in ("filterset_fields", "search_fields", "ordering_fields"):
            allowed.update(getattr(self, attr, None) or [])

        unknown = unknown_params(request, allowed)
        if unknown:
            if self.STRICT_LIST_PARAMS:
                return rejection_response(unknown, allowed)
            logger.warning(
                "Ignored query parameter(s) on %s: %s (allowed: %s)",
                request.path, ", ".join(unknown), ", ".join(sorted(allowed)),
            )
        return super().list(request, *args, **kwargs)
