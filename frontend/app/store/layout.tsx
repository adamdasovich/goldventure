import { Metadata } from "next";
import { TheTicker } from "@/components/store/TheTicker";
import { StoreHeader } from "@/components/store/StoreHeader";

export const metadata: Metadata = {
  title: "Mining Store - Rare Specimens, Field Gear & Resources",
  description:
    "Shop rare mineral specimens, prospecting field gear, and educational resources for gold mining enthusiasts. Authenticated mining collectibles from junior mining properties.",
  keywords: [
    "mining specimens",
    "gold specimens",
    "mineral specimens for sale",
    "prospecting gear",
    "mining field equipment",
    "mineral collecting",
    "gold nuggets",
    "mining books",
    "geological specimens",
    "mining memorabilia",
  ],
  openGraph: {
    title: "Mining Store - Rare Specimens & Field Gear",
    description:
      "Shop rare mineral specimens, prospecting gear, and educational resources for mining enthusiasts.",
    type: "website",
    images: ["/og-image.png"],
    url: "https://juniorminingintelligence.com/store",
  },
  twitter: {
    card: "summary_large_image",
    title: "Mining Store - Rare Specimens & Field Gear",
    description:
      "Shop rare mineral specimens, prospecting gear, and educational resources for mining enthusiasts.",
  },
  alternates: {
    canonical: "https://juniorminingintelligence.com/store",
  },
};

export default function StoreLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-slate-900">
      {/* Store Header with Navigation */}
      <StoreHeader />

      {/* The Ticker Banner */}
      <TheTicker variant="banner" />

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </div>
    </div>
  );
}
