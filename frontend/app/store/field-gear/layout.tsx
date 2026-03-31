import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Field Gear - Prospecting Equipment & Mining Tools",
  description:
    "Shop professional prospecting equipment, mining field gear, and exploration tools. Hand lenses, rock hammers, sample bags, GPS units, and essential gear for mineral exploration.",
  keywords: [
    "prospecting equipment",
    "mining field gear",
    "rock hammer",
    "hand lens geology",
    "prospecting tools",
    "mineral exploration gear",
    "gold panning equipment",
    "geological field equipment",
  ],
  openGraph: {
    title: "Field Gear - Prospecting Equipment & Mining Tools",
    description:
      "Professional prospecting equipment and mining field gear for mineral exploration.",
    type: "website",
    images: ["/og-image.png"],
    url: "https://juniorminingintelligence.com/store/field-gear",
  },
  alternates: {
    canonical: "https://juniorminingintelligence.com/store/field-gear",
  },
};

export default function FieldGearLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
