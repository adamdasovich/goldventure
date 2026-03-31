import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Resource Library - Mining Books, Guides & Educational Materials",
  description:
    "Digital and physical resources for mining investors. Technical guides, NI 43-101 primers, geological reference books, and educational materials for mineral exploration.",
  keywords: [
    "mining books",
    "mining investment guides",
    "NI 43-101 guide",
    "geological reference",
    "mining education",
    "mineral exploration resources",
    "mining technical reports",
  ],
  openGraph: {
    title: "Resource Library - Mining Books & Educational Materials",
    description:
      "Digital and physical resources for mining investors, including technical guides and geological references.",
    type: "website",
    images: ["/og-image.png"],
    url: "https://juniorminingintelligence.com/store/resource-library",
  },
  alternates: {
    canonical: "https://juniorminingintelligence.com/store/resource-library",
  },
};

export default function ResourceLibraryLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
