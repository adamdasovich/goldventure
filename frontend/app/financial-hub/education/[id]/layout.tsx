import type { Metadata } from "next";

const API_BASE_URL =
  process.env.API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000/api";

/**
 * Per-module metadata.
 *
 * Without this, every module page inherited the education layout's canonical
 * and declared itself a duplicate of /financial-hub/education — the same fault
 * that had five Financial Hub routes claiming to be copies of the parent. Four
 * distinct modules pointing at one URL would have made expanding any of them
 * pointless.
 *
 * noindex for now. Each module carries roughly 300 characters of body, which
 * is not enough to justify indexing, and the page is a client component that
 * renders a spinner to a crawler regardless. Remove the robots block once the
 * modules carry real content AND the page renders it server-side; the
 * education listing shows the initialData pattern that does that.
 */

interface Module {
  id: number;
  title: string;
  description: string;
  estimated_read_time_minutes: number;
}

async function fetchModule(id: string): Promise<Module | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/education/modules/${id}/`, {
      next: { revalidate: 3600 },
    });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

type Props = {
  params: Promise<{ id: string }>;
  children: React.ReactNode;
};

export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string }>;
}): Promise<Metadata> {
  const { id } = await params;
  const canonical = `https://juniorminingintelligence.com/financial-hub/education/${id}`;
  const module = await fetchModule(id);

  if (!module) {
    return {
      title: "Module — Financial Hub",
      alternates: { canonical },
      robots: { index: false, follow: true },
    };
  }

  const minutes = module.estimated_read_time_minutes;
  return {
    title: `${module.title} — Mining Investment Education`,
    description:
      module.description ||
      `A ${minutes}-minute module on junior mining financing from the Junior Mining Intelligence education hub.`,
    alternates: { canonical },
    robots: { index: false, follow: true },
  };
}

export default function EducationModuleLayout({ children }: Props) {
  return children;
}
