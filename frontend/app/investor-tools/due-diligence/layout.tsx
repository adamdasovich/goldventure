import { Metadata } from "next";

const url = "https://juniorminingintelligence.com/investor-tools/due-diligence";
const description =
  "Ask a due-diligence question about a junior mining company and get the exact NI 43-101 technical-report passages that answer it, with citations.";

export const metadata: Metadata = {
  title: "Project Due-Diligence Assistant - Junior Mining Intelligence",
  description,
  keywords: [
    "mining due diligence",
    "NI 43-101 report search",
    "technical report passages",
    "mining project research",
    "due diligence retrieval",
  ],
  openGraph: {
    title: "Project Due-Diligence Assistant - Junior Mining Intelligence",
    description,
    type: "website",
    url,
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "Project Due-Diligence Assistant",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Project Due-Diligence Assistant - Junior Mining Intelligence",
    description,
    images: ["/og-image.png"],
  },
  alternates: {
    canonical: url,
  },
};

export default function DueDiligenceLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
