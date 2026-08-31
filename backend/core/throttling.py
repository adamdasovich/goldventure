"""Rate limiting that can tell our own server apart from the internet.

Two problems this fixes, both found on 2026-08-31 when a frontend build started
failing with 429s from our own API.

**The throttle key was the caller's to choose.** With NUM_PROXIES unset, DRF's
``get_ident()`` falls through to ``''.join(xff.split())`` — the *entire*
X-Forwarded-For header — and only uses REMOTE_ADDR when there is no such header.
nginx appends to X-Forwarded-For rather than replacing it, so a client sending
``X-Forwarded-For: <anything>`` gets a key of ``<anything>,<their real ip>``.
Vary the first part per request and every request lands in a fresh bucket: the
anonymous rate limit could be walked past by anyone who knew to set one header.

``NUM_PROXIES = 1`` in settings pins the key to ``addrs[-1]`` — the entry nginx
itself appended, which is the real peer address and cannot be forged from
outside.

**Our own server counted against it.** Next.js renders on this box and calls
gunicorn directly on localhost, as does a production build — 621 pages of it.
That traffic is not a visitor and throttling it achieves nothing except failing
deploys, which is exactly what happened: a build's glossary fetch got a 429, the
category came back empty, and the build died on an unrelated consistency guard.
"""

import logging

from rest_framework.throttling import AnonRateThrottle

logger = logging.getLogger(__name__)

LOOPBACK_ADDRESSES = frozenset({'127.0.0.1', '::1'})


def is_internal_request(request) -> bool:
    """True when this came from a process on this machine, not from a visitor.

    Two conditions, and both are needed:

    * REMOTE_ADDR is loopback. Gunicorn binds 127.0.0.1 and [::1] only — see
      ExecStart in gunicorn.service — so nothing off-box can reach it directly.
    * No X-Forwarded-For. nginx sets that header on every /api/ location, so a
      request that came through nginx always has one. Its absence means nothing
      proxied this.

    Testing loopback alone would exempt the entire internet, since nginx also
    proxies from 127.0.0.1.
    """
    if request.META.get('HTTP_X_FORWARDED_FOR'):
        return False
    return request.META.get('REMOTE_ADDR') in LOOPBACK_ADDRESSES


class InternalAwareAnonRateThrottle(AnonRateThrottle):
    """AnonRateThrottle that does not count our own server-side rendering."""

    def allow_request(self, request, view):
        if is_internal_request(request):
            return True
        return super().allow_request(request, view)
