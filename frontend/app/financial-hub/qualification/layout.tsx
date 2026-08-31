import type { Metadata } from "next";

/**
 * Metadata for accredited investor qualification.
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
  title: "Accredited Investor Qualification — Financial Hub",
  description:
    "Set your accredited investor status. Registering interest in a financing is open to any account holder; accredited status unlocks additional deals.",
  alternates: {
    canonical: "https://juniorminingintelligence.com/financial-hub/qualification",
  },
  // See the note above: remove this once the page renders content.
  robots: { index: false, follow: true },
  openGraph: {
    title: "Accredited Investor Qualification — Financial Hub",
    description:
      "Set your accredited investor status. Registering interest in a financing is open to any account holder; accredited status unlocks additional deals.",
    url: "https://juniorminingintelligence.com/financial-hub/qualification",
    type: "website",
    siteName: "Junior Mining Intelligence",
    images: [{ url: "/og-image.png", width: 1200, height: 630 }],
  },
};

export default function QualificationLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
