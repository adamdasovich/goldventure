import type { Metadata } from "next";

/**
 * Metadata for the Educational Hub.
 *
 * Without this file the page inherited app/financial-hub/layout.tsx, whose
 * canonical is /financial-hub — so this route declared itself a duplicate of
 * the parent and shared its title. Anything published here would have been
 * canonicalised away.
 *
 * noindex until it renders something. The page is a client component that
 * shows a spinner on first render, so a crawler receives no content at all —
 * which is the thin-page pattern this project has been removing everywhere
 * else. Delete the robots block below once there is content to index.
 */
export const metadata: Metadata = {
  title: "Mining Investment Education — Financial Hub",
  description:
    "Learn how junior mining financings work before taking part: placement structures, subscription agreements, hold periods and what accredited status changes.",
  alternates: {
    canonical: "https://juniorminingintelligence.com/financial-hub/education",
  },
  // See the note above: remove this once the page renders content.
  robots: { index: false, follow: true },
  openGraph: {
    title: "Mining Investment Education — Financial Hub",
    description:
      "Learn how junior mining financings work before taking part: placement structures, subscription agreements, hold periods and what accredited status changes.",
    url: "https://juniorminingintelligence.com/financial-hub/education",
    type: "website",
    siteName: "Junior Mining Intelligence",
    images: [{ url: "/og-image.png", width: 1200, height: 630 }],
  },
};

export default function EducationLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
