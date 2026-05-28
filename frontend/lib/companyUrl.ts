/**
 * Build canonical `/companies/{id}-{slug}` href.
 *
 * The route segment is `{numericId}-{slug}`; the page extracts the leading
 * integer for API lookups, so legacy `/companies/{id}` URLs still resolve
 * and the page issues a 301 to the canonical slug form.
 */
export function companyHref(
  company:
    | { id: number | string; slug?: string | null; name?: string | null }
    | null
    | undefined,
): string {
  if (!company) return "/companies";
  const slug = (company.slug || "").trim();
  if (slug) return `/companies/${company.id}-${slug}`;
  return `/companies/${company.id}`;
}

/** Extract the numeric company id from a `[id]` route segment. */
export function parseCompanyIdParam(segment: string): number | null {
  const match = /^(\d+)/.exec(segment);
  if (!match) return null;
  const n = parseInt(match[1], 10);
  return Number.isFinite(n) ? n : null;
}
