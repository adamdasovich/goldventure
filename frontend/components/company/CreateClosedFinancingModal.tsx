'use client';

import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

interface NewsReleaseFlag {
  id: number;
  company_name: string;
  company_id: number;
  news_release_id: number;
  news_title: string;
  news_url: string;
  news_date: string;
  detected_keywords: string[];
  status: string;
  flagged_at: string;
}

interface CreateClosedFinancingModalProps {
  flag: NewsReleaseFlag;
  accessToken: string | null;
  onClose: () => void;
  onCreateComplete: () => void;
}

const FINANCING_TYPES = [
  { value: 'private_placement', label: 'Private Placement', description: 'Non-public offering to select investors' },
  { value: 'bought_deal', label: 'Bought Deal', description: 'Underwriter commits to full financing' },
  { value: 'flow_through', label: 'Flow-Through Shares', description: 'Tax-advantaged Canadian exploration financing' },
  { value: 'rights_offering', label: 'Rights Offering', description: 'Existing shareholders can purchase new shares' },
  { value: 'warrant_exercise', label: 'Warrant Exercise', description: 'Existing warrant holders exercise their warrants' },
  { value: 'public_offering', label: 'Public Offering', description: 'Public offering via prospectus' },
  { value: 'convertible', label: 'Convertible Debenture', description: 'Debt convertible to equity' },
  { value: 'debt', label: 'Debt Financing', description: 'Loan or credit facility' },
  { value: 'other', label: 'Other', description: 'Other type of financing' },
];

const UNIT_TYPES = [
  { value: 'shares', label: 'Common Shares Only', description: 'Simple equity offering' },
  { value: 'units', label: 'Units (Shares + Warrants)', description: 'Each unit includes shares and warrants' },
  { value: 'flow_through_shares', label: 'Flow-Through Shares', description: 'Tax-advantaged shares for Canadian investors' },
];

// Helper to infer financing type from detected keywords
const inferFinancingType = (keywords: string[]): string => {
  const keywordsLower = keywords.map(k => k.toLowerCase());

  if (keywordsLower.some(k => k.includes('flow-through') || k.includes('flow through'))) {
    return 'flow_through';
  }
  if (keywordsLower.some(k => k.includes('bought deal'))) {
    return 'bought_deal';
  }
  if (keywordsLower.some(k => k.includes('warrant') && k.includes('exercise'))) {
    return 'warrant_exercise';
  }
  if (keywordsLower.some(k => k.includes('rights offering'))) {
    return 'rights_offering';
  }
  if (keywordsLower.some(k => k.includes('convertible') || k.includes('debenture'))) {
    return 'convertible';
  }
  if (keywordsLower.some(k => k.includes('debt') || k.includes('loan'))) {
    return 'debt';
  }
  if (keywordsLower.some(k => k.includes('public offering') || k.includes('prospectus'))) {
    return 'public_offering';
  }
  if (keywordsLower.some(k => k.includes('private placement') || k.includes('non-brokered'))) {
    return 'private_placement';
  }

  return 'private_placement';
};

