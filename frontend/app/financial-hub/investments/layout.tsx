import type { Metadata } from "next";

/**
 * Metadata for Your Mining Investments.
 *
 * This page shows the financings the signed-in user has registered interest in. It is an account page, not a content page — the
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
  title: "Your Mining Investments — Financial Hub",
  description:
    "Track the financings you have registered interest in, your allocations, and the documents attached to each round.",
  alternates: {
    canonical: "https://juniorminingintelligence.com/financial-hub/investments",
  },
  robots: { index: false, follow: false },
};

export default function InvestmentsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
