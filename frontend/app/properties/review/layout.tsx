import { Metadata } from "next";

/**
 * Keeps this page out of the index -- moderation queue, renders a login wall.
 *
 * Not a page anyone should reach from a search result, and the four
 * /properties/* views in particular all render the same ~516-word login wall,
 * so they read as near-duplicates of each other. /dashboard, /account and
 * /store/checkout already do this; these were simply missed.
 *
 * `follow` stays true: every one of these carries the full site navigation,
 * and there is no reason to cut off link discovery just because the page
 * itself should not rank.
 */
export const metadata: Metadata = {
  title: "Listing Review",
  robots: {
    index: false,
    follow: true,
  },
};

export default function ListingReviewLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
