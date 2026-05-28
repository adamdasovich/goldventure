import HomeClient from "./HomeClient";

const API_BASE_URL =
  process.env.API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000/api";

const faqPageJsonLd = {
  "@context": "https://schema.org",
  "@type": "FAQPage",
  mainEntity: [
    {
      "@type": "Question",
      name: "What is a junior mining company?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "A junior mining company is a small to mid-sized exploration or development company focused on discovering and developing mineral deposits including gold, silver, lithium, copper, rare earths, and other critical minerals. These companies typically have market capitalizations under $500 million and are listed on exchanges like the TSX Venture Exchange (TSXV) or TSX.",
      },
    },
    {
      "@type": "Question",
      name: "What is NI 43-101?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "NI 43-101 is a Canadian National Instrument that sets standards for disclosure of scientific and technical information about mineral projects. It requires all public disclosures of mineral resources and reserves to be prepared or supervised by a Qualified Person and to follow strict reporting standards.",
      },
    },
    {
      "@type": "Question",
      name: "How do I track junior mining stocks?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "Junior Mining Intelligence provides a comprehensive platform to track 500+ junior mining companies exploring gold, silver, lithium, copper, rare earths, and critical minerals. Features include real-time exploration data, NI 43-101 technical reports, mineral resource estimates, project financings, and AI-powered analysis. Our database includes companies listed on TSXV, TSX, and other major exchanges.",
      },
    },
    {
      "@type": "Question",
      name: "What data does the platform provide?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "Our platform provides comprehensive data including: company profiles and management teams, NI 43-101 technical reports, mineral resource estimates (gold, silver, copper, lithium, rare earths, nickel), exploration project details and locations, financing history and market data, news releases and press announcements, AI-powered company analysis, and real-time precious metals and critical minerals pricing.",
      },
    },
    {
      "@type": "Question",
      name: "What are mineral resource categories?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "Under NI 43-101, mineral resources are classified into three categories based on geological confidence: Inferred Resources (lowest confidence), Indicated Resources (moderate confidence), and Measured Resources (highest confidence). Measured and Indicated Resources can be converted to Mineral Reserves after economic feasibility is demonstrated.",
      },
    },
  ],
};

export default async function Home() {
  let initialArticles: any[] = [];

  try {
    const res = await fetch(
      `${API_BASE_URL}/news/articles/?limit=8&offset=0&days=7`,
      // 15-min ISR: news is fresh enough for crawlers; saves per-request
      // round-trips to the Django API on the homepage.
      { next: { revalidate: 900 } },
    );
    if (res.ok) {
      const data = await res.json();
      initialArticles = data.articles || [];
    }
  } catch {
    // Fall back to client-side fetch
  }

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(faqPageJsonLd) }}
      />
      <HomeClient initialArticles={initialArticles} />
    </>
  );
}