export function CreateClosedFinancingModal({ flag, accessToken, onClose, onCreateComplete }: CreateClosedFinancingModalProps) {
  const [step, setStep] = useState(1);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form state - pre-filled from flag
  const [financingType, setFinancingType] = useState(() => inferFinancingType(flag.detected_keywords));
  const [unitType, setUnitType] = useState('shares');
  const [amountRaised, setAmountRaised] = useState('');
  const [pricePerShare, setPricePerShare] = useState('');
  const [sharesIssued, setSharesIssued] = useState('');
  const [hasWarrants, setHasWarrants] = useState(false);
  const [warrantStrikePrice, setWarrantStrikePrice] = useState('');
  const [warrantExpiryDate, setWarrantExpiryDate] = useState('');
  const [announcedDate, setAnnouncedDate] = useState(() => flag.news_date ? flag.news_date.split('T')[0] : '');
  const [closingDate, setClosingDate] = useState(() => flag.news_date ? flag.news_date.split('T')[0] : '');
  const [useOfProceeds, setUseOfProceeds] = useState('');
  const [leadAgent, setLeadAgent] = useState('');
  const [pressReleaseUrl, setPressReleaseUrl] = useState(() => flag.news_url || '');
  const [notes, setNotes] = useState(() => `Created from news flag: "${flag.news_title}"`);

  // Auto-calculate shares when amount and price change
  const calculateShares = () => {
    if (amountRaised && pricePerShare) {
      const amount = parseFloat(amountRaised.replace(/,/g, ''));
      const price = parseFloat(pricePerShare);
      if (!isNaN(amount) && !isNaN(price) && price > 0) {
        const shares = Math.floor(amount / price);
        setSharesIssued(shares.toLocaleString());
      }
    }
  };

  const handleCreate = async () => {
    setError(null);
    setCreating(true);

    try {
      // Validate required fields
      if (!amountRaised || !closingDate) {
        throw new Error('Please fill in all required fields (Amount and Closing Date)');
      }

      const payload = {
        company_id: flag.company_id,
        financing_type: financingType,
        amount_raised_usd: parseFloat(amountRaised.replace(/,/g, '')),
        price_per_share: pricePerShare ? parseFloat(pricePerShare) : null,
        shares_issued: sharesIssued ? parseInt(sharesIssued.replace(/,/g, '')) : null,
        has_warrants: hasWarrants || unitType === 'units',
        warrant_strike_price: (hasWarrants || unitType === 'units') && warrantStrikePrice ? parseFloat(warrantStrikePrice) : null,
        warrant_expiry_date: (hasWarrants || unitType === 'units') && warrantExpiryDate ? warrantExpiryDate : null,
        announced_date: announcedDate || null,
        closing_date: closingDate,
        use_of_proceeds: useOfProceeds || '',
        lead_agent: leadAgent || '',
        press_release_url: pressReleaseUrl || '',
        notes: notes || '',
        source_news_flag_id: flag.id,
      };

      // Get fresh token from localStorage in case the prop is stale
      const token = accessToken || localStorage.getItem('accessToken');

      const response = await fetch(`${API_URL}/closed-financings/create/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || errorData.detail || 'Failed to create financing');
      }

      const data = await response.json();

      // Show success message
      let successMsg = `Closed financing created successfully for ${flag.company_name}!`;
      if (data.duplicates_removed && data.duplicates_removed > 0) {
        successMsg += ` (${data.duplicates_removed} duplicate financing round(s) removed)`;
      }
      alert(successMsg);

      onCreateComplete();
      onClose();
    } catch (err) {
      console.error('Failed to create financing:', err);
      setError(err instanceof Error ? err.message : 'Failed to create financing');
    } finally {
      setCreating(false);
    }
  };

  const formatCurrency = (value: string) => {
    const num = value.replace(/[^0-9.]/g, '');
    const parts = num.split('.');
    parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    return parts.join('.');
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-screen items-center justify-center p-4">
        <div className="fixed inset-0 bg-black/70" onClick={onClose} />

        <Card className="relative z-10 w-full max-w-3xl p-6 max-h-[90vh] overflow-y-auto">
          {/* Header */}
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-xl font-semibold text-white">Add Closed Financing from Flag</h2>
              <p className="text-sm text-slate-400">{flag.company_name}</p>
            </div>
            <button onClick={onClose} className="text-slate-400 hover:text-white">
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Pre-filled Info Banner */}
          <div className="mb-4 p-3 bg-emerald-900/30 border border-emerald-700/50 rounded-lg">
            <p className="text-sm text-emerald-300 font-medium mb-1">Pre-filled from News Flag:</p>
            <p className="text-sm text-slate-300">
              <span className="text-slate-500">News:</span> {flag.news_title}
            </p>
            <p className="text-sm text-slate-300">
              <span className="text-slate-500">Keywords:</span> {flag.detected_keywords.join(', ')}
            </p>
          </div>

          {/* Progress Steps */}
          <div className="flex items-center justify-center gap-2 mb-4">
            {[1, 2, 3].map((s) => (
              <div key={s} className="flex items-center">
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                    step >= s ? 'bg-emerald-500 text-white' : 'bg-slate-700 text-slate-400'
                  }`}
                >
                  {s}
                </div>
                {s < 3 && (
                  <div className={`w-12 h-1 ${step > s ? 'bg-emerald-500' : 'bg-slate-700'}`} />
                )}
              </div>
            ))}
          </div>
          <div className="flex justify-between text-xs text-slate-400 mb-6 px-2">
            <span>Type & Structure</span>
            <span>Offering Details</span>
            <span>Additional Info</span>
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-900/30 border border-red-700 rounded-lg text-red-400 text-sm">
              {error}
            </div>
          )}

          {/* Step 1: Financing Type & Structure */}
          {step === 1 && (
            <div className="space-y-6">
              {/* Financing Type */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-3">
                  Financing Type <span className="text-red-400">*</span>
                </label>
                <div className="grid grid-cols-2 gap-3">
                  {FINANCING_TYPES.map((type) => (
                    <button
                      key={type.value}
                      type="button"
                      onClick={() => setFinancingType(type.value)}
                      className={`p-3 rounded-lg border text-left transition-all ${
                        financingType === type.value
                          ? 'border-emerald-500 bg-emerald-500/10'
                          : 'border-slate-700 hover:border-slate-600'
                      }`}
                    >
                      <p className={`font-medium ${financingType === type.value ? 'text-emerald-400' : 'text-white'}`}>
                        {type.label}
                      </p>
                      <p className="text-xs text-slate-400 mt-1">{type.description}</p>
                    </button>
                  ))}
                </div>
              </div>

              {/* Unit Structure (for private placements) */}
              {(financingType === 'private_placement' || financingType === 'bought_deal' || financingType === 'flow_through') && (
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-3">
                    Offering Structure
                  </label>
                  <div className="grid grid-cols-1 gap-3">
                    {UNIT_TYPES.map((type) => (
                      <button
                        key={type.value}
                        type="button"
                        onClick={() => {
                          setUnitType(type.value);
                          setHasWarrants(type.value === 'units');
                        }}
                        className={`p-4 rounded-lg border text-left transition-all ${
                          unitType === type.value
                            ? 'border-emerald-500 bg-emerald-500/10'
                            : 'border-slate-700 hover:border-slate-600'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <div>
                            <p className={`font-medium ${unitType === type.value ? 'text-emerald-400' : 'text-white'}`}>
                              {type.label}
                            </p>
                            <p className="text-xs text-slate-400 mt-1">{type.description}</p>
                          </div>
                          {unitType === type.value && (
                            <svg className="w-5 h-5 text-emerald-500" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                            </svg>
                          )}
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Step 2: Offering Details */}
          {step === 2 && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                {/* Amount Raised */}
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Amount Raised (CAD) <span className="text-red-400">*</span>
                  </label>
                  <div className="relative">
                    <span className="absolute left-3 top-2.5 text-slate-400">$</span>
                    <input
                      type="text"
                      value={amountRaised}
                      onChange={(e) => setAmountRaised(formatCurrency(e.target.value))}
                      onBlur={calculateShares}
                      placeholder="1,000,000"
                      className="w-full bg-slate-800 border border-slate-700 rounded-lg pl-7 pr-4 py-2 text-white placeholder-slate-500 focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                    />
                  </div>
                </div>

                {/* Price Per Share/Unit */}
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Price Per {unitType === 'units' ? 'Unit' : 'Share'}
                  </label>
                  <div className="relative">
                    <span className="absolute left-3 top-2.5 text-slate-400">$</span>
                    <input
                      type="text"
                      value={pricePerShare}
                      onChange={(e) => setPricePerShare(e.target.value.replace(/[^0-9.]/g, ''))}
                      onBlur={calculateShares}
                      placeholder="0.50"
                      className="w-full bg-slate-800 border border-slate-700 rounded-lg pl-7 pr-4 py-2 text-white placeholder-slate-500 focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                    />
                  </div>
                </div>
              </div>

              {/* Calculated Shares */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  {unitType === 'units' ? 'Units' : 'Shares'} Issued
                </label>
                <input
                  type="text"
                  value={sharesIssued}
                  onChange={(e) => setSharesIssued(formatCurrency(e.target.value))}
                  placeholder="Auto-calculated or enter manually"
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white placeholder-slate-500 focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                />
                <p className="text-xs text-slate-500 mt-1">Auto-calculated based on amount and price, or enter manually</p>
              </div>

              {/* Warrant Details (if units) */}
              {(hasWarrants || unitType === 'units') && (
                <div className="p-4 bg-slate-800/50 rounded-lg border border-slate-700 space-y-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Badge variant="copper">Warrant Terms</Badge>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-slate-300 mb-2">
                        Warrant Strike Price
                      </label>
                      <div className="relative">
                        <span className="absolute left-3 top-2.5 text-slate-400">$</span>
                        <input
                          type="text"
                          value={warrantStrikePrice}
                          onChange={(e) => setWarrantStrikePrice(e.target.value.replace(/[^0-9.]/g, ''))}
                          placeholder="0.75"
                          className="w-full bg-slate-800 border border-slate-700 rounded-lg pl-7 pr-4 py-2 text-white placeholder-slate-500 focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-slate-300 mb-2">
                        Warrant Expiry Date
                      </label>
                      <input
                        type="date"
                        value={warrantExpiryDate}
                        onChange={(e) => setWarrantExpiryDate(e.target.value)}
                        className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* Dates */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Announced Date
                  </label>
                  <input
                    type="date"
                    value={announcedDate}
                    onChange={(e) => setAnnouncedDate(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Closing Date <span className="text-red-400">*</span>
                  </label>
                  <input
                    type="date"
                    value={closingDate}
                    onChange={(e) => setClosingDate(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Step 3: Additional Information */}
          {step === 3 && (
            <div className="space-y-4">
              {/* Use of Proceeds */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Use of Proceeds
                </label>
                <textarea
                  value={useOfProceeds}
                  onChange={(e) => setUseOfProceeds(e.target.value)}
                  rows={3}
                  placeholder="e.g., Exploration drilling at the Main Zone, general working capital..."
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white placeholder-slate-500 focus:ring-2 focus:ring-emerald-500 focus:border-transparent resize-none"
                />
              </div>

              {/* Lead Agent */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Lead Agent / Underwriter
                </label>
                <input
                  type="text"
                  value={leadAgent}
                  onChange={(e) => setLeadAgent(e.target.value)}
                  placeholder="e.g., Canaccord Genuity, BMO Capital Markets"
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white placeholder-slate-500 focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                />
              </div>

              {/* Press Release URL */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Press Release URL
                </label>
                <input
                  type="url"
                  value={pressReleaseUrl}
                  onChange={(e) => setPressReleaseUrl(e.target.value)}
                  placeholder="https://..."
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white placeholder-slate-500 focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                />
              </div>

              {/* Notes */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Additional Notes
                </label>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  rows={2}
                  placeholder="Any additional information about this financing..."
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white placeholder-slate-500 focus:ring-2 focus:ring-emerald-500 focus:border-transparent resize-none"
                />
              </div>

              {/* Summary */}
              <div className="p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-lg">
                <h4 className="text-sm font-medium text-emerald-400 mb-3">Closed Financing Summary</h4>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div className="text-slate-400">Company:</div>
                  <div className="text-white">{flag.company_name}</div>
                  <div className="text-slate-400">Type:</div>
                  <div className="text-white">{FINANCING_TYPES.find(t => t.value === financingType)?.label}</div>
                  <div className="text-slate-400">Amount:</div>
                  <div className="text-white">C${amountRaised || '---'}</div>
                  {pricePerShare && (
                    <>
                      <div className="text-slate-400">Price:</div>
                      <div className="text-white">${pricePerShare} per {unitType === 'units' ? 'unit' : 'share'}</div>
                    </>
                  )}
                  {sharesIssued && (
                    <>
                      <div className="text-slate-400">{unitType === 'units' ? 'Units' : 'Shares'}:</div>
                      <div className="text-white">{sharesIssued}</div>
                    </>
                  )}
                  {(hasWarrants || unitType === 'units') && warrantStrikePrice && (
                    <>
                      <div className="text-slate-400">Warrants:</div>
                      <div className="text-white">${warrantStrikePrice} strike{warrantExpiryDate && `, expires ${warrantExpiryDate}`}</div>
                    </>
                  )}
                  <div className="text-slate-400">Closing Date:</div>
                  <div className="text-white">{closingDate || '---'}</div>
                </div>
              </div>

              {/* Duplicate Warning */}
              <div className="p-3 bg-amber-900/30 border border-amber-700/50 rounded-lg">
                <p className="text-sm text-amber-300">
                  <strong>Note:</strong> Any duplicate announced financing rounds for this company within ±30 days of the closing date will be automatically removed.
                </p>
              </div>
            </div>
          )}

          {/* Navigation Buttons */}
          <div className="flex gap-3 mt-6">
            {step > 1 ? (
              <Button
                variant="ghost"
                className="flex-1"
                onClick={() => setStep(step - 1)}
                disabled={creating}
              >
                Back
              </Button>
            ) : (
              <Button
                variant="ghost"
                className="flex-1"
                onClick={onClose}
                disabled={creating}
              >
                Cancel
              </Button>
            )}

            {step < 3 ? (
              <Button
                variant="primary"
                className="flex-1 bg-emerald-600 hover:bg-emerald-700"
                onClick={() => setStep(step + 1)}
              >
                Continue
              </Button>
            ) : (
              <Button
                variant="primary"
                className="flex-1 bg-emerald-600 hover:bg-emerald-700"
                onClick={handleCreate}
                disabled={creating || !amountRaised || !closingDate}
              >
                {creating ? 'Creating...' : 'Create Closed Financing'}
              </Button>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}
