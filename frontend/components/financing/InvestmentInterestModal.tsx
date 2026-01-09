'use client';

import { useState, useEffect, useMemo } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { useAuth } from '@/contexts/AuthContext';

interface Financing {
  id: number;
  financing_type: string;
  financing_type_display: string;
  status: string;
  price_per_share: number | null;
  amount_raised_usd: number;
}

interface Company {
  id: number;
  name: string;
  ticker_symbol: string;
}

interface InvestmentInterestModalProps {
  financing: Financing;
  company: Company;
  onClose: () => void;
  onSuccess: () => void;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

export function InvestmentInterestModal({
  financing,
  company,
  onClose,
  onSuccess,
}: InvestmentInterestModalProps) {
  const { user } = useAuth();
  const accessToken = typeof window !== 'undefined' ? localStorage.getItem('accessToken') : null;

  // Form state
  const [step, setStep] = useState<'form' | 'confirmation' | 'success'>('form');
  const [isAccredited, setIsAccredited] = useState(false);
  const [sharesRequested, setSharesRequested] = useState<number>(1000);
  const [termSheetConfirmed, setTermSheetConfirmed] = useState(false);
  const [subscriptionConfirmed, setSubscriptionConfirmed] = useState(false);
  const [riskAcknowledged, setRiskAcknowledged] = useState(false);
  const [contactEmail, setContactEmail] = useState(user?.email || '');
  const [contactPhone, setContactPhone] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Calculate investment amount
  const investmentAmount = useMemo(() => {
    if (!financing.price_per_share) return 0;
    return sharesRequested * Number(financing.price_per_share);
  }, [sharesRequested, financing.price_per_share]);

  // Pre-fill email from user
  useEffect(() => {
    if (user?.email) {
      setContactEmail(user.email);
    }
  }, [user]);

  const handleSubmit = async () => {
    if (!accessToken) return;

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_URL}/investment-interest/register/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`,
        },
        body: JSON.stringify({
          financing: financing.id,
          is_accredited_investor: isAccredited,
          shares_requested: sharesRequested,
          term_sheet_confirmed: termSheetConfirmed,
          subscription_agreement_confirmed: subscriptionConfirmed,
          contact_email: contactEmail,
          contact_phone: contactPhone,
          risk_acknowledged: riskAcknowledged,
        }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || data.error || Object.values(data).flat().join(', ') || 'Failed to register interest');
      }

      setStep('success');
      setTimeout(() => {
        onSuccess();
      }, 2000);
    } catch (err: any) {
      setError(err.message || 'Failed to register investment interest');
    } finally {
      setLoading(false);
    }
  };

  const canProceed = isAccredited && sharesRequested > 0 && termSheetConfirmed &&
    subscriptionConfirmed && riskAcknowledged && contactEmail;

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-CA', {
      style: 'currency',
      currency: 'CAD',
      minimumFractionDigits: 2,
    }).format(amount);
  };

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4 overflow-y-auto">
      <Card variant="glass-card" className="max-w-2xl w-full my-8">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-gold-400">Register Investment Interest</CardTitle>
              <p className="text-sm text-slate-400 mt-1">
                {company.name} - {financing.financing_type_display}
              </p>
            </div>
            <button
              onClick={onClose}
              className="text-slate-400 hover:text-white transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </CardHeader>
        <CardContent>
          {step === 'success' ? (
            <div className="text-center py-8">
              <div className="w-16 h-16 mx-auto bg-green-500/20 rounded-full flex items-center justify-center mb-4">
                <svg className="w-8 h-8 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">Interest Registered Successfully!</h3>
              <p className="text-slate-400">
                Your investment interest has been recorded. The company will contact you at {contactEmail} with next steps.
              </p>
            </div>
          ) : (
            <form className="space-y-6" onSubmit={(e) => { e.preventDefault(); handleSubmit(); }}>
              {error && (
                <div className="bg-red-500/10 border border-red-500/30 text-red-400 px-4 py-3 rounded-lg text-sm">
                  {error}
                </div>
              )}

              {/* Accredited Investor Confirmation */}
              <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700">
                <label className="flex items-start gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={isAccredited}
                    onChange={(e) => setIsAccredited(e.target.checked)}
                    className="w-5 h-5 mt-0.5 rounded border-slate-600 text-gold-500 focus:ring-gold-500"
                  />
                  <div>
                    <span className="text-white font-medium">I confirm I am an Accredited Investor</span>
                    <p className="text-sm text-slate-400 mt-1">
                      As defined by securities regulations, I meet the income, net worth, or professional
                      qualifications required to be classified as an accredited investor.
                    </p>
                  </div>
                </label>
              </div>

              {/* Shares and Investment Amount */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Number of Shares
                  </label>
                  <input
                    type="number"
                    min="1"
                    step="1"
                    value={sharesRequested}
                    onChange={(e) => setSharesRequested(Math.max(1, parseInt(e.target.value) || 0))}
                    className="w-full px-4 py-3 bg-slate-800/50 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-gold-500"
                    required
                  />
                  {financing.price_per_share && (
                    <p className="text-xs text-slate-400 mt-1">
                      @ ${Number(financing.price_per_share).toFixed(4)} per share
                    </p>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Investment Amount
                  </label>
                  <div className="px-4 py-3 bg-slate-900/50 border border-slate-700 rounded-lg">
                    <span className="text-2xl font-bold text-gold-400">
                      {formatCurrency(investmentAmount)}
                    </span>
                  </div>
                </div>
              </div>

              {/* Document Confirmations */}
              <div className="space-y-3">
                <h4 className="text-sm font-medium text-white">Document Confirmations</h4>

                <label className="flex items-start gap-3 cursor-pointer p-3 bg-slate-800/30 rounded-lg hover:bg-slate-800/50 transition-colors">
                  <input
                    type="checkbox"
                    checked={termSheetConfirmed}
                    onChange={(e) => setTermSheetConfirmed(e.target.checked)}
                    className="w-5 h-5 mt-0.5 rounded border-slate-600 text-gold-500 focus:ring-gold-500"
                  />
                  <div>
                    <span className="text-white">I have read and understood the Term Sheet</span>
                    <p className="text-xs text-slate-400 mt-0.5">
                      The term sheet contains key details about this financing round.
                    </p>
                  </div>
                </label>

                <label className="flex items-start gap-3 cursor-pointer p-3 bg-slate-800/30 rounded-lg hover:bg-slate-800/50 transition-colors">
                  <input
                    type="checkbox"
                    checked={subscriptionConfirmed}
                    onChange={(e) => setSubscriptionConfirmed(e.target.checked)}
                    className="w-5 h-5 mt-0.5 rounded border-slate-600 text-gold-500 focus:ring-gold-500"
                  />
                  <div>
                    <span className="text-white">I have read and understood the Subscription Agreement</span>
                    <p className="text-xs text-slate-400 mt-0.5">
                      The subscription agreement outlines the terms and conditions of your investment.
                    </p>
                  </div>
                </label>
              </div>

              {/* Contact Information */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Contact Email <span className="text-red-400">*</span>
                  </label>
                  <input
                    type="email"
                    value={contactEmail}
                    onChange={(e) => setContactEmail(e.target.value)}
                    className="w-full px-4 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-gold-500"
                    placeholder="your@email.com"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Contact Phone (Optional)
                  </label>
                  <input
                    type="tel"
                    value={contactPhone}
                    onChange={(e) => setContactPhone(e.target.value)}
                    className="w-full px-4 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-gold-500"
                    placeholder="+1 (555) 123-4567"
                  />
                </div>
              </div>

              {/* Risk Acknowledgment */}
              <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-4">
                <label className="flex items-start gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={riskAcknowledged}
                    onChange={(e) => setRiskAcknowledged(e.target.checked)}
                    className="w-5 h-5 mt-0.5 rounded border-amber-600 text-amber-500 focus:ring-amber-500"
                  />
                  <div>
                    <span className="text-amber-200 font-medium">Investment Risk Acknowledgment</span>
                    <p className="text-sm text-amber-200/70 mt-1">
                      I understand that investing in private placements involves significant risk, including
                      the potential loss of my entire investment. I have reviewed the risk factors and am
                      making this investment decision based on my own independent judgment.
                    </p>
                  </div>
                </label>
              </div>

              {/* Summary */}
              <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700">
                <h4 className="text-sm font-medium text-white mb-3">Investment Summary</h4>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-slate-400">Company:</span>
                    <span className="text-white ml-2">{company.name}</span>
                  </div>
                  <div>
                    <span className="text-slate-400">Financing Type:</span>
                    <span className="text-white ml-2">{financing.financing_type_display}</span>
                  </div>
                  <div>
                    <span className="text-slate-400">Shares:</span>
                    <span className="text-white ml-2">{sharesRequested.toLocaleString()}</span>
                  </div>
                  <div>
                    <span className="text-slate-400">Total:</span>
                    <span className="text-gold-400 font-semibold ml-2">{formatCurrency(investmentAmount)}</span>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-3">
                <Button
                  type="button"
                  variant="ghost"
                  onClick={onClose}
                  className="flex-1"
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  className="flex-1"
                  disabled={!canProceed || loading}
                >
                  {loading ? 'Submitting...' : 'Confirm Interest'}
                </Button>
              </div>

              <p className="text-xs text-slate-500 text-center">
                By submitting, you agree to be contacted by {company.name} regarding this investment opportunity.
                This registration of interest is non-binding.
              </p>
            </form>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
