import { Metadata } from "next";

export const metadata: Metadata = {
  title: "The Vault - Rare Mineral Specimens & Mining Collectibles",
  description:
    "Browse authenticated rare mineral specimens, gold nuggets, and premium mining collectibles. Each specimen verified with provenance documentation from junior mining properties.",
  keywords: [
    "rare mineral specimens",
    "gold specimens for sale",
    "mineral collectibles",
    "authenticated specimens",
    "gold nuggets",
    "mining collectibles",
    "geological specimens",
    "mineral collection",
  ],
  openGraph: {
    title: "The Vault - Rare Mineral Specimens",
    description:
      "Authenticated rare mineral specimens and gold nuggets from junior mining properties.",
    type: "website",
    images: ["/og-image.png"],
    url: "https://juniorminingintelligence.com/store/vault",
  },
  alternates: {
    canonical: "https://juniorminingintelligence.com/store/vault",
  },
};

export default function VaultLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
