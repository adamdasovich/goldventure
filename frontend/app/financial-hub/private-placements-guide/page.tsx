'use client';

import { useRouter } from 'next/navigation';
import {
  ArrowLeft,
  Briefcase,
  CheckCircle,
  AlertCircle,
  Clock,
  Shield,
  DollarSign,
  Users,
  Scale,
  TrendingUp,
  Building,
  FileText,
  Percent
} from 'lucide-react';
import { Button } from '@/components/ui/Button';
import LogoMono from '@/components/LogoMono';

export default function PrivatePlacementsGuide() {
  const router = useRouter();

  const sections = [
    {
      id: 'what-is',
      title: 'What is a Private Placement?',
      icon: Briefcase,
      content: `A private placement is a method of raising capital by selling securities directly to a select group of investors rather than through a public offering on a stock exchange. In Canada, private placements are exempt from the full prospectus requirements that apply to public offerings.

For junior mining companies, private placements are the primary method of raising capital to fund exploration, development, and operations. These offerings allow companies to raise money quickly and with less regulatory burden than public offerings, while providing investors the opportunity to acquire securities at favorable terms.`
    },
    {
      id: 'how-it-works',
      title: 'How Private Placements Work',
      icon: Clock,
      content: null,
      steps: [
        {
          number: 1,
          title: 'Company Announces Offering',
          description: 'The company issues a press release announcing the private placement, including the type of securities offered, price, and intended use of proceeds.'
        },
        {
          number: 2,
          title: 'Investor Qualification',
          description: 'Investors must qualify under an exemption (typically as accredited investors) to participate in the offering.'
        },
        {
          number: 3,
          title: 'Subscription Process',
          description: 'Qualified investors complete subscription agreements and submit payment according to the offering terms.'
        },
        {
          number: 4,
          title: 'Regulatory Filings',
          description: 'The company files required documents with securities regulators (e.g., Form 45-106F1 in Canada).'
        },
        {
          number: 5,
          title: 'Closing',
          description: 'Once minimum subscription requirements are met, the offering closes and securities are issued to investors.'
        },
        {
          number: 6,
          title: 'Hold Period',
          description: 'Investors receive their securities subject to a statutory hold period (typically 4 months in Canada) during which they cannot resell.'
        }
      ]
    },
    {
      id: 'types',
      title: 'Types of Private Placement Securities',
      icon: FileText,
      content: null,
      types: [
        {
          name: 'Common Shares',
          description: 'Basic equity ownership in the company with voting rights and potential for capital appreciation.',
          features: ['Voting rights at shareholder meetings', 'Potential dividend payments', 'Direct exposure to share price movement']
        },
        {
          name: 'Units',
          description: 'A combination of common shares and warrants bundled together at a single price.',
          features: ['Typically includes half or full warrant coverage', 'Additional upside potential through warrants', 'Most common structure in mining placements']
        },
        {
          name: 'Flow-Through Shares',
          description: 'Shares that allow the company to transfer tax deductions from exploration expenses to investors.',
          features: ['100% tax deduction on eligible exploration expenses', 'Additional provincial tax credits may apply', 'Typically priced at a premium to common shares']
        },
        {
          name: 'Convertible Debentures',
          description: 'Debt instruments that can be converted into equity at a predetermined price.',
          features: ['Fixed interest payments', 'Option to convert to shares', 'Priority over common shareholders in bankruptcy']
        }
      ]
    },
    {
      id: 'exemptions',
      title: 'Prospectus Exemptions in Canada',
      icon: Scale,
      content: `Private placements in Canada rely on exemptions from the prospectus requirement under National Instrument 45-106. The most common exemptions include:`,
      exemptions: [
        {
          name: 'Accredited Investor Exemption',
          description: 'The most widely used exemption, allowing sales to individuals and entities meeting specific financial thresholds.',
          criteria: 'Net financial assets >$1M, income >$200K, or net assets >$5M'
        },
        {
          name: 'Minimum Amount Investment Exemption',
          description: 'Allows anyone to invest a minimum of $150,000 in a single transaction.',
          criteria: 'Minimum $150,000 investment per transaction'
        },
        {
          name: 'Family, Friends, and Business Associates',
          description: 'Permits sales to close personal connections of company directors or officers.',
          criteria: 'Must have close personal relationship with director/officer'
        },
        {
          name: 'Offering Memorandum Exemption',
          description: 'Allows sales to any investor who receives an offering memorandum, with investment limits for non-accredited investors.',
          criteria: 'Requires detailed offering memorandum document'
        }
      ]
    },
    {
      id: 'benefits',
      title: 'Benefits of Private Placements',
      icon: TrendingUp,
      content: null,
      benefitGroups: [
        {
          group: 'For Companies',
          items: [
            'Faster access to capital than public offerings',
            'Lower regulatory costs and compliance burden',
            'Ability to raise money without affecting public share price',
            'Flexibility in structuring the offering terms',
            'Access to sophisticated investors who understand the business'
          ]
        },
        {
          group: 'For Investors',
          items: [
            'Opportunity to invest at prices below market (often with warrants)',
            'Access to investment opportunities not available to the public',
            'Direct relationship with company management',
            'Warrant coverage provides additional upside potential',
            'Tax benefits with flow-through shares'
          ]
        }
      ]
    },
    {
      id: 'pricing',
      title: 'Understanding Pricing',
      icon: DollarSign,
      content: `Private placement pricing in junior mining is typically set relative to the current market price of the company's publicly traded shares:`,
      pricingDetails: [
        {
          term: 'Market Price Discount',
          description: 'Most private placements are priced at a discount to market (typically 10-25%) to compensate investors for the hold period and illiquidity risk.'
        },
        {
          term: 'TSX Venture Pricing Rules',
          description: 'The TSX Venture Exchange requires a minimum price of $0.05 and limits discounts based on market capitalization and trading history.'
        },
        {
          term: 'Warrant Strike Price',
          description: 'Warrants are typically priced at a premium to the placement price (often 25-50% higher), providing investors with leveraged upside.'
        },
        {
          term: 'Flow-Through Premium',
          description: 'Flow-through shares are priced at a premium (typically 15-30%) to compensate for the tax benefits being transferred.'
        }
      ]
    },
    {
      id: 'use-of-proceeds',
      title: 'Typical Use of Proceeds',
      icon: Building,
      content: `Junior mining companies raise capital through private placements to fund various activities. Companies must disclose the intended use of proceeds:`,
      uses: [
        {
          category: 'Exploration',
          percentage: '40-60%',
          description: 'Drilling programs, geological surveys, geophysical studies, and assay testing'
        },
        {
          category: 'Property Acquisition',
          percentage: '10-30%',
          description: 'Acquiring new mineral claims or properties, option payments'
        },
        {
          category: 'General Working Capital',
          percentage: '15-25%',
          description: 'Operating expenses, salaries, professional fees, and corporate overhead'
        },
        {
          category: 'Development',
          percentage: '0-40%',
          description: 'Pre-feasibility studies, permitting, environmental assessments (for advanced projects)'
        }
      ]
    },
    {
      id: 'risks',
      title: 'Risks to Consider',
      icon: AlertCircle,
      content: null,
      risks: [
        {
          title: 'Illiquidity',
          description: 'Securities are subject to a 4-month hold period and may have limited trading volume after'
        },
        {
          title: 'Dilution',
          description: 'Private placements increase shares outstanding, diluting existing shareholders ownership percentage'
        },
        {
          title: 'Speculative Nature',
          description: 'Junior mining is highly speculative with most exploration projects failing to become mines'
        },
        {
          title: 'Price Decline',
          description: 'Share price may fall below your purchase price before the hold period expires'
        },
        {
          title: 'Warrant Expiry',
          description: 'Warrants expire worthless if the share price never exceeds the strike price'
        },
        {
          title: 'Company Risk',
          description: 'Junior miners may run out of cash, be unable to raise more capital, or fail entirely'
        }
      ]
    },
    {
      id: 'due-diligence',
      title: 'Due Diligence Checklist',
      icon: CheckCircle,
      content: `Before investing in any private placement, consider reviewing:`,
      checklist: [
        'Management team experience and track record',
        'Property location, size, and geological potential',
        'Recent drill results and technical reports (NI 43-101)',
        'Current cash position and burn rate',
        'Existing share structure and dilution history',
        'Insider ownership and recent insider activity',
        'Use of proceeds and business plan',
        'Comparable company valuations',
        'Jurisdiction and political risk',
        'Environmental and permitting status'
      ]
    },
    {
      id: 'regulatory',
      title: 'Regulatory Framework',
      icon: Shield,
      content: `Private placements in Canada are governed by provincial securities legislation and national instruments:`,
      regulations: [
        {
          name: 'National Instrument 45-106',
          description: 'Prospectus Exemptions - defines who can participate and under what conditions'
        },
        {
          name: 'National Instrument 43-101',
          description: 'Standards for mineral project disclosure to ensure technical information is reliable'
        },
        {
          name: 'TSX/TSX-V Policies',
          description: 'Exchange-specific rules governing pricing, dilution limits, and approval requirements'
        },
        {
          name: 'Resale Restrictions',
          description: 'National Instrument 45-102 governs the 4-month hold period and resale conditions'
        }
      ]
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 via-slate-900 to-slate-800">
      {/* Navigation */}
      <nav className="glass-nav sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-24">
            <div className="flex items-center space-x-3 cursor-pointer" onClick={() => router.push('/')}>
              <LogoMono className="h-18" />
            </div>
            <div className="flex items-center space-x-4">
              <Button variant="ghost" size="sm" onClick={() => router.push('/')}>Dashboard</Button>
              <Button variant="ghost" size="sm" onClick={() => router.push('/companies')}>Companies</Button>
              <Button variant="ghost" size="sm" onClick={() => router.push('/financial-hub')}>Financial Hub</Button>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative py-16 px-4 sm:px-6 lg:px-8 overflow-hidden">
        <div className="absolute inset-0" style={{
          backgroundImage: 'radial-gradient(circle at 50% 50%, rgba(212, 161, 42, 0.1) 0%, transparent 50%)'
        }}></div>

        <div className="relative max-w-4xl mx-auto">
          {/* Back Button */}
          <button
            onClick={() => router.push('/financial-hub')}
            className="flex items-center gap-2 text-slate-400 hover:text-gold-400 transition-colors mb-8"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Financial Hub
          </button>

          {/* Header */}
          <div className="text-center mb-12">
            <div className="w-20 h-20 rounded-xl mx-auto mb-6 flex items-center justify-center"
                 style={{ backgroundColor: 'rgba(212, 175, 55, 0.2)', border: '2px solid #d4af37' }}>
              <Briefcase className="w-10 h-10" style={{ color: '#d4af37' }} />
            </div>
            <h1 className="text-4xl md:text-5xl font-bold mb-4 text-gradient-gold">
              Private Placements Guide
            </h1>
            <p className="text-xl text-slate-300 max-w-2xl mx-auto">
              Understanding how junior mining companies raise capital and how you can participate
              in private placement financings.
            </p>
          </div>
        </div>
      </section>

      {/* Main Content */}
      <section className="py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto space-y-12">
          {sections.map((section) => {
            const Icon = section.icon;

            return (
              <div
                key={section.id}
                id={section.id}
                className="p-8 backdrop-blur-sm bg-slate-800/50 border border-slate-700/50 rounded-xl"
              >
                {/* Section Header */}
                <div className="flex items-start gap-4 mb-6">
                  <div className="w-12 h-12 rounded-lg flex items-center justify-center flex-shrink-0"
                       style={{ backgroundColor: 'rgba(212, 175, 55, 0.2)', border: '2px solid #d4af37' }}>
                    <Icon className="w-6 h-6" style={{ color: '#d4af37' }} />
                  </div>
                  <h2 className="text-2xl font-bold text-white">{section.title}</h2>
                </div>

                {/* Content */}
                {section.content && (
                  <p className="text-slate-300 leading-relaxed whitespace-pre-line mb-6">
                    {section.content}
                  </p>
                )}

                {/* Process Steps */}
                {section.steps && (
                  <div className="space-y-6">
                    {section.steps.map((step) => (
                      <div key={step.number} className="flex gap-4">
                        <div className="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 font-bold text-slate-900"
                             style={{ backgroundColor: '#d4af37' }}>
                          {step.number}
                        </div>
                        <div>
                          <h4 className="font-semibold text-white mb-1">{step.title}</h4>
                          <p className="text-slate-300">{step.description}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Security Types */}
                {section.types && (
                  <div className="grid md:grid-cols-2 gap-4">
                    {section.types.map((type, idx) => (
                      <div key={idx} className="p-4 bg-slate-900/50 rounded-lg border border-slate-700">
                        <h4 className="font-semibold text-gold-400 mb-2">{type.name}</h4>
                        <p className="text-slate-300 text-sm mb-3">{type.description}</p>
                        <ul className="space-y-1">
                          {type.features.map((feature, fidx) => (
                            <li key={fidx} className="flex gap-2 text-sm text-slate-400">
                              <CheckCircle className="w-4 h-4 text-green-400 flex-shrink-0 mt-0.5" />
                              {feature}
                            </li>
                          ))}
                        </ul>
                      </div>
                    ))}
                  </div>
                )}

                {/* Exemptions */}
                {section.exemptions && (
                  <div className="space-y-4">
                    {section.exemptions.map((exemption, idx) => (
                      <div key={idx} className="p-4 bg-slate-900/50 rounded-lg border border-slate-700">
                        <h4 className="font-semibold text-white mb-1">{exemption.name}</h4>
                        <p className="text-slate-300 text-sm mb-2">{exemption.description}</p>
                        <p className="text-xs text-gold-400">{exemption.criteria}</p>
                      </div>
                    ))}
                  </div>
                )}

                {/* Benefit Groups */}
                {section.benefitGroups && (
                  <div className="grid md:grid-cols-2 gap-6">
                    {section.benefitGroups.map((group, idx) => (
                      <div key={idx}>
                        <h4 className="font-semibold text-gold-400 mb-3">{group.group}</h4>
                        <ul className="space-y-2">
                          {group.items.map((item, iidx) => (
                            <li key={iidx} className="flex gap-2 text-slate-300 text-sm">
                              <CheckCircle className="w-4 h-4 text-green-400 flex-shrink-0 mt-0.5" />
                              {item}
                            </li>
                          ))}
                        </ul>
                      </div>
                    ))}
                  </div>
                )}

                {/* Pricing Details */}
                {section.pricingDetails && (
                  <div className="space-y-4">
                    {section.pricingDetails.map((detail, idx) => (
                      <div key={idx} className="flex gap-4">
                        <DollarSign className="w-5 h-5 text-gold-400 flex-shrink-0 mt-1" />
                        <div>
                          <span className="font-semibold text-white">{detail.term}:</span>
                          <span className="text-slate-300 ml-2">{detail.description}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Use of Proceeds */}
                {section.uses && (
                  <div className="space-y-4">
                    {section.uses.map((use, idx) => (
                      <div key={idx} className="p-4 bg-slate-900/50 rounded-lg border border-slate-700">
                        <div className="flex justify-between items-center mb-2">
                          <h4 className="font-semibold text-white">{use.category}</h4>
                          <span className="text-gold-400 font-mono">{use.percentage}</span>
                        </div>
                        <p className="text-slate-400 text-sm">{use.description}</p>
                      </div>
                    ))}
                  </div>
                )}

                {/* Risks */}
                {section.risks && (
                  <div className="space-y-4">
                    {section.risks.map((risk, idx) => (
                      <div key={idx} className="p-4 bg-red-500/10 border border-red-500/30 rounded-lg">
                        <h4 className="font-semibold text-red-400 mb-1">{risk.title}</h4>
                        <p className="text-slate-300 text-sm">{risk.description}</p>
                      </div>
                    ))}
                  </div>
                )}

                {/* Checklist */}
                {section.checklist && (
                  <div className="grid md:grid-cols-2 gap-3">
                    {section.checklist.map((item, idx) => (
                      <div key={idx} className="flex gap-2 text-slate-300">
                        <CheckCircle className="w-5 h-5 text-gold-400 flex-shrink-0 mt-0.5" />
                        {item}
                      </div>
                    ))}
                  </div>
                )}

                {/* Regulations */}
                {section.regulations && (
                  <div className="space-y-4">
                    {section.regulations.map((reg, idx) => (
                      <div key={idx} className="flex gap-4">
                        <Shield className="w-5 h-5 text-gold-400 flex-shrink-0 mt-1" />
                        <div>
                          <span className="font-semibold text-white">{reg.name}:</span>
                          <span className="text-slate-300 ml-2">{reg.description}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}

          {/* CTA Section */}
          <div className="p-8 backdrop-blur-sm bg-gradient-to-r from-gold-400/10 to-gold-600/10 border border-gold-400/30 rounded-xl text-center">
            <h3 className="text-2xl font-bold text-white mb-4">
              Ready to Participate?
            </h3>
            <p className="text-slate-300 mb-6 max-w-2xl mx-auto">
              Complete your accredited investor qualification to access active financing opportunities.
            </p>
            <div className="flex flex-wrap gap-4 justify-center">
              <Button
                variant="primary"
                size="lg"
                onClick={() => router.push('/financial-hub/qualification')}
              >
                Get Qualified
              </Button>
              <Button
                variant="ghost"
                size="lg"
                onClick={() => router.push('/financial-hub/subscription-agreements-guide')}
              >
                Learn About Subscription Agreements
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 px-4 border-t border-slate-800">
        <div className="max-w-7xl mx-auto text-center text-slate-400 text-sm">
          <p>&copy; {new Date().getFullYear()} GoldVenture. All rights reserved.</p>
          <p className="mt-2 text-xs">
            This information is for educational purposes only and does not constitute legal or financial advice.
            Always consult with qualified professionals before making investment decisions.
          </p>
        </div>
      </footer>
    </div>
  );
}
