'use client';

import { useRouter } from 'next/navigation';
import {
  ArrowLeft,
  FileText,
  CheckCircle,
  AlertCircle,
  Clock,
  Shield,
  DollarSign,
  Users,
  Scale,
  BookOpen
} from 'lucide-react';
import { Button } from '@/components/ui/Button';
import LogoMono from '@/components/LogoMono';

export default function SubscriptionAgreementsGuide() {
  const router = useRouter();

  const sections = [
    {
      id: 'what-is',
      title: 'What is a Subscription Agreement?',
      icon: FileText,
      content: `A subscription agreement is a legally binding contract between an investor and a company (typically a private company or one conducting a private placement) that outlines the terms and conditions under which the investor agrees to purchase shares or other securities.

In the context of junior mining companies, subscription agreements are commonly used during private placement financings when companies raise capital from accredited investors before or instead of public offerings.`
    },
    {
      id: 'key-components',
      title: 'Key Components',
      icon: BookOpen,
      content: null,
      list: [
        {
          term: 'Investment Amount',
          description: 'The total dollar amount you are committing to invest and the price per share/unit'
        },
        {
          term: 'Securities Description',
          description: 'Details about what you are purchasing (common shares, units with warrants, flow-through shares, etc.)'
        },
        {
          term: 'Representations & Warranties',
          description: 'Statements confirming your eligibility as an accredited investor and your understanding of the risks'
        },
        {
          term: 'Hold Period',
          description: 'The statutory hold period during which you cannot resell the securities (typically 4 months in Canada)'
        },
        {
          term: 'Closing Conditions',
          description: 'Requirements that must be met before the transaction completes'
        },
        {
          term: 'Risk Acknowledgments',
          description: 'Your acknowledgment of the speculative nature of the investment'
        }
      ]
    },
    {
      id: 'process',
      title: 'The Subscription Process',
      icon: Clock,
      content: null,
      steps: [
        {
          number: 1,
          title: 'Review the Offering',
          description: 'Carefully read all offering documents, including the term sheet and any available prospectus or offering memorandum.'
        },
        {
          number: 2,
          title: 'Complete Accreditation',
          description: 'Verify that you meet the accredited investor criteria and complete any required qualification questionnaires.'
        },
        {
          number: 3,
          title: 'Sign the Agreement',
          description: 'Review and execute the subscription agreement, confirming your investment amount and acknowledging all terms.'
        },
        {
          number: 4,
          title: 'Submit Payment',
          description: 'Transfer funds according to the payment instructions provided (wire transfer, certified check, etc.).'
        },
        {
          number: 5,
          title: 'Await Closing',
          description: 'The company will confirm receipt and process your subscription. Closing may be subject to minimum raise requirements.'
        },
        {
          number: 6,
          title: 'Receive Securities',
          description: 'After closing, you will receive your share certificates or DRS statement confirming your ownership.'
        }
      ]
    },
    {
      id: 'accredited-investor',
      title: 'Accredited Investor Requirements',
      icon: Shield,
      content: `In Canada, to participate in most private placements, you must qualify as an "accredited investor" under National Instrument 45-106. Common criteria include:`,
      criteria: [
        'Net financial assets (excluding primary residence) exceeding $1,000,000',
        'Net income before taxes exceeding $200,000 in each of the two most recent years (or $300,000 combined with spouse)',
        'Net assets of at least $5,000,000',
        'Being a registered securities dealer, advisor, or investment fund manager',
        'Being a company with net assets of at least $5,000,000'
      ]
    },
    {
      id: 'risks',
      title: 'Important Risk Considerations',
      icon: AlertCircle,
      content: null,
      risks: [
        {
          title: 'Illiquidity',
          description: 'Private placement securities are subject to hold periods and may have limited resale markets'
        },
        {
          title: 'Loss of Capital',
          description: 'Junior mining investments are highly speculative; you could lose your entire investment'
        },
        {
          title: 'No Guarantee of Returns',
          description: 'Past performance does not guarantee future results; mineral exploration is inherently risky'
        },
        {
          title: 'Dilution',
          description: 'Future financings may dilute your ownership percentage'
        },
        {
          title: 'Regulatory Risk',
          description: 'Mining projects are subject to extensive regulation and permitting requirements'
        }
      ]
    },
    {
      id: 'rights',
      title: 'Your Rights as an Investor',
      icon: Scale,
      content: `When you sign a subscription agreement, you are entitled to certain rights and protections:`,
      rights: [
        'Right to receive all material information about the offering',
        'Right to a cooling-off period (in some jurisdictions)',
        'Right to receive share certificates or DRS statements',
        'Right to vote at shareholder meetings (for common shares)',
        'Right to receive dividends if declared',
        'Right to participate in future offerings (subject to terms)',
        'Protection under securities laws against fraud and misrepresentation'
      ]
    },
    {
      id: 'warrants',
      title: 'Understanding Warrants',
      icon: DollarSign,
      content: `Many private placements include warrants as part of the offering. A warrant gives you the right (but not the obligation) to purchase additional shares at a predetermined "strike price" within a specified time period.

For example, if you purchase units at $0.50 each with a half-warrant exercisable at $0.75 for 24 months, you can buy additional shares at $0.75 each anytime within 2 years, regardless of market price.

Warrants can provide significant upside if the share price appreciates above the strike price, but they expire worthless if the price remains below the strike price.`
    },
    {
      id: 'flow-through',
      title: 'Flow-Through Shares',
      icon: Users,
      content: `Flow-through shares are a unique Canadian tax incentive for mining and resource exploration. When you purchase flow-through shares:

- The company "flows through" the tax deductions from eligible exploration expenses to you
- You can claim these deductions against your income, potentially reducing your tax burden
- Flow-through shares typically trade at a premium to reflect their tax benefits
- Additional provincial tax credits may be available depending on your province of residence

Flow-through shares are particularly attractive for high-income investors seeking tax-efficient investment opportunities in the mining sector.`
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
              <FileText className="w-10 h-10" style={{ color: '#d4af37' }} />
            </div>
            <h1 className="text-4xl md:text-5xl font-bold mb-4 text-gradient-gold">
              Subscription Agreements Guide
            </h1>
            <p className="text-xl text-slate-300 max-w-2xl mx-auto">
              Everything you need to know about subscription agreements, private placements,
              and investing in junior mining companies.
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

                {/* Key Components List */}
                {section.list && (
                  <div className="space-y-4">
                    {section.list.map((item, idx) => (
                      <div key={idx} className="flex gap-4">
                        <CheckCircle className="w-5 h-5 text-gold-400 flex-shrink-0 mt-1" />
                        <div>
                          <span className="font-semibold text-white">{item.term}:</span>
                          <span className="text-slate-300 ml-2">{item.description}</span>
                        </div>
                      </div>
                    ))}
                  </div>
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

                {/* Criteria List */}
                {section.criteria && (
                  <ul className="space-y-3 mt-4">
                    {section.criteria.map((criterion, idx) => (
                      <li key={idx} className="flex gap-3 text-slate-300">
                        <Shield className="w-5 h-5 text-gold-400 flex-shrink-0 mt-0.5" />
                        {criterion}
                      </li>
                    ))}
                  </ul>
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

                {/* Rights */}
                {section.rights && (
                  <ul className="space-y-3 mt-4">
                    {section.rights.map((right, idx) => (
                      <li key={idx} className="flex gap-3 text-slate-300">
                        <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
                        {right}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            );
          })}

          {/* CTA Section */}
          <div className="p-8 backdrop-blur-sm bg-gradient-to-r from-gold-400/10 to-gold-600/10 border border-gold-400/30 rounded-xl text-center">
            <h3 className="text-2xl font-bold text-white mb-4">
              Ready to Invest?
            </h3>
            <p className="text-slate-300 mb-6 max-w-2xl mx-auto">
              Complete your accredited investor qualification and explore available financing opportunities.
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
                onClick={() => router.push('/financial-hub/agreements')}
              >
                View Agreements
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
