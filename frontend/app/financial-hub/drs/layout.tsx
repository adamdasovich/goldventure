import type { Metadata } from "next";

/**
 * Metadata for Your DRS Statements.
 *
 * This page shows the signed-in user's own DRS statements and share records. It is an account page, not a content page — the
 * same category as /dashboard and /account/orders, which are permanently
 * noindex, nofollow. It renders nothing to a crawler because there is nothing
 * a crawler should see, and that will not change when the Financial Hub gains
 * content elsewhere.
 *
 * Do not remove the robots block. If this page ever needs a public,
 * indexable explanation of what it does, that belongs on /financial-hub or in
 * a guide, not here.
 *
 * The canonical is its own URL rather than the parent's. Every route under
 * /financial-hub used to inherit `canonical: /financial-hub` from the parent
 * layout, which declared five distinct pages duplicates of one another.
 */
export const metadata: Metadata = {
  title: "Your DRS Statements — Financial Hub",
  description:
    "Direct Registration System statements and share ownership records for placements you have participated in.",
  alternates: {
    canonical: "https://juniorminingintelligence.com/financial-hub/drs",
  },
  robots: { index: false, follow: false },
};

export default function DrsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
