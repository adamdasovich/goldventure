import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const API_BASE_URL =
  process.env.API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000/api";

// Tight matcher: only fires for /companies/{path-segment} (one segment, not
// sub-routes like /companies/123/financing). Sub-routes keep working via
// numeric ids the page handler strips itself.
export const config = {
  matcher: ["/companies/:id"],
};

const NUMERIC_ONLY = /^\d+$/;
const ID_WITH_SLUG = /^(\d+)-(.+)$/;

/**
 * id -> canonical slug, cached in module scope.
 *
 * The route sets `dynamicParams = false`, so an id outside
 * generateStaticParams 404s at the router -- which is what finally gave
 * /companies/<unknown> a real 404 instead of an ISR shell served with 200.
 * The cost is that a *stale* slug for a real company would 404 too, and
 * renaming a company changes its slug: eighteen of them moved on 2026-08-25,
 * with the old URLs already indexed by Google.
 *
 * So this resolves the canonical slug and redirects rather than letting those
 * die. The cache keeps it off the API on the hot path -- without it every
 * company page view would add a lookup, and fetch-level caching is not
 * dependable in middleware.
 */
const SLUG_TTL_MS = 60 * 60 * 1000;
const slugCache = new Map<string, { slug: string | null; at: number }>();

type Lookup =
  | { status: "found"; slug: string | null }
  | { status: "missing" }
  | { status: "unavailable" };

async function lookupCanonicalSlug(id: string): Promise<Lookup> {
  const hit = slugCache.get(id);
  if (hit && Date.now() - hit.at < SLUG_TTL_MS) {
    return { status: "found", slug: hit.slug };
  }

  try {
    const res = await fetch(`${API_BASE_URL}/companies/${id}/`, {
      next: { revalidate: 3600 },
    });
    if (res.status === 404) return { status: "missing" };
    if (!res.ok) return { status: "unavailable" };

    const company = await res.json();
    const slug =
      typeof company.slug === "string" && company.slug ? company.slug : null;
    slugCache.set(id, { slug, at: Date.now() });
    return { status: "found", slug };
  } catch {
    return { status: "unavailable" };
  }
}

function canonicalRedirect(request: NextRequest, id: string, slug: string) {
  const canonical = new URL(`/companies/${id}-${slug}`, request.nextUrl.origin);
  // Preserve query + hash.
  canonical.search = request.nextUrl.search;
  canonical.hash = request.nextUrl.hash;
  return NextResponse.redirect(canonical, 308);
}

export async function middleware(request: NextRequest) {
  const segment = request.nextUrl.pathname.split("/").pop() ?? "";

  const withSlug = ID_WITH_SLUG.exec(segment);
  if (withSlug) {
    const [, id, slug] = withSlug;
    const result = await lookupCanonicalSlug(id);

    // A lookup failure must not turn a good page into a redirect loop or a
    // 404 -- serve it and let the route decide.
    if (result.status !== "found") return NextResponse.next();
    // No slug on record: nothing better to point at.
    if (!result.slug) return NextResponse.next();
    // Stale or wrong slug for a real company -- send it to the canonical URL
    // rather than letting dynamicParams = false 404 it.
    if (result.slug !== slug)
      return canonicalRedirect(request, id, result.slug);

    return NextResponse.next();
  }

  // Not a number at all — let the page handler 404 it.
  if (!NUMERIC_ONLY.test(segment)) return NextResponse.next();

  const result = await lookupCanonicalSlug(segment);
  if (result.status !== "found" || !result.slug) return NextResponse.next();
  return canonicalRedirect(request, segment, result.slug);
}
