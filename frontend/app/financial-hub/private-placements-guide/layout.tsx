import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Private Placements Guide - How Mining Companies Raise Capital",
  description:
    "Comprehensive guide to private placements in junior mining. Learn how mining companies raise capital, investor eligibility, pricing mechanics, hold periods, and regulatory requirements in Canada.",
  keywords: [
    "private placement guide",
    "mining private placement",
    "how to invest in private placements",
    "accredited investor mining",
    "TSXV private placement",
    "flow-through shares",
    "hold period",
    "prospectus exemptions",
  ],
  openGraph: {
    title: "Private Placements Guide - Junior Mining Capital Raises",
    description:
      "Learn how private placements work in junior mining, from investor eligibility to regulatory requirements.",
    type: "article",
    url: "https://juniorminingintelligence.com/financial-hub/private-placements-guide",
  },
  alternates: {
    canonical:
      "https://juniorminingintelligence.com/financial-hub/private-placements-guide",
  },
};

export default function PrivatePlacementsGuideLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
