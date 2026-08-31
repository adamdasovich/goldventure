import EducationClient from "./EducationClient";

const API_BASE_URL =
  process.env.API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000/api";

/**
 * Server shell for the Financial Hub education page.
 *
 * The page was a client component that fetched its modules on mount, so a
 * crawler received a spinner and the words "Loading modules...". Four
 * published modules existed the whole time and none of them was ever in the
 * HTML. The endpoint also required authentication until now, so anonymous
 * visitors got a 401 behind that spinner.
 *
 * Fetching here and passing the result in as initialData is the same pattern
 * /open-financings and /companies use. The client keeps its own fetch as a
 * refresh, because completion status is per-user and cannot come from a
 * response shared by every visitor.
 */
export const revalidate = 3600;

interface EducationalModule {
  id: number;
  module_type: string;
  title: string;
  description: string;
  content?: string;
  estimated_read_time_minutes: number;
  is_required: boolean;
  completion_status: null;
}

async function fetchModules(): Promise<EducationalModule[]> {
  // Retry rather than swallow: returning [] on a blip would bake the spinner
  // back into the static render and undo the point of this file.
  for (let attempt = 0; attempt < 3; attempt++) {
    try {
      const res = await fetch(`${API_BASE_URL}/education/modules/`, {
        next: { revalidate: 3600 },
      });
      if (!res.ok) break;
      const data = await res.json();
      return Array.isArray(data) ? data : data.results || [];
    } catch {
      if (attempt === 2) break;
      await new Promise((r) => setTimeout(r, 500 * (attempt + 1)));
    }
  }
  return [];
}

export default async function EducationPage() {
  const modules = await fetchModules();
  return <EducationClient initialModules={modules} />;
}
