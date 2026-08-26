import { Metadata } from "next";

const url = "https://juniorminingintelligence.com/investor-tools/grade-ranker";
const description =
  "Rank 390+ junior mining companies by resource grade and size. Filter by commodity, stage, and minimum resource to find the highest-grade gold, silver, and copper deposits.";

export const metadata: Metadata = {
  title: "Resource Grade Ranker - Screen Junior Miners by Grade",
  description,
  keywords: [
    "resource grade ranker",
    "mining grade screener",
    "highest grade gold deposits",
    "junior mining screener",
    "resource size comparison",
  ],
  openGraph: {
    title:
      "Resource Grade Ranker - Screen Junior Miners by Grade | Junior Mining Intelligence",
    description,
    type: "website",
    url,
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "Resource Grade Ranker",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Resource Grade Ranker - Screen Junior Miners by Grade",
    description,
    images: ["/og-image.png"],
  },
  alternates: {
    canonical: url,
  },
};

export default function GradeRankerLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
