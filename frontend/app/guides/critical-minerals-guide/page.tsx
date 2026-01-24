import type { Metadata } from 'next';
import Link from 'next/link';

export const metadata: Metadata = {
  title: 'Critical Minerals Investment Guide 2026 | Lithium, Copper, Rare Earths | Junior Mining Intelligence',
  description: 'Comprehensive guide to investing in critical minerals including lithium, copper, rare earth elements, nickel, cobalt, graphite, and uranium. Learn about supply chains, demand drivers, and top junior mining companies.',
  keywords: [
    'critical minerals investment',
    'lithium mining stocks',
    'copper mining companies',
    'rare earth elements',
    'battery metals',
    'EV metals',
    'nickel mining',
    'cobalt stocks',
    'graphite mining',
    'uranium stocks',
    'junior mining critical minerals'
  ],
  openGraph: {
    title: 'Critical Minerals Investment Guide 2026',
    description: 'Learn how to invest in critical minerals powering the energy transition.',
    type: 'article',
    url: 'https://juniorminingintelligence.com/guides/critical-minerals-guide',
  },
  alternates: {
    canonical: 'https://juniorminingintelligence.com/guides/critical-minerals-guide',
  },
};

const articleSchema = {
  '@context': 'https://schema.org',
  '@type': 'Article',
  headline: 'Critical Minerals Investment Guide 2026',
  description: 'Comprehensive guide to investing in critical minerals for the energy transition.',
  author: {
    '@type': 'Organization',
    name: 'Junior Mining Intelligence',
    url: 'https://juniorminingintelligence.com'
  },
  publisher: {
    '@type': 'Organization',
    name: 'Junior Mining Intelligence',
  },
  datePublished: '2026-01-16',
  dateModified: '2026-01-16',
};

const faqSchema = {
  '@context': 'https://schema.org',
  '@type': 'FAQPage',
  mainEntity: [
    {
      '@type': 'Question',
      name: 'What are critical minerals?',
      acceptedAnswer: {
        '@type': 'Answer',
        text: 'Critical minerals are raw materials essential for economic and national security that face supply chain risks. They include lithium, cobalt, rare earth elements, graphite, copper, nickel, and uranium.'
      }
    },
    {
      '@type': 'Question',
      name: 'Why invest in critical minerals now?',
      acceptedAnswer: {
        '@type': 'Answer',
        text: 'The energy transition requires massive quantities of critical minerals, while supply chains remain concentrated in a few countries. Government support, growing demand, and supply constraints create a favorable investment environment.'
      }
    }
  ]
};

