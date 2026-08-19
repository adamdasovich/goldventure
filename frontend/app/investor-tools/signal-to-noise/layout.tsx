import { Metadata } from "next";

const url =
  "https://juniorminingintelligence.com/investor-tools/signal-to-noise";
const description =
  "Measure what share of a mining company's news reports an actual result — drill intercepts, resource updates, studies — versus corporate filler. Sector average is about 25%.";

// Without this file the route inherits investor-tools/layout.tsx, including
// its canonical — which pointed this page at /investor-tools and told Google
// to drop it from the index.
export const metadata: Metadata = {
  title: "Signal-to-Noise Ratio - Is This Mining Company Actually Exploring?",
  description,
  keywords: [
    "mining news analysis",
    "junior mining promotion",
    "drill results vs press releases",
    "mining company signal to noise",
    "explorer or promoter",
    "junior mining red flags",
  ],
  openGraph: {
    title:
      "Signal-to-Noise Ratio - Is This Mining Company Actually Exploring? | Junior Mining Intelligence",
    description,
    type: "website",
    url,
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "Signal-to-Noise Ratio",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Signal-to-Noise Ratio - Is This Mining Company Actually Exploring?",
    description,
    images: ["/og-image.png"],
  },
  alternates: {
    canonical: url,
  },
};

export default function SignalToNoiseLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
