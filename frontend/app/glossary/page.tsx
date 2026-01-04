'use client';

import { useState, useEffect } from 'react';
import Head from 'next/head';
import { Card, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import LogoMono from '@/components/LogoMono';
import GlossarySubmissionForm from '@/components/GlossarySubmissionForm';

interface GlossaryTerm {
  id?: number;
  term: string;
  definition: string;
  category: 'reporting' | 'geology' | 'finance' | 'regulatory' | 'operations' | 'general';
  relatedLinks?: { text: string; url: string }[];
  keywords?: string;
  created_at?: string;
  updated_at?: string;
}

// Fallback static terms (will be replaced by API data when available)
const fallbackGlossaryTerms: GlossaryTerm[] = [
  {
    term: "NI 43-101",
    definition: "Canadian National Instrument 43-101 is a regulatory standard for public disclosure of scientific and technical information concerning mineral projects. It requires independent qualified persons to prepare technical reports and resource estimates, ensuring transparency and accuracy in mining investment information.",
    category: "regulatory",
    relatedLinks: [
      { text: "View Companies with NI 43-101 Reports", url: "/companies" }
    ]
  },
  {
    term: "Indicated Resource",
    definition: "A mineral resource for which quantity, grade, densities, shape, and physical characteristics are estimated with sufficient confidence to allow the appropriate application of technical and economic parameters. Indicated resources have a higher level of confidence than inferred resources but lower than measured resources.",
    category: "reporting",
    relatedLinks: [
      { text: "Browse Mining Projects", url: "/companies" }
    ]
  },
  {
    term: "Inferred Resource",
    definition: "A mineral resource for which quantity and grade are estimated based on limited geological evidence and sampling. Inferred resources have the lowest level of geological confidence and should not be converted to mineral reserves. Further exploration is required to upgrade to indicated or measured categories.",
    category: "reporting"
  },
  {
    term: "Measured Resource",
    definition: "A mineral resource for which quantity, grade, densities, shape, and physical characteristics are estimated with confidence sufficient for the appropriate application of technical and economic parameters to support production planning. This is the highest level of geological confidence in resource estimation.",
    category: "reporting"
  },
  {
    term: "TSXV (TSX Venture Exchange)",
    definition: "The TSX Venture Exchange is Canada's premier public venture capital marketplace for emerging companies. It is the primary listing exchange for junior mining companies in Canada, providing access to capital for exploration and development projects. Many junior gold mining companies are listed on TSXV.",
    category: "finance",
    relatedLinks: [
      { text: "Explore TSXV Mining Stocks", url: "/companies" }
    ]
  },
  {
    term: "Grade (g/t)",
    definition: "The concentration of a valuable mineral within ore, typically expressed in grams per tonne (g/t) for precious metals like gold and silver. Higher grades indicate richer ore deposits and generally better economics. For example, 5 g/t gold means 5 grams of gold per tonne of ore.",
    category: "geology"
  },
  {
    term: "Heap Leaching",
    definition: "An industrial mining process used to extract precious metals from ore by placing crushed ore in large heaps and percolating a chemical solution through it to dissolve the valuable minerals. This method is economical for processing lower-grade ore deposits and is commonly used in gold mining operations.",
    category: "operations"
  },
  {
    term: "Feasibility Study",
    definition: "A comprehensive technical and economic study of a mineral project used to demonstrate whether the project is economically viable and technically feasible. Feasibility studies are required before a project can proceed to development and must be prepared by qualified persons under NI 43-101 standards.",
    category: "reporting",
    relatedLinks: [
      { text: "View Economic Studies", url: "/companies" }
    ]
  },
  {
    term: "Junior Mining Company",
    definition: "An exploration or development-stage mining company focused on discovering and developing new mineral deposits. Junior miners typically have market capitalizations under $500 million, limited production or revenue, and rely on equity financing for exploration programs. They carry higher risk but offer significant upside potential.",
    category: "finance",
    relatedLinks: [
      { text: "Browse Junior Gold Mining Companies", url: "/companies" }
    ]
  },
  {
    term: "Preliminary Economic Assessment (PEA)",
    definition: "An initial economic analysis of a mineral project that includes estimates of capital and operating costs, metal prices, and project economics. PEAs are less detailed than feasibility studies and carry higher uncertainty, but help determine if a project warrants further study.",
    category: "reporting"
  },
  {
    term: "Assay",
    definition: "The chemical analysis of rock, soil, or drill core samples to determine the concentration of valuable minerals or metals. Assay results are critical for resource estimation and are typically reported in parts per million (ppm) or grams per tonne (g/t) for precious metals.",
    category: "geology"
  },
  {
    term: "Drill Program",
    definition: "A systematic exploration program using diamond or reverse circulation drilling to obtain subsurface samples for geological and geochemical analysis. Drill programs are essential for resource definition, exploration targeting, and upgrading resource classifications.",
    category: "operations"
  },
  {
    term: "Cut-off Grade",
    definition: "The minimum grade of mineralization that can be economically mined and processed. Material below the cut-off grade is considered waste, while material above it is classified as ore. Cut-off grades depend on mining costs, processing costs, metal prices, and metallurgical recovery rates.",
    category: "geology"
  },
  {
    term: "Metallurgical Recovery",
    definition: "The percentage of valuable metal that can be extracted from ore during processing. For example, 90% gold recovery means that 90% of the gold in the ore can be recovered through milling and processing, with 10% lost to tailings.",
    category: "operations"
  },
  {
    term: "Ounce (Troy Ounce)",
    definition: "The standard unit of measurement for precious metals, equal to 31.1035 grams. Gold, silver, platinum, and palladium are typically quoted and traded in troy ounces. Not to be confused with the avoirdupois ounce (28.35 grams) used for everyday items.",
    category: "reporting"
  },
  {
    term: "Greenfield Exploration",
    definition: "Exploration activities conducted in areas with no previous mining or exploration history. Greenfield projects carry higher geological risk but offer potential for major new discoveries. Contrasts with brownfield exploration near existing mines or known deposits.",
    category: "operations"
  },
  {
    term: "Brownfield Exploration",
    definition: "Exploration conducted near existing mines or known mineral deposits to find additional resources or extensions. Brownfield exploration has lower geological risk than greenfield work because the geological setting is already understood.",
    category: "operations"
  },
  {
    term: "Qualified Person (QP)",
    definition: "Under NI 43-101, a qualified person is an engineer or geoscientist with at least five years of relevant experience in mineral exploration, mine development, or operations. QPs are responsible for preparing and approving technical reports and resource estimates.",
    category: "regulatory"
  },
  {
    term: "Mineral Reserve",
    definition: "The economically mineable portion of a measured or indicated mineral resource, demonstrated by at least a preliminary feasibility study. Mineral reserves include consideration of mining, metallurgical, economic, marketing, legal, and environmental factors.",
    category: "reporting"
  },
  {
    term: "Proven Reserve",
    definition: "The economically mineable portion of a measured mineral resource, representing the highest level of confidence in reserve estimation. Proven reserves are suitable for detailed mine planning and financing decisions.",
    category: "reporting"
  },
  {
    term: "Probable Reserve",
    definition: "The economically mineable portion of an indicated and, in some cases, a measured mineral resource. Probable reserves have a lower level of confidence than proven reserves but are still suitable for mine planning purposes.",
    category: "reporting"
  },
  {
    term: "Strike Length",
    definition: "The horizontal distance along which a mineralized zone extends. Greater strike lengths indicate larger potential deposits and are important factors in resource estimation and mine planning.",
    category: "geology"
  },
  {
    term: "True Width",
    definition: "The actual thickness of a mineralized zone measured perpendicular to its orientation. Drill holes rarely intersect mineralization at perfect right angles, so true width calculations are necessary to estimate tonnage accurately.",
    category: "geology"
  },
  {
    term: "Intercept",
    definition: "The length of mineralization encountered in a drill hole, typically reported with grade information. For example, '10 meters at 5 g/t gold' means the drill hole encountered 10 meters of material grading 5 grams of gold per tonne.",
    category: "geology"
  },
  {
    term: "Flow-Through Shares",
    definition: "A Canadian tax incentive that allows mining exploration companies to transfer tax deductions for exploration expenses to investors. Flow-through financing is a common method for junior miners to raise capital for exploration programs.",
    category: "finance"
  },
  {
    term: "Private Placement",
    definition: "A capital raising method where securities are sold directly to a small number of investors rather than through a public offering. Junior mining companies frequently use private placements to fund exploration and development activities.",
    category: "finance",
    relatedLinks: [
      { text: "Learn About Private Placements", url: "/financial-hub/private-placements-guide" }
    ]
  },
  {
    term: "Warrant",
    definition: "A security that gives the holder the right to purchase shares at a specified price (strike price) within a certain time period. Warrants are often issued as part of private placement financings in junior mining companies.",
    category: "finance"
  },
  {
    term: "All-in Sustaining Cost (AISC)",
    definition: "A comprehensive measure of the total cost to produce an ounce of gold, including mining, processing, administrative costs, sustaining capital, and exploration. AISC is the industry standard metric for comparing mining company costs.",
    category: "finance"
  },
  {
    term: "Stripping Ratio",
    definition: "The ratio of waste rock that must be removed to extract one tonne of ore in open-pit mining. Lower stripping ratios indicate better economics. For example, a 3:1 stripping ratio means 3 tonnes of waste must be removed for every tonne of ore mined.",
    category: "operations"
  },
  {
    term: "Tailings",
    definition: "The waste material left over after ore has been processed to extract valuable minerals. Tailings are typically stored in engineered facilities called tailings dams and must be managed to prevent environmental impacts.",
    category: "operations"
  },
  {
    term: "Mill",
    definition: "A facility where ore is crushed, ground, and processed to extract valuable minerals. Gold mills typically use gravity concentration, flotation, or cyanide leaching to recover gold from ore.",
    category: "operations"
  },
  {
    term: "Underground Mining",
    definition: "Mining method used to extract ore from deposits located deep beneath the surface. Underground mining is more expensive than open-pit but is necessary for deposits that are too deep or have too much overburden for surface mining.",
    category: "operations"
  },
  {
    term: "Open-Pit Mining",
    definition: "A surface mining method where ore is extracted from an open excavation. Open-pit mining is suitable for deposits near the surface and is generally less expensive than underground mining but creates larger environmental footprints.",
    category: "operations"
  },
  {
    term: "Orebody",
    definition: "A continuous, well-defined mass of material containing a sufficient concentration of valuable minerals to be economically mined. The size, grade, and geometry of the orebody determine the mining method and project economics.",
    category: "geology"
  },
  {
    term: "Geophysical Survey",
    definition: "The use of physical measurements (magnetic, electromagnetic, gravity, or seismic) to detect subsurface geological features and potential mineral deposits. Geophysical surveys are cost-effective exploration tools for identifying drill targets.",
    category: "operations"
  },
  {
    term: "Geochemical Survey",
    definition: "The systematic collection and analysis of soil, rock, or water samples to detect anomalous concentrations of target elements. Geochemical surveys help identify areas of mineralization for follow-up drilling.",
    category: "operations"
  },
  {
    term: "Alteration",
    definition: "Chemical and mineralogical changes in rocks caused by hydrothermal fluids or weathering. Certain types of alteration are associated with specific deposit types and serve as exploration indicators for mineralization.",
    category: "geology"
  },
  {
    term: "Vein",
    definition: "A sheet-like body of mineralized rock that fills a fracture or fault in the host rock. Gold veins are important exploration targets and have historically been significant sources of high-grade gold production.",
    category: "geology"
  },
  {
    term: "Disseminated Deposit",
    definition: "A mineral deposit where the valuable minerals are scattered throughout the host rock rather than concentrated in veins. Many large, low-grade gold deposits are disseminated deposits suitable for open-pit mining and heap leaching.",
    category: "geology"
  },
  {
    term: "Exploration Target",
    definition: "An estimate of the potential quantity and grade of mineralization in a target area, based on limited geological information. Exploration targets are not mineral resources and should be treated with appropriate caution.",
    category: "reporting"
  },
  {
    term: "Royalty",
    definition: "A payment made to the owner of mineral rights based on production or revenue from mining operations. Royalties are typically calculated as a percentage of gross revenue (NSR) or net profit and represent a ongoing financial obligation.",
    category: "finance"
  },
  {
    term: "Net Smelter Return (NSR)",
    definition: "A royalty calculated as a percentage of the gross revenue from metal sales, minus refining and transport costs. NSR royalties are common in mining agreements and are paid to property owners or previous owners.",
    category: "finance"
  },
  {
    term: "Concentrate",
    definition: "The product of ore processing that contains a high percentage of valuable minerals. Concentrates are typically shipped to smelters for final metal extraction and are the main revenue source for many mining operations.",
    category: "operations"
  },
  {
    term: "Recovery Rate",
    definition: "The percentage of valuable metal recovered from ore during processing, after accounting for losses in milling, concentration, and smelting. Higher recovery rates improve project economics.",
    category: "operations"
  },
  {
    term: "Dilution",
    definition: "The unintentional mining of waste rock along with ore, which lowers the average grade of material sent to the mill. Dilution is a normal part of mining and must be accounted for in mine planning and resource estimation.",
    category: "operations"
  },
  {
    term: "Mine Life",
    definition: "The estimated number of years a mine can operate based on proven and probable reserves and planned production rates. Longer mine lives generally indicate more valuable projects and better access to financing.",
    category: "reporting"
  },
  {
    term: "Payback Period",
    definition: "The length of time required for a mining project to recover its initial capital investment from operating cash flows. Shorter payback periods indicate lower financial risk and are favored by investors and lenders.",
    category: "finance"
  },
  {
    term: "Net Present Value (NPV)",
    definition: "The present value of future cash flows from a mining project, discounted at an appropriate rate to account for the time value of money. NPV is a key metric for evaluating project economics, with higher NPV indicating better investment returns.",
    category: "finance"
  },
  {
    term: "Internal Rate of Return (IRR)",
    definition: "The discount rate at which the net present value of a project equals zero. IRR represents the expected annual return on investment and is used to compare mining projects. Higher IRR indicates better project economics.",
    category: "finance"
  },
  {
    term: "Accredited Investor",
    definition: "An individual or entity that meets specific income or net worth requirements allowing them to participate in private placement financings. In Canada, accredited investors can invest in flow-through shares and private placements offered by junior mining companies.",
    category: "regulatory",
    relatedLinks: [
      { text: "Learn About Investor Qualification", url: "/financial-hub/qualification" }
    ]
  },
  {
    term: "Preliminary Feasibility Study (PFS)",
    definition: "Also known as a pre-feasibility study, this is a comprehensive study of a mineral project's viability that includes detailed engineering, cost estimates, and economic analysis. A PFS has greater confidence than a PEA but less than a full feasibility study.",
    category: "reporting"
  },
  {
    term: "Mineral Resource",
    definition: "A concentration or occurrence of material of intrinsic economic interest in or on the Earth's crust in such form, quality, and quantity that there are reasonable prospects for eventual economic extraction. Resources are classified as measured, indicated, or inferred.",
    category: "reporting"
  },
  {
    term: "Exploration Stage",
    definition: "The phase of a mining project focused on discovering and defining mineral deposits through geological mapping, sampling, and drilling. Most junior mining companies are in the exploration stage and have not yet achieved production.",
    category: "operations",
    relatedLinks: [
      { text: "Browse Exploration Companies", url: "/companies" }
    ]
  },
  {
    term: "Development Stage",
    definition: "The phase between exploration and production where a company conducts detailed engineering, obtains permits, arranges financing, and constructs mine infrastructure. Development-stage projects have defined resources and are advancing toward production.",
    category: "operations"
  },
  {
    term: "Production Stage",
    definition: "The operational phase where a mine is extracting ore, processing it, and selling metal concentrate or refined metal. Production-stage companies generate revenue and cash flow from mining operations.",
    category: "operations"
  },
  {
    term: "Drill Core",
    definition: "Cylindrical rock samples extracted from the ground using diamond drilling. Core samples provide continuous geological information and are split for assaying to determine mineral content and grade.",
    category: "geology"
  },
  {
    term: "Gold Equivalent (AuEq)",
    definition: "A metric that converts the value of other metals (silver, copper, etc.) into equivalent gold ounces based on relative metal prices and recovery rates. Gold equivalent allows comparison of multi-metal deposits on a single metric basis.",
    category: "reporting"
  }
];

const categories = [
  { id: 'all', label: 'All Terms' },
  { id: 'reporting', label: 'Reporting & Resources' },
  { id: 'geology', label: 'Geology & Exploration' },
  { id: 'finance', label: 'Finance & Investment' },
  { id: 'regulatory', label: 'Regulatory & Standards' },
  { id: 'operations', label: 'Mining Operations' }
];

export default function GlossaryPage() {
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [glossaryTerms, setGlossaryTerms] = useState<GlossaryTerm[]>(fallbackGlossaryTerms);
  const [isLoading, setIsLoading] = useState(true);
  const [apiError, setApiError] = useState<string | null>(null);
  const [isSubmissionFormOpen, setIsSubmissionFormOpen] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [showSuccessMessage, setShowSuccessMessage] = useState(false);

  // Check authentication status
  useEffect(() => {
    const token = localStorage.getItem('accessToken');
    setIsAuthenticated(!!token);
  }, []);

  // Fetch glossary terms from API
  useEffect(() => {
    const fetchGlossaryTerms = async () => {
      try {
        // Request all terms with a large page size to avoid pagination
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/glossary/?page_size=200`);
        if (response.ok) {
          const data = await response.json();
          // API returns paginated results with 'results' array
          const terms = Array.isArray(data) ? data : (data.results || []);
          if (terms.length > 0) {
            setGlossaryTerms(terms);
            setApiError(null);
          }
        } else {
          console.warn('Failed to fetch glossary from API, using fallback data');
          setApiError('Using cached glossary data');
        }
      } catch (error) {
        console.error('Error fetching glossary:', error);
        setApiError('Using cached glossary data');
      } finally {
        setIsLoading(false);
      }
    };

    fetchGlossaryTerms();
  }, []);

  const handleSubmissionSuccess = () => {
    setShowSuccessMessage(true);
    setTimeout(() => setShowSuccessMessage(false), 5000);
  };

  // Filter terms based on category and search
  const filteredTerms = glossaryTerms
    .filter(term => selectedCategory === 'all' || term.category === selectedCategory)
    .filter(term =>
      term.term.toLowerCase().includes(searchQuery.toLowerCase()) ||
      term.definition.toLowerCase().includes(searchQuery.toLowerCase())
    )
    .sort((a, b) => a.term.localeCompare(b.term));

  // Group terms by first letter
  const groupedTerms = filteredTerms.reduce((acc, term) => {
    const firstLetter = term.term[0].toUpperCase();
    if (!acc[firstLetter]) {
      acc[firstLetter] = [];
    }
    acc[firstLetter].push(term);
    return acc;
  }, {} as Record<string, GlossaryTerm[]>);

  // Full alphabet A-Z
  const allLetters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('');
  const letters = allLetters;

  // Generate DefinedTermSet schema for SEO
  const schemaMarkup = {
    '@context': 'https://schema.org',
    '@type': 'DefinedTermSet',
    name: 'Junior Gold Mining Industry Glossary',
    description: 'Comprehensive glossary of technical terms, standards, and definitions used in junior gold mining, mineral exploration, NI 43-101 standards, TSXV listings, and mining investment. Essential resource for understanding mining terminology.',
    url: 'https://juniorgoldminingintelligence.com/glossary',
    inLanguage: 'en-US',
    dateModified: new Date().toISOString().split('T')[0],
    publisher: {
      '@type': 'Organization',
      name: 'Junior Gold Mining Intelligence',
      url: 'https://juniorgoldminingintelligence.com',
      description: 'Junior gold mining data, stock intelligence, and industry analysis platform'
    },
    about: [
      {
        '@type': 'Thing',
        '@id': 'https://www.wikidata.org/wiki/Q44626',
        name: 'Junior Mining'
      },
      {
        '@type': 'Thing',
        '@id': 'https://www.wikidata.org/wiki/Q897308',
        name: 'Gold Mining'
      },
      {
        '@type': 'Thing',
        name: 'NI 43-101 Technical Reports'
      },
      {
        '@type': 'Thing',
        name: 'TSX Venture Exchange Mining'
      }
    ],
    hasDefinedTerm: (glossaryTerms || []).map(term => ({
      '@type': 'DefinedTerm',
      '@id': `https://juniorgoldminingintelligence.com/glossary#${term.term.toLowerCase().replace(/[^a-z0-9]+/g, '-')}`,
      name: term.term,
      description: term.definition,
      inDefinedTermSet: 'Junior Gold Mining Industry Glossary',
      termCode: term.category,
      ...(term.keywords && {
        alternateName: term.keywords.split(',').map(k => k.trim()).slice(0, 3)
      })
    }))
  };

  return (
    <>
      {/* SEO Meta Tags */}
      <Head>
        <title>Junior Gold Mining Glossary - NI 43-101, TSXV & Mining Terms | Junior Gold Mining Intelligence</title>
        <meta
          name="description"
          content="Comprehensive glossary of 60+ junior gold mining terms covering NI 43-101 standards, TSXV listings, mineral resources, exploration geology, and mining investment. Essential definitions for understanding junior mining stocks."
        />
        <meta name="keywords" content="junior gold mining glossary, NI 43-101 terms, mining definitions, TSXV mining, indicated resource, feasibility study, junior mining company, gold exploration terms" />
        <link rel="canonical" href="https://juniorgoldminingintelligence.com/glossary" />
        <meta property="og:title" content="Junior Gold Mining Industry Glossary - 60+ Essential Terms" />
        <meta property="og:description" content="Learn junior gold mining terminology: NI 43-101, indicated resources, feasibility studies, TSXV listings, and exploration terms." />
        <meta property="og:url" content="https://juniorgoldminingintelligence.com/glossary" />
        <meta property="og:type" content="website" />
      </Head>

      <div className="min-h-screen bg-slate-900">
        {/* Schema Markup */}
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(schemaMarkup) }}
        />

      {/* Navigation */}
      <nav className="glass-nav sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-24">
            <div className="flex items-center space-x-3">
              <div className="cursor-pointer" onClick={() => window.location.href = '/'}>
                <LogoMono className="h-18" />
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <Button variant="ghost" size="sm" onClick={() => window.location.href = '/'}>Home</Button>
              <Button variant="ghost" size="sm" onClick={() => window.location.href = '/dashboard'}>Dashboard</Button>
              <Button variant="ghost" size="sm" onClick={() => window.location.href = '/companies'}>Companies</Button>
              <Button variant="ghost" size="sm" onClick={() => window.location.href = '/properties'}>Properties</Button>
              <Button variant="primary" size="sm">Glossary</Button>
              <Button variant="ghost" size="sm" onClick={() => window.location.href = '/metals'}>Metals</Button>
            </div>
          </div>
        </div>
      </nav>

      {/* Header */}
      <div className="bg-gradient-to-b from-slate-800 to-slate-900 border-b border-slate-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="flex items-start justify-between gap-4 mb-4">
            <div className="flex-1">
              <h1 className="text-4xl md:text-5xl font-bold text-gradient-gold mb-4">
                Junior Gold Mining Glossary
              </h1>
            </div>
            <Button
              variant="primary"
              size="sm"
              onClick={() => {
                if (!isAuthenticated) {
                  alert('Please log in to submit glossary terms');
                  window.location.href = '/';
                  return;
                }
                setIsSubmissionFormOpen(true);
              }}
              className="mt-2"
            >
              <svg className="w-4 h-4 mr-2 inline" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Submit New Term
            </Button>
          </div>

          {showSuccessMessage && (
            <div className="mb-4 p-4 bg-green-500/20 border border-green-500/50 rounded-lg">
              <p className="text-green-300 font-medium">
                ✓ Term submitted successfully! Your submission will be reviewed by our team.
              </p>
            </div>
          )}

          <p className="text-xl text-slate-300 max-w-3xl">
            Essential terms and definitions for understanding junior gold mining, exploration, NI 43-101 standards, TSXV listings, and mining investment fundamentals.
          </p>
          <p className="text-slate-400 mt-4">
            {glossaryTerms.length} terms covering reporting standards, geology, finance, regulatory requirements, and mining operations.
          </p>
        </div>
      </div>

      {/* Filters and Search */}
      <div className="sticky top-0 z-40 bg-slate-900/95 backdrop-blur-sm border-b border-slate-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          {/* Search */}
          <div className="mb-4">
            <input
              type="text"
              placeholder="Search glossary terms..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-4 py-2.5 glass-light rounded-lg border border-slate-600 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-gold-500"
            />
          </div>

          {/* Category Filters */}
          <div className="flex flex-wrap gap-2">
            {categories.map(cat => (
              <Button
                key={cat.id}
                variant={selectedCategory === cat.id ? 'primary' : 'ghost'}
                size="sm"
                onClick={() => setSelectedCategory(cat.id)}
              >
                {cat.label}
              </Button>
            ))}
          </div>

          {/* Letter Navigation */}
          <div className="mt-4 flex flex-wrap gap-2">
            {letters && letters.map(letter => {
              const hasTerms = groupedTerms && groupedTerms[letter] && groupedTerms[letter].length > 0;
              return hasTerms ? (
                <a
                  key={letter}
                  href={`#letter-${letter}`}
                  className="w-8 h-8 flex items-center justify-center rounded border border-gold-500/30 text-gold-400 hover:bg-gold-500/20 transition-colors text-sm font-medium"
                >
                  {letter}
                </a>
              ) : (
                <span
                  key={letter}
                  className="w-8 h-8 flex items-center justify-center rounded border border-slate-700/30 text-slate-600 text-sm font-medium cursor-not-allowed"
                >
                  {letter}
                </span>
              );
            })}
          </div>
        </div>
      </div>

      {/* Terms List */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {filteredTerms.length === 0 ? (
          <Card variant="glass-card">
            <CardHeader>
              <CardTitle>No terms found</CardTitle>
              <CardDescription>
                Try adjusting your search or filter criteria.
              </CardDescription>
            </CardHeader>
          </Card>
        ) : (
          <div className="space-y-12">
            {letters.map(letter => {
              // Only render letters that have terms
              if (!groupedTerms[letter] || groupedTerms[letter].length === 0) {
                return null;
              }
              return (
              <div key={letter} id={`letter-${letter}`}>
                <h2 className="text-3xl font-bold text-gold-400 mb-6 pb-2 border-b border-slate-700">
                  {letter}
                </h2>
                <div className="space-y-6">
                  {groupedTerms[letter].map((term, idx) => (
                    <Card key={idx} variant="glass-card">
                      <CardHeader>
                        <div className="flex items-start justify-between gap-4">
                          <div className="flex-1">
                            <CardTitle className="text-2xl mb-2">
                              {term.term}
                            </CardTitle>
                            <CardDescription className="text-base leading-relaxed">
                              {term.definition}
                            </CardDescription>
                            {term.relatedLinks && term.relatedLinks.length > 0 && (
                              <div className="mt-4 flex flex-wrap gap-2">
                                {term.relatedLinks.map((link, linkIdx) => (
                                  <a
                                    key={linkIdx}
                                    href={link.url}
                                    className="text-sm text-gold-400 hover:text-gold-300 underline"
                                  >
                                    {link.text} →
                                  </a>
                                ))}
                              </div>
                            )}
                          </div>
                          <span className="text-xs px-2 py-1 rounded bg-slate-700/50 text-slate-400 whitespace-nowrap">
                            {categories.find(c => c.id === term.category)?.label.split(' ')[0]}
                          </span>
                        </div>
                      </CardHeader>
                    </Card>
                  ))}
                </div>
              </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Related Resources */}
      <div className="bg-slate-800/50 border-t border-slate-700 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <h2 className="text-2xl font-bold text-gold-400 mb-6">Related Resources</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card variant="glass-card">
              <CardHeader>
                <CardTitle>Browse Companies</CardTitle>
                <CardDescription>
                  Explore junior gold mining companies with detailed technical reports and resource estimates.
                </CardDescription>
                <a href="/companies" className="text-gold-400 hover:text-gold-300 mt-4 inline-block">
                  View All Companies →
                </a>
              </CardHeader>
            </Card>
            <Card variant="glass-card">
              <CardHeader>
                <CardTitle>Financial Hub</CardTitle>
                <CardDescription>
                  Learn about private placements, accredited investor requirements, and mining investment fundamentals.
                </CardDescription>
                <a href="/financial-hub" className="text-gold-400 hover:text-gold-300 mt-4 inline-block">
                  Explore Financial Hub →
                </a>
              </CardHeader>
            </Card>
            <Card variant="glass-card">
              <CardHeader>
                <CardTitle>Prospector's Exchange</CardTitle>
                <CardDescription>
                  Browse exploration properties, mining projects, and mineral claims available for partnership or sale.
                </CardDescription>
                <a href="/properties" className="text-gold-400 hover:text-gold-300 mt-4 inline-block">
                  View Properties →
                </a>
              </CardHeader>
            </Card>
          </div>
        </div>
      </div>

      {/* Submission Form Modal */}
      <GlossarySubmissionForm
        isOpen={isSubmissionFormOpen}
        onClose={() => setIsSubmissionFormOpen(false)}
        onSubmitSuccess={handleSubmissionSuccess}
      />
      </div>
    </>
  );
}