export default function CriticalMineralsGuide() {
  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(articleSchema) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(faqSchema) }}
      />
      <div className="min-h-screen bg-slate-900">
        <header className="bg-slate-800/50 border-b border-slate-700">
          <div className="max-w-4xl mx-auto px-4 py-8">
            <Link href="/guides" className="text-gold-400 hover:text-gold-300 mb-4 inline-block">
              ← Back to Guides
            </Link>
            <div className="flex items-center gap-3 mb-4">
              <span className="bg-emerald-500/20 text-emerald-400 text-sm px-3 py-1 rounded-full">
                Critical Minerals
              </span>
              <span className="text-slate-400 text-sm">18 min read</span>
              <span className="text-slate-400 text-sm">Updated January 2026</span>
            </div>
            <h1 className="text-4xl md:text-5xl font-bold text-white leading-tight">
              Critical Minerals Investment Guide 2026
            </h1>
            <p className="text-xl text-slate-300 mt-4 leading-relaxed">
              Everything you need to know about investing in the minerals powering the energy transition—lithium, copper, rare earths, nickel, cobalt, graphite, and uranium.
            </p>
          </div>
        </header>

        <nav className="bg-slate-800/30 border-b border-slate-700/50">
          <div className="max-w-4xl mx-auto px-4 py-6">
            <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4">Table of Contents</h2>
            <div className="grid md:grid-cols-2 gap-2">
              {[
                { id: 'what-are-critical-minerals', title: '1. What Are Critical Minerals?' },
                { id: 'why-invest', title: '2. Why Invest in Critical Minerals?' },
                { id: 'lithium', title: '3. Lithium' },
                { id: 'copper', title: '4. Copper' },
                { id: 'rare-earths', title: '5. Rare Earth Elements' },
                { id: 'nickel-cobalt', title: '6. Nickel & Cobalt' },
                { id: 'graphite', title: '7. Graphite' },
                { id: 'uranium', title: '8. Uranium' },
                { id: 'strategies', title: '9. Investment Strategies' },
                { id: 'faq', title: '10. FAQ' },
              ].map((item) => (
                <a
                  key={item.id}
                  href={`#${item.id}`}
                  className="text-slate-300 hover:text-gold-400 text-sm py-1 transition-colors"
                >
                  {item.title}
                </a>
              ))}
            </div>
          </div>
        </nav>

        <main className="max-w-4xl mx-auto px-4 py-12">
          <article className="prose prose-invert prose-lg max-w-none">
            
            <section id="what-are-critical-minerals" className="mb-16">
              <h2 className="text-3xl font-bold text-gold-400 mb-6">1. What Are Critical Minerals?</h2>
              <p className="text-slate-300 leading-relaxed mb-6">
                Critical minerals are raw materials deemed essential for economic prosperity, national security, and the energy transition. 
                These minerals face supply chain vulnerabilities due to geographic concentration, limited substitutes, and growing demand.
              </p>
              <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6 mb-6">
                <h3 className="text-xl font-semibold text-white mb-4">Key Critical Minerals for Investors</h3>
                <div className="grid md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <span className="text-emerald-400">●</span>
                      <span className="text-slate-300"><strong className="text-white">Lithium</strong> - EV batteries, energy storage</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-orange-400">●</span>
                      <span className="text-slate-300"><strong className="text-white">Copper</strong> - Electrification, EVs, renewables</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-purple-400">●</span>
                      <span className="text-slate-300"><strong className="text-white">Rare Earths</strong> - Magnets, defense, electronics</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-blue-400">●</span>
                      <span className="text-slate-300"><strong className="text-white">Nickel</strong> - Battery cathodes, stainless steel</span>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <span className="text-pink-400">●</span>
                      <span className="text-slate-300"><strong className="text-white">Cobalt</strong> - Battery stability, superalloys</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-gray-400">●</span>
                      <span className="text-slate-300"><strong className="text-white">Graphite</strong> - Battery anodes, lubricants</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-yellow-400">●</span>
                      <span className="text-slate-300"><strong className="text-white">Uranium</strong> - Nuclear power generation</span>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            <section id="why-invest" className="mb-16">
              <h2 className="text-3xl font-bold text-gold-400 mb-6">2. Why Invest in Critical Minerals?</h2>
              <div className="space-y-6">
                <div className="bg-gradient-to-r from-emerald-500/10 to-blue-500/10 border border-emerald-500/30 rounded-xl p-6">
                  <h3 className="text-xl font-semibold text-white mb-4">The Energy Transition Thesis</h3>
                  <p className="text-slate-300 mb-4">
                    The global shift from fossil fuels to clean energy requires unprecedented quantities of critical minerals. 
                    An electric vehicle uses 6x more minerals than a conventional car. A wind turbine requires 9x more minerals than a gas plant.
                  </p>
                  <div className="grid md:grid-cols-3 gap-4 mt-4">
                    <div className="text-center">
                      <div className="text-3xl font-bold text-emerald-400">40x</div>
                      <div className="text-sm text-slate-400">Lithium demand growth by 2040</div>
                    </div>
                    <div className="text-center">
                      <div className="text-3xl font-bold text-orange-400">25x</div>
                      <div className="text-sm text-slate-400">Graphite demand growth by 2040</div>
                    </div>
                    <div className="text-center">
                      <div className="text-3xl font-bold text-blue-400">20x</div>
                      <div className="text-sm text-slate-400">Cobalt demand growth by 2040</div>
                    </div>
                  </div>
                </div>

                <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
                  <h3 className="text-xl font-semibold text-white mb-4">Supply Chain Vulnerabilities</h3>
                  <p className="text-slate-300 mb-4">
                    Critical mineral supply chains are dangerously concentrated. China dominates processing of nearly all battery materials, 
                    creating strategic risks that governments are racing to address.
                  </p>
                  <ul className="text-slate-300 space-y-2">
                    <li>• <strong className="text-white">China controls 60-80%</strong> of rare earth processing</li>
                    <li>• <strong className="text-white">DRC produces 70%</strong> of global cobalt</li>
                    <li>• <strong className="text-white">Australia and Chile</strong> dominate lithium mining</li>
                    <li>• <strong className="text-white">Government incentives</strong> driving domestic supply development</li>
                  </ul>
                </div>
              </div>
            </section>

            <section id="lithium" className="mb-16">
              <h2 className="text-3xl font-bold text-gold-400 mb-6">3. Lithium: The White Gold</h2>
              <p className="text-slate-300 leading-relaxed mb-6">
                Lithium is the cornerstone of the EV revolution. Every electric vehicle battery contains 8-12kg of lithium, 
                and demand is expected to increase 40-fold by 2040 to meet climate targets.
              </p>

              <div className="grid md:grid-cols-2 gap-6 mb-6">
                <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
                  <h3 className="text-lg font-semibold text-white mb-3">Hard Rock Lithium</h3>
                  <ul className="text-slate-300 space-y-2">
                    <li>• Mined from spodumene pegmatites</li>
                    <li>• Higher capital costs, faster production</li>
                    <li>• Major deposits in Australia, Canada</li>
                    <li>• Produces spodumene concentrate</li>
                  </ul>
                </div>
                <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
                  <h3 className="text-lg font-semibold text-white mb-3">Brine Lithium</h3>
                  <ul className="text-slate-300 space-y-2">
                    <li>• Extracted from salt flats</li>
                    <li>• Lower costs, longer development</li>
                    <li>• Chile, Argentina Lithium Triangle</li>
                    <li>• Direct lithium extraction emerging</li>
                  </ul>
                </div>
              </div>

              <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-xl p-6">
                <h3 className="text-lg font-semibold text-white mb-3">Investment Considerations</h3>
                <p className="text-slate-300">
                  Junior lithium companies offer significant leverage to lithium prices. Focus on projects with 
                  NI 43-101 resources, favorable metallurgy, and proximity to battery manufacturing hubs.
                </p>
              </div>
            </section>

            <section id="copper" className="mb-16">
              <h2 className="text-3xl font-bold text-gold-400 mb-6">4. Copper: The Metal of Electrification</h2>
              <p className="text-slate-300 leading-relaxed mb-6">
                Copper is essential for electrification—EVs use 4x more copper than conventional vehicles, 
                and renewable energy systems require massive copper wiring. Analysts project a 50% supply gap by 2035.
              </p>

              <div className="bg-gradient-to-r from-orange-500/10 to-red-500/10 border border-orange-500/30 rounded-xl p-6 mb-6">
                <h3 className="text-xl font-semibold text-white mb-4">The Copper Supply Crisis</h3>
                <div className="grid md:grid-cols-2 gap-6">
                  <div>
                    <h4 className="text-orange-400 font-semibold mb-2">Demand Drivers</h4>
                    <ul className="text-slate-300 space-y-2 text-sm">
                      <li>• EVs: 80kg copper per vehicle</li>
                      <li>• Solar: 5 tons per MW</li>
                      <li>• Wind: 4+ tons per MW</li>
                      <li>• Grid upgrades worldwide</li>
                    </ul>
                  </div>
                  <div>
                    <h4 className="text-orange-400 font-semibold mb-2">Supply Challenges</h4>
                    <ul className="text-slate-300 space-y-2 text-sm">
                      <li>• Declining ore grades at major mines</li>
                      <li>• 15+ years to develop new mines</li>
                      <li>• Limited new discoveries</li>
                      <li>• ESG and permitting challenges</li>
                    </ul>
                  </div>
                </div>
              </div>

              <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
                <h3 className="text-lg font-semibold text-white mb-3">Junior Copper Opportunity</h3>
                <p className="text-slate-300">
                  Major producers need to replace depleting reserves, creating M&A opportunities for juniors with quality deposits. 
                  Look for porphyry copper projects in stable jurisdictions with scale potential.
                </p>
              </div>
            </section>

            <section id="rare-earths" className="mb-16">
              <h2 className="text-3xl font-bold text-gold-400 mb-6">5. Rare Earth Elements: Strategic Metals</h2>
              <p className="text-slate-300 leading-relaxed mb-6">
                Rare earth elements are critical for permanent magnets used in EVs, wind turbines, and defense applications. 
                China controls 60% of mining and 90% of processing, creating significant supply chain risks.
              </p>

              <div className="bg-purple-500/10 border border-purple-500/30 rounded-xl p-6 mb-6">
                <h3 className="text-xl font-semibold text-white mb-4">Key Rare Earths for Investors</h3>
                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <h4 className="text-purple-400 font-semibold mb-2">Magnet REEs (Most Valuable)</h4>
                    <ul className="text-slate-300 space-y-1 text-sm">
                      <li>• Neodymium (Nd) - strongest permanent magnets</li>
                      <li>• Praseodymium (Pr) - magnet alloys</li>
                      <li>• Dysprosium (Dy) - high-temp magnets</li>
                      <li>• Terbium (Tb) - magnet stabilizer</li>
                    </ul>
                  </div>
                  <div>
                    <h4 className="text-purple-400 font-semibold mb-2">Heavy REEs (Scarcer)</h4>
                    <ul className="text-slate-300 space-y-1 text-sm">
                      <li>• Command premium prices</li>
                      <li>• Limited non-Chinese supply</li>
                      <li>• Critical for defense applications</li>
                      <li>• Ionic clay deposits in development</li>
                    </ul>
                  </div>
                </div>
              </div>

              <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
                <h3 className="text-lg font-semibold text-white mb-3">Investment Thesis</h3>
                <p className="text-slate-300">
                  Western governments are prioritizing rare earth supply chain security with billions in incentives. 
                  Junior REE companies with permitted projects and offtake agreements are positioned for revaluation.
                </p>
              </div>
            </section>

            <section id="nickel-cobalt" className="mb-16">
              <h2 className="text-3xl font-bold text-gold-400 mb-6">6. Nickel & Cobalt: Battery Metals</h2>
              
              <div className="grid md:grid-cols-2 gap-6 mb-6">
                <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
                  <h3 className="text-xl font-semibold text-white mb-4">Nickel</h3>
                  <p className="text-slate-300 text-sm mb-4">
                    Nickel enables high energy density in EV batteries. Class 1 nickel (greater than 99.8% purity) is required 
                    for battery applications, distinct from lower-grade nickel used in stainless steel.
                  </p>
                  <ul className="text-slate-300 space-y-2 text-sm">
                    <li>• <strong className="text-white">Indonesia dominates</strong> new supply</li>
                    <li>• <strong className="text-white">Sulfide deposits</strong> preferred for batteries</li>
                    <li>• <strong className="text-white">ESG concerns</strong> with Indonesian laterites</li>
                  </ul>
                </div>
                <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
                  <h3 className="text-xl font-semibold text-white mb-4">Cobalt</h3>
                  <p className="text-slate-300 text-sm mb-4">
                    Cobalt stabilizes battery cathode structures, improving safety and longevity. Demand is growing 
                    despite efforts to reduce cobalt content in batteries.
                  </p>
                  <ul className="text-slate-300 space-y-2 text-sm">
                    <li>• <strong className="text-white">DRC produces 70%</strong> of global supply</li>
                    <li>• <strong className="text-white">Artisanal mining concerns</strong> drive ESG focus</li>
                    <li>• <strong className="text-white">Premium for ethically-sourced</strong> material</li>
                  </ul>
                </div>
              </div>
            </section>

            <section id="graphite" className="mb-16">
              <h2 className="text-3xl font-bold text-gold-400 mb-6">7. Graphite: The Forgotten Battery Metal</h2>
              <p className="text-slate-300 leading-relaxed mb-6">
                Graphite is the largest component by weight in lithium-ion batteries, comprising 100% of the anode. 
                An EV battery contains 50-100kg of graphite—more than lithium, nickel, or cobalt combined.
              </p>

              <div className="grid md:grid-cols-2 gap-6 mb-6">
                <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
                  <h3 className="text-lg font-semibold text-white mb-3">Natural Graphite</h3>
                  <ul className="text-slate-300 space-y-2">
                    <li>• Mined from flake graphite deposits</li>
                    <li>• China produces 65% of global supply</li>
                    <li>• Lower carbon footprint than synthetic</li>
                    <li>• Growing projects in Canada, Australia, Africa</li>
                  </ul>
                </div>
                <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
                  <h3 className="text-lg font-semibold text-white mb-3">Synthetic Graphite</h3>
                  <ul className="text-slate-300 space-y-2">
                    <li>• Produced from petroleum coke</li>
                    <li>• Higher purity and consistency</li>
                    <li>• Energy-intensive production</li>
                    <li>• Higher cost than natural graphite</li>
                  </ul>
                </div>
              </div>

              <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-xl p-6">
                <h3 className="text-lg font-semibold text-white mb-3">Investment Opportunity</h3>
                <p className="text-slate-300">
                  China export restrictions have accelerated interest in non-Chinese projects. The US, Canada, and EU 
                  are prioritizing domestic graphite production with incentives and offtake support.
                </p>
              </div>
            </section>

            <section id="uranium" className="mb-16">
              <h2 className="text-3xl font-bold text-gold-400 mb-6">8. Uranium: Nuclear Renaissance</h2>
              <p className="text-slate-300 leading-relaxed mb-6">
                Nuclear power is experiencing a global resurgence as countries recognize it as essential for 
                decarbonization. Uranium demand is set to increase significantly as new reactors come online.
              </p>

              <div className="bg-gradient-to-r from-yellow-500/10 to-green-500/10 border border-yellow-500/30 rounded-xl p-6 mb-6">
                <h3 className="text-xl font-semibold text-white mb-4">Why Uranium Now?</h3>
                <div className="grid md:grid-cols-2 gap-6">
                  <div>
                    <h4 className="text-gold-400 font-semibold mb-2">Demand Drivers</h4>
                    <ul className="text-slate-300 space-y-2 text-sm">
                      <li>• <strong className="text-white">60+ reactors</strong> under construction globally</li>
                      <li>• <strong className="text-white">China plans 150+ new reactors</strong> by 2035</li>
                      <li>• <strong className="text-white">Life extensions</strong> for existing fleet</li>
                      <li>• <strong className="text-white">SMR development</strong> gaining traction</li>
                    </ul>
                  </div>
                  <div>
                    <h4 className="text-gold-400 font-semibold mb-2">Supply Constraints</h4>
                    <ul className="text-slate-300 space-y-2 text-sm">
                      <li>• Production deficit for 10+ years</li>
                      <li>• Secondary supplies depleting</li>
                      <li>• Long lead times for new mines</li>
                      <li>• Geopolitical risks in Kazakhstan, Russia</li>
                    </ul>
                  </div>
                </div>
              </div>

              <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
                <h3 className="text-lg font-semibold text-white mb-3">Junior Uranium Investment Thesis</h3>
                <p className="text-slate-300 mb-4">
                  Junior uranium companies offer significant leverage to uranium price movements. Key investment criteria:
                </p>
                <ul className="text-slate-300 space-y-2">
                  <li>• <strong className="text-white">Permitted projects</strong> in stable jurisdictions</li>
                  <li>• <strong className="text-white">Low capital intensity</strong> ISR projects preferred</li>
                  <li>• <strong className="text-white">Proximity to infrastructure</strong> for near-term production</li>
                  <li>• <strong className="text-white">Management with cycle experience</strong></li>
                </ul>
              </div>
            </section>

            <section id="strategies" className="mb-16">
              <h2 className="text-3xl font-bold text-gold-400 mb-6">9. Investment Strategies for Critical Minerals</h2>
              
              <div className="space-y-6">
                <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
                  <h3 className="text-xl font-semibold text-white mb-4">Portfolio Construction</h3>
                  <div className="grid md:grid-cols-3 gap-4">
                    <div className="bg-slate-900/50 rounded-lg p-4">
                      <h4 className="text-gold-400 font-semibold mb-2">Conservative (30%)</h4>
                      <ul className="text-slate-300 text-sm space-y-1">
                        <li>• Large-cap producers</li>
                        <li>• Diversified miners</li>
                        <li>• Royalty companies</li>
                      </ul>
                    </div>
                    <div className="bg-slate-900/50 rounded-lg p-4">
                      <h4 className="text-gold-400 font-semibold mb-2">Growth (50%)</h4>
                      <ul className="text-slate-300 text-sm space-y-1">
                        <li>• Development-stage juniors</li>
                        <li>• Near-production assets</li>
                        <li>• Strategic acquisitions</li>
                      </ul>
                    </div>
                    <div className="bg-slate-900/50 rounded-lg p-4">
                      <h4 className="text-gold-400 font-semibold mb-2">Speculative (20%)</h4>
                      <ul className="text-slate-300 text-sm space-y-1">
                        <li>• Early-stage explorers</li>
                        <li>• Discovery potential</li>
                        <li>• Emerging commodities</li>
                      </ul>
                    </div>
                  </div>
                </div>

                <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
                  <h3 className="text-xl font-semibold text-white mb-4">Due Diligence Checklist</h3>
                  <div className="grid md:grid-cols-2 gap-6">
                    <div>
                      <h4 className="text-gold-400 font-semibold mb-2">Technical Factors</h4>
                      <ul className="text-slate-300 space-y-2 text-sm">
                        <li>✓ Resource quality and grade</li>
                        <li>✓ Metallurgical recoveries</li>
                        <li>✓ Infrastructure access</li>
                        <li>✓ Environmental considerations</li>
                        <li>✓ NI 43-101 compliant resources</li>
                      </ul>
                    </div>
                    <div>
                      <h4 className="text-gold-400 font-semibold mb-2">Financial Factors</h4>
                      <ul className="text-slate-300 space-y-2 text-sm">
                        <li>✓ Capital requirements vs. cash position</li>
                        <li>✓ Share structure and dilution risk</li>
                        <li>✓ Management track record</li>
                        <li>✓ Insider ownership</li>
                        <li>✓ Strategic partnerships/offtakes</li>
                      </ul>
                    </div>
                  </div>
                </div>

                <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-6">
                  <h3 className="text-lg font-semibold text-white mb-3">Risk Management</h3>
                  <p className="text-slate-300 mb-4">
                    Critical mineral investments carry unique risks that require active management:
                  </p>
                  <ul className="text-slate-300 space-y-2">
                    <li>• <strong className="text-white">Commodity price volatility</strong> - Consider averaging into positions</li>
                    <li>• <strong className="text-white">Technology disruption</strong> - Diversify across multiple minerals</li>
                    <li>• <strong className="text-white">Geopolitical risk</strong> - Favor stable jurisdictions</li>
                    <li>• <strong className="text-white">Execution risk</strong> - Focus on experienced management teams</li>
                  </ul>
                </div>
              </div>
            </section>

            <section id="faq" className="mb-16">
              <h2 className="text-3xl font-bold text-gold-400 mb-6">10. Frequently Asked Questions</h2>
              
              <div className="space-y-4">
                <details className="group bg-slate-800/50 border border-slate-700 rounded-xl">
                  <summary className="flex justify-between items-center cursor-pointer p-6">
                    <span className="text-white font-semibold">What are critical minerals?</span>
                    <span className="text-gold-400 group-open:rotate-180 transition-transform">▼</span>
                  </summary>
                  <div className="px-6 pb-6 text-slate-300">
                    Critical minerals are raw materials essential for economic and national security that face 
                    supply chain risks. They include lithium, cobalt, rare earth elements, graphite, copper, 
                    nickel, and uranium—materials vital for EVs, renewable energy, defense, and technology.
                  </div>
                </details>

                <details className="group bg-slate-800/50 border border-slate-700 rounded-xl">
                  <summary className="flex justify-between items-center cursor-pointer p-6">
                    <span className="text-white font-semibold">Why invest in critical minerals now?</span>
                    <span className="text-gold-400 group-open:rotate-180 transition-transform">▼</span>
                  </summary>
                  <div className="px-6 pb-6 text-slate-300">
                    The energy transition requires massive quantities of critical minerals, while supply chains 
                    remain concentrated in a few countries. Government support, growing demand, and supply 
                    constraints create a favorable investment environment for the next decade.
                  </div>
                </details>

                <details className="group bg-slate-800/50 border border-slate-700 rounded-xl">
                  <summary className="flex justify-between items-center cursor-pointer p-6">
                    <span className="text-white font-semibold">What is the best critical mineral to invest in?</span>
                    <span className="text-gold-400 group-open:rotate-180 transition-transform">▼</span>
                  </summary>
                  <div className="px-6 pb-6 text-slate-300">
                    There is no single best mineral—it depends on your investment thesis and risk tolerance. 
                    Copper offers stability with long-term growth. Lithium has the most direct EV exposure. 
                    Uranium benefits from nuclear renaissance. Diversification across multiple minerals reduces risk.
                  </div>
                </details>

                <details className="group bg-slate-800/50 border border-slate-700 rounded-xl">
                  <summary className="flex justify-between items-center cursor-pointer p-6">
                    <span className="text-white font-semibold">How do I evaluate junior mining companies?</span>
                    <span className="text-gold-400 group-open:rotate-180 transition-transform">▼</span>
                  </summary>
                  <div className="px-6 pb-6 text-slate-300">
                    Focus on: (1) Quality of the deposit—grade, size, metallurgy; (2) Management track record 
                    and insider ownership; (3) Jurisdiction and permitting status; (4) Financial health and 
                    funding runway; (5) Path to production or acquisition value.
                  </div>
                </details>

                <details className="group bg-slate-800/50 border border-slate-700 rounded-xl">
                  <summary className="flex justify-between items-center cursor-pointer p-6">
                    <span className="text-white font-semibold">What are the main risks of critical mineral investing?</span>
                    <span className="text-gold-400 group-open:rotate-180 transition-transform">▼</span>
                  </summary>
                  <div className="px-6 pb-6 text-slate-300">
                    Key risks include: commodity price volatility, technology changes reducing demand for specific 
                    minerals, geopolitical disruptions, permitting delays, capital requirements, and dilution. 
                    Junior miners carry additional risks of execution, financing, and project development.
                  </div>
                </details>

                <details className="group bg-slate-800/50 border border-slate-700 rounded-xl">
                  <summary className="flex justify-between items-center cursor-pointer p-6">
                    <span className="text-white font-semibold">Should I invest in producers or explorers?</span>
                    <span className="text-gold-400 group-open:rotate-180 transition-transform">▼</span>
                  </summary>
                  <div className="px-6 pb-6 text-slate-300">
                    A balanced approach works best. Producers offer cash flow and lower risk but limited upside. 
                    Developers and near-production companies offer revaluation potential with moderate risk. 
                    Early explorers offer highest returns but also highest risk of capital loss.
                  </div>
                </details>
              </div>
            </section>

            {/* CTA Section */}
            <section className="mb-16">
              <div className="bg-gradient-to-r from-gold-400/20 to-amber-500/20 border border-gold-400/50 rounded-2xl p-8 text-center">
                <h2 className="text-2xl font-bold text-white mb-4">Start Researching Critical Mineral Companies</h2>
                <p className="text-slate-300 mb-6 max-w-2xl mx-auto">
                  Use our comprehensive database to research and compare critical mineral companies. 
                  Access detailed profiles, technical reports, and market data.
                </p>
                <div className="flex flex-wrap gap-4 justify-center">
                  <a 
                    href="/companies?commodity=lithium" 
                    className="px-6 py-3 bg-gold-400 text-slate-900 font-semibold rounded-lg hover:bg-gold-300 transition-colors"
                  >
                    Explore Lithium Companies
                  </a>
                  <a 
                    href="/companies?commodity=copper" 
                    className="px-6 py-3 border border-gold-400 text-gold-400 font-semibold rounded-lg hover:bg-gold-400/10 transition-colors"
                  >
                    Explore Copper Companies
                  </a>
                </div>
              </div>
            </section>

            {/* Disclaimer */}
            <section className="text-sm text-slate-500 border-t border-slate-800 pt-8">
              <p className="mb-4">
                <strong>Disclaimer:</strong> This guide is for educational purposes only and does not constitute 
                investment advice. Critical mineral investments carry significant risks including loss of capital. 
                Always conduct your own research and consult with qualified financial advisors before making 
                investment decisions.
              </p>
              <p>
                Last updated: January 2026
              </p>
            </section>

          </article>
        </main>
      </div>
    </>
  );
}
