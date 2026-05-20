import { Metadata } from "next";

const url =
  "https://juniorminingintelligence.com/investor-tools/catalyst-calendar";
const description =
  "Track news release frequency across junior mining companies. Spot quiet companies, find the most active newsmakers, and monitor weekly news volume trends.";

export const metadata: Metadata = {
  title: "News Catalyst Calendar - Junior Mining News Tracker",
  description,
  keywords: [
    "mining news calendar",
    "junior mining catalysts",
    "news release tracker",
    "mining news volume",
    "catalyst calendar mining",
  ],
  openGraph: {
    title:
      "News Catalyst Calendar - Junior Mining News Tracker | Junior Mining Intelligence",
    description,
    type: "website",
    url,
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "News Catalyst Calendar",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "News Catalyst Calendar - Junior Mining News Tracker",
    description,
    images: ["/og-image.png"],
  },
  alternates: {
    canonical: url,
  },
};

export default function CatalystCalendarLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
