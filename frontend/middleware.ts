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

export async function middleware(request: NextRequest) {
  const segment = request.nextUrl.pathname.split("/").pop() ?? "";

  // Already in `{id}-{slug}` shape — nothing to do.
  if (ID_WITH_SLUG.test(segment)) return NextResponse.next();
  // Not a number at all — let the page handler 404 it.
  if (!NUMERIC_ONLY.test(segment)) return NextResponse.next();

  try {
    const res = await fetch(`${API_BASE_URL}/companies/${segment}/`, {
      next: { revalidate: 3600 },
    });
    if (!res.ok) return NextResponse.next();

    const company = await res.json();
    if (!company.slug) return NextResponse.next();

    const canonical = new URL(
      `/companies/${company.id}-${company.slug}`,
      request.nextUrl.origin,
    );
    // Preserve query + hash.
    canonical.search = request.nextUrl.search;
    canonical.hash = request.nextUrl.hash;

    return NextResponse.redirect(canonical, 308);
  } catch {
    return NextResponse.next();
  }
}
