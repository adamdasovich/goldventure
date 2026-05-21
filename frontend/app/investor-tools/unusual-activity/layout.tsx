import { Metadata } from "next";

const url =
  "https://juniorminingintelligence.com/investor-tools/unusual-activity";
const description =
  "Detect unusual trading-volume spikes in junior mining stocks and cross-reference news to tell explained moves from unexplained accumulation.";

export const metadata: Metadata = {
  title: "Unusual Activity Detector - Junior Mining Intelligence",
  description,
  keywords: [
    "unusual trading volume",
    "mining stock volume spike",
    "abnormal trading activity",
    "accumulation detection",
    "junior mining volume scanner",
  ],
  openGraph: {
    title: "Unusual Activity Detector - Junior Mining Intelligence",
    description,
    type: "website",
    url,
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "Unusual Activity Detector",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Unusual Activity Detector - Junior Mining Intelligence",
    description,
    images: ["/og-image.png"],
  },
  alternates: {
    canonical: url,
  },
};

export default function UnusualActivityLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
