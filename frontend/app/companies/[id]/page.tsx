import { Metadata } from "next";
import CompanyDetailClient from "./CompanyDetailClient";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function getCompany(id: string) {
  const fetchUrl = `${API_URL}/companies/${id}/`;

  try {
    const response = await fetch(fetchUrl, {
      cache: "no-store",
    });

    if (!response.ok) {
      return null;
    }

    return await response.json();
  } catch (error) {
    console.error("Failed to fetch company for metadata:", error);
    return null;
  }
}

type Props = {
  params: Promise<{ id: string }>;
};

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { id } = await params;
  const company = await getCompany(id);

  if (!company) {
    return {
      title: "Company Not Found",
      description: "The requested mining company could not be found.",
    };
  }

  const exchange = company.exchange || "TSXV";
  const ticker = company.ticker_symbol || "";
  const title = `${company.name} (${exchange}: ${ticker}) - Junior Mining Company Profile`;
  const description =
    company.description?.slice(0, 155) ||
    `${company.name} is a junior mining company listed on ${exchange} under ticker ${ticker}. View exploration projects, news releases, NI 43-101 reports, and financings.`;

  const images = company.logo_url ? [company.logo_url] : ["/og-image.png"];

  return {
    title,
    description,
    keywords: [
      company.name,
      ticker,
      `${exchange} ${ticker}`,
      "junior mining company",
      "mining stocks",
      "mineral exploration",
      "NI 43-101",
    ],
    openGraph: {
      title,
      description,
      type: "profile",
      images,
      url: `https://juniorminingintelligence.com/companies/${id}`,
    },
    twitter: {
      card: "summary_large_image",
      title,
      description,
      images,
    },
    alternates: {
      canonical: `https://juniorminingintelligence.com/companies/${id}`,
    },
  };
}

export default function CompanyDetailPage() {
  return <CompanyDetailClient />;
}
