import { Metadata } from "next";

export const metadata: Metadata = {
  title:
    "Subscription Agreements Guide - Mining Investment Contracts Explained",
  description:
    "Understand subscription agreements for junior mining investments. Learn key clauses, investor protections, representations and warranties, and what to review before signing.",
  keywords: [
    "subscription agreement guide",
    "mining investment contracts",
    "subscription agreement clauses",
    "investor protections",
    "private placement subscription",
    "mining securities",
    "accredited investor agreement",
  ],
  openGraph: {
    title: "Subscription Agreements Guide - Mining Investment Contracts",
    description:
      "Understand subscription agreements for junior mining investments and what to review before signing.",
    type: "article",
    url: "https://juniorminingintelligence.com/financial-hub/subscription-agreements-guide",
  },
  alternates: {
    canonical:
      "https://juniorminingintelligence.com/financial-hub/subscription-agreements-guide",
  },
};

export default function SubscriptionAgreementsGuideLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
