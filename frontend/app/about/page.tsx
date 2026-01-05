import { Metadata } from 'next';
import Link from 'next/link';
import { OrganizationSchema } from '@/components/StructuredData';

export const metadata: Metadata = {
  title: 'About Us - Junior Mining Intelligence Platform',
  description: 'Learn about Junior Mining Intelligence, the AI-powered platform providing comprehensive analysis and data on 500+ junior mining companies exploring gold, silver, lithium, copper, rare earths, and critical minerals.',
  keywords: [
    'about junior mining intelligence',
    'mining data platform',
    'junior mining research',
    'AI mining analysis',
    'NI 43-101 reports',
    'mining investment research',
    'TSXV mining companies',
  ],
  openGraph: {
    title: 'About Us - Junior Mining Intelligence Platform',
    description: 'AI-powered platform providing comprehensive analysis and data on 500+ junior mining companies exploring gold, silver, lithium, copper, rare earths, and critical minerals.',
    url: 'https://juniorminingintelligence.com/about',
    type: 'website',
    images: [
      {
        url: '/og-image.png',
        width: 1200,
        height: 630,
        alt: 'Junior Mining Intelligence Platform',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'About Us - Junior Mining Intelligence Platform',
    description: 'AI-powered platform providing comprehensive analysis and data on 500+ junior mining companies.',
    images: ['/og-image.png'],
  },
  alternates: {
    canonical: 'https://juniorminingintelligence.com/about',
  },
};

// AboutPage structured data
const aboutPageSchema = {
  '@context': 'https://schema.org',
  '@type': 'AboutPage',
  '@id': 'https://juniorminingintelligence.com/about',
  url: 'https://juniorminingintelligence.com/about',
  name: 'About Junior Mining Intelligence',
  description: 'Learn about Junior Mining Intelligence, the AI-powered platform providing comprehensive analysis and data on 500+ junior mining companies.',
  mainEntity: {
    '@type': 'Organization',
    '@id': 'https://juniorminingintelligence.com/#organization',
    name: 'Junior Mining Intelligence',
  },
  breadcrumb: {
    '@type': 'BreadcrumbList',
    itemListElement: [
      {
        '@type': 'ListItem',
        position: 1,
        name: 'Home',
        item: 'https://juniorminingintelligence.com',
      },
      {
        '@type': 'ListItem',
        position: 2,
        name: 'About',
        item: 'https://juniorminingintelligence.com/about',
      },
    ],
  },
};

export default function AboutPage() {
  return (
    <>
      {/* Structured Data */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(aboutPageSchema) }}
      />
      <OrganizationSchema />

      <div className="min-h-screen bg-gradient-to-b from-slate-900 via-slate-800 to-slate-900">
        {/* Hero Section */}
        <section className="relative py-20 px-4 overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-r from-amber-500/10 to-amber-600/5" />
          <div className="relative max-w-7xl mx-auto">
            <div className="text-center">
              <h1 className="text-5xl md:text-6xl font-bold text-white mb-6">
                About Junior Mining Intelligence
              </h1>
              <p className="text-xl md:text-2xl text-slate-300 max-w-4xl mx-auto leading-relaxed">
                AI-powered platform providing comprehensive analysis and data on 500+ junior mining companies
                exploring gold, silver, lithium, copper, rare earths, and critical minerals.
              </p>
            </div>
          </div>
        </section>

        {/* Mission Section */}
        <section className="py-16 px-4 bg-slate-800/50">
          <div className="max-w-6xl mx-auto">
            <div className="grid md:grid-cols-2 gap-12 items-center">
              <div>
                <h2 className="text-3xl md:text-4xl font-bold text-white mb-6">
                  Our Mission
                </h2>
                <p className="text-lg text-slate-300 mb-4 leading-relaxed">
                  We democratize access to junior mining intelligence by aggregating, analyzing, and presenting
                  critical data on exploration companies across precious metals, battery metals, and critical minerals.
                </p>
                <p className="text-lg text-slate-300 leading-relaxed">
                  Our platform empowers investors, analysts, and industry professionals with real-time data,
                  NI 43-101 technical reports, resource estimates, and AI-powered insights to make informed
                  decisions in the junior mining sector.
                </p>
              </div>
              <div className="bg-gradient-to-br from-amber-500/20 to-amber-600/10 p-8 rounded-lg border border-amber-500/30">
                <h3 className="text-2xl font-semibold text-amber-400 mb-4">What We Track</h3>
                <ul className="space-y-3 text-slate-300">
                  <li className="flex items-start">
                    <span className="text-amber-500 mr-2">•</span>
                    <span><strong className="text-white">500+ Companies:</strong> Comprehensive junior mining database</span>
                  </li>
                  <li className="flex items-start">
                    <span className="text-amber-500 mr-2">•</span>
                    <span><strong className="text-white">NI 43-101 Reports:</strong> Technical reports and resource estimates</span>
                  </li>
                  <li className="flex items-start">
                    <span className="text-amber-500 mr-2">•</span>
                    <span><strong className="text-white">Real-time Data:</strong> News, financings, and exploration updates</span>
                  </li>
                  <li className="flex items-start">
                    <span className="text-amber-500 mr-2">•</span>
                    <span><strong className="text-white">AI Analysis:</strong> Machine learning-powered company insights</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </section>

        {/* Coverage Section */}
        <section className="py-16 px-4">
          <div className="max-w-7xl mx-auto">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-12 text-center">
              Comprehensive Coverage
            </h2>
            <div className="grid md:grid-cols-3 gap-8">
              {/* Precious Metals */}
              <div className="bg-slate-800 p-8 rounded-lg border border-slate-700 hover:border-amber-500/50 transition-all">
                <div className="text-4xl mb-4">🥇</div>
                <h3 className="text-2xl font-semibold text-amber-400 mb-4">Precious Metals</h3>
                <ul className="space-y-2 text-slate-300">
                  <li>• Gold exploration companies</li>
                  <li>• Silver mining projects</li>
                  <li>• Platinum group metals</li>
                  <li>• TSXV & TSX listings</li>
                </ul>
              </div>

              {/* Battery Metals */}
              <div className="bg-slate-800 p-8 rounded-lg border border-slate-700 hover:border-amber-500/50 transition-all">
                <div className="text-4xl mb-4">🔋</div>
                <h3 className="text-2xl font-semibold text-amber-400 mb-4">Battery Metals</h3>
                <ul className="space-y-2 text-slate-300">
                  <li>• Lithium exploration</li>
                  <li>• Nickel projects</li>
                  <li>• Cobalt deposits</li>
                  <li>• Graphite resources</li>
                </ul>
              </div>

              {/* Critical Minerals */}
              <div className="bg-slate-800 p-8 rounded-lg border border-slate-700 hover:border-amber-500/50 transition-all">
                <div className="text-4xl mb-4">⚡</div>
                <h3 className="text-2xl font-semibold text-amber-400 mb-4">Critical Minerals</h3>
                <ul className="space-y-2 text-slate-300">
                  <li>• Copper exploration</li>
                  <li>• Rare earth elements</li>
                  <li>• Zinc & lead projects</li>
                  <li>• Strategic minerals</li>
                </ul>
              </div>
            </div>
          </div>
        </section>

        {/* Platform Features */}
        <section className="py-16 px-4 bg-slate-800/50">
          <div className="max-w-7xl mx-auto">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-12 text-center">
              Platform Features
            </h2>
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="bg-slate-900 p-6 rounded-lg border border-slate-700">
                <div className="text-3xl mb-3">📊</div>
                <h3 className="text-lg font-semibold text-white mb-2">Company Profiles</h3>
                <p className="text-sm text-slate-400">
                  Detailed profiles with management, projects, financials, and historical data
                </p>
              </div>
              <div className="bg-slate-900 p-6 rounded-lg border border-slate-700">
                <div className="text-3xl mb-3">📄</div>
                <h3 className="text-lg font-semibold text-white mb-2">NI 43-101 Database</h3>
                <p className="text-sm text-slate-400">
                  Access technical reports and mineral resource estimates
                </p>
              </div>
              <div className="bg-slate-900 p-6 rounded-lg border border-slate-700">
                <div className="text-3xl mb-3">💰</div>
                <h3 className="text-lg font-semibold text-white mb-2">Financing Tracker</h3>
                <p className="text-sm text-slate-400">
                  Monitor private placements, debt financings, and capital raises
                </p>
              </div>
              <div className="bg-slate-900 p-6 rounded-lg border border-slate-700">
                <div className="text-3xl mb-3">🤖</div>
                <h3 className="text-lg font-semibold text-white mb-2">AI-Powered Chat</h3>
                <p className="text-sm text-slate-400">
                  Ask questions and get instant insights about companies and projects
                </p>
              </div>
              <div className="bg-slate-900 p-6 rounded-lg border border-slate-700">
                <div className="text-3xl mb-3">📈</div>
                <h3 className="text-lg font-semibold text-white mb-2">Resource Estimates</h3>
                <p className="text-sm text-slate-400">
                  Measured, indicated, and inferred resource data
                </p>
              </div>
              <div className="bg-slate-900 p-6 rounded-lg border border-slate-700">
                <div className="text-3xl mb-3">📰</div>
                <h3 className="text-lg font-semibold text-white mb-2">News Aggregation</h3>
                <p className="text-sm text-slate-400">
                  Real-time news releases and press announcements
                </p>
              </div>
              <div className="bg-slate-900 p-6 rounded-lg border border-slate-700">
                <div className="text-3xl mb-3">🗺️</div>
                <h3 className="text-lg font-semibold text-white mb-2">Property Database</h3>
                <p className="text-sm text-slate-400">
                  Explore mining properties with location data and project details
                </p>
              </div>
              <div className="bg-slate-900 p-6 rounded-lg border border-slate-700">
                <div className="text-3xl mb-3">📚</div>
                <h3 className="text-lg font-semibold text-white mb-2">Mining Glossary</h3>
                <p className="text-sm text-slate-400">
                  Comprehensive glossary of 60+ mining industry terms
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Technology Section */}
        <section className="py-16 px-4">
          <div className="max-w-6xl mx-auto">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-8 text-center">
              Powered by Advanced Technology
            </h2>
            <div className="bg-gradient-to-br from-slate-800 to-slate-900 p-8 rounded-lg border border-slate-700">
              <div className="grid md:grid-cols-2 gap-8">
                <div>
                  <h3 className="text-xl font-semibold text-amber-400 mb-4">AI & Machine Learning</h3>
                  <p className="text-slate-300 mb-4">
                    Our platform leverages cutting-edge AI to analyze thousands of documents, extract key data points,
                    and provide intelligent insights on junior mining companies.
                  </p>
                  <ul className="space-y-2 text-slate-400 text-sm">
                    <li>• Natural language processing for document analysis</li>
                    <li>• Automated NI 43-101 report extraction</li>
                    <li>• Intelligent company matching and categorization</li>
                  </ul>
                </div>
                <div>
                  <h3 className="text-xl font-semibold text-amber-400 mb-4">Real-Time Data Pipeline</h3>
                  <p className="text-slate-300 mb-4">
                    Automated data collection and processing ensures you have access to the most current information
                    on junior mining companies and their exploration activities.
                  </p>
                  <ul className="space-y-2 text-slate-400 text-sm">
                    <li>• Daily news release monitoring</li>
                    <li>• Automatic financing detection and alerts</li>
                    <li>• Real-time precious metals pricing</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Standards Section */}
        <section className="py-16 px-4 bg-slate-800/50">
          <div className="max-w-6xl mx-auto">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-8 text-center">
              Industry Standards
            </h2>
            <div className="bg-slate-900 p-8 rounded-lg border border-slate-700">
              <div className="flex items-start gap-4">
                <div className="text-5xl">📋</div>
                <div>
                  <h3 className="text-2xl font-semibold text-amber-400 mb-4">NI 43-101 Compliance</h3>
                  <p className="text-slate-300 mb-4">
                    National Instrument 43-101 is the Canadian standard for disclosure of scientific and technical
                    information about mineral projects. All resource estimates and technical reports in our database
                    adhere to these rigorous standards.
                  </p>
                  <p className="text-slate-400 text-sm">
                    NI 43-101 requires that all public disclosures of mineral resources and reserves be prepared
                    or supervised by a Qualified Person and follow strict reporting standards for transparency and accuracy.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="py-16 px-4">
          <div className="max-w-4xl mx-auto text-center">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-6">
              Start Exploring Junior Mining Companies
            </h2>
            <p className="text-xl text-slate-300 mb-8">
              Access comprehensive data on 500+ companies exploring gold, silver, lithium, copper, and critical minerals
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link
                href="/companies"
                className="inline-flex items-center justify-center px-8 py-4 bg-gradient-to-r from-amber-500 to-amber-600 text-slate-900 font-semibold rounded-lg hover:from-amber-600 hover:to-amber-700 transition-all shadow-lg hover:shadow-amber-500/50"
              >
                Browse Companies
                <svg className="w-5 h-5 ml-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </Link>
              <Link
                href="/glossary"
                className="inline-flex items-center justify-center px-8 py-4 bg-slate-800 text-white font-semibold rounded-lg hover:bg-slate-700 transition-all border border-slate-700"
              >
                View Glossary
              </Link>
            </div>
          </div>
        </section>

        {/* Contact Section */}
        <section className="py-12 px-4 bg-slate-800/50 border-t border-slate-700">
          <div className="max-w-4xl mx-auto text-center">
            <h3 className="text-2xl font-semibold text-white mb-4">Questions or Feedback?</h3>
            <p className="text-slate-300 mb-6">
              We're constantly improving our platform. Contact us with questions, suggestions, or partnership inquiries.
            </p>
            <a
              href="mailto:info@juniorminingintelligence.com"
              className="text-amber-400 hover:text-amber-300 font-medium"
            >
              info@juniorminingintelligence.com
            </a>
          </div>
        </section>
      </div>
    </>
  );
}
