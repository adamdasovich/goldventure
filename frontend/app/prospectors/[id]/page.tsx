import { Metadata } from "next";
import ProspectorProfileClient from "./ProspectorProfileClient";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function getProspector(id: string) {
  try {
    const response = await fetch(`${API_URL}/properties/prospectors/${id}/`, {
      cache: "no-store",
    });
    if (!response.ok) return null;
    return await response.json();
  } catch {
    return null;
  }
}

type Props = {
  params: Promise<{ id: string }>;
};

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { id } = await params;
  const prospector = await getProspector(id);

  if (!prospector) {
    return {
      title: "Prospector Not Found",
      description: "The requested prospector profile could not be found.",
    };
  }

  const name = prospector.display_name || prospector.username;
  const title = `${name} - Prospector Profile | Prospector's Exchange`;
  const description =
    prospector.bio?.slice(0, 155) ||
    `${name} is a prospector on Junior Mining Intelligence with ${prospector.active_listings || 0} active property listings.`;

  return {
    title,
    description,
    openGraph: {
      title,
      description,
      type: "profile",
      url: `https://juniorminingintelligence.com/prospectors/${id}`,
    },
    alternates: {
      canonical: `https://juniorminingintelligence.com/prospectors/${id}`,
    },
  };
}

export default function ProspectorProfilePage({ params }: Props) {
  return <ProspectorProfileClient params={params} />;
}
