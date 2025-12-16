'use client';

import { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

interface CreateFinancingModalProps {
  companyId: number;
  companyName: string;
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
  { value: 'debt', label: 'Debt Financing', description: 'Loan or credit facility' },
  { value: 'royalty_stream', label: 'Royalty/Stream', description: 'Upfront payment for future production royalties' },
  { value: 'other', label: 'Other', description: 'Other type of financing' },
];

const UNIT_TYPES = [
  { value: 'shares', label: 'Common Shares Only', description: 'Simple equity offering' },
  { value: 'units', label: 'Units (Shares + Warrants)', description: 'Each unit includes shares and warrants' },
  { value: 'flow_through_shares', label: 'Flow-Through Shares', description: 'Tax-advantaged shares for Canadian investors' },
];

export function CreateFinancingModal({ companyId, companyName, accessToken, onClose, onCreateComplete }: CreateFinancingModalProps) {
  const [step, setStep] = useState(1);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form state
  const [financingType, setFinancingType] = useState('private_placement');
  const [unitType, setUnitType] = useState('shares');
  const [amountRaised, setAmountRaised] = useState('');
  const [pricePerShare, setPricePerShare] = useState('');
  const [sharesIssued, setSharesIssued] = useState('');
  const [hasWarrants, setHasWarrants] = useState(false);
  const [warrantStrikePrice, setWarrantStrikePrice] = useState('');
  const [warrantExpiryDate, setWarrantExpiryDate] = useState('');
  const [warrantRatio, setWarrantRatio] = useState('1'); // e.g., 1 warrant per unit
  const [announcedDate, setAnnouncedDate] = useState(new Date().toISOString().split('T')[0]);
  const [closingDate, setClosingDate] = useState('');
  const [useOfProceeds, setUseOfProceeds] = useState('');
  const [leadAgent, setLeadAgent] = useState('');
  const [pressReleaseUrl, setPressReleaseUrl] = useState('');
  const [notes, setNotes] = useState('');

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
      if (!amountRaised || !pricePerShare || !announcedDate) {
        throw new Error('Please fill in all required fields');
      }

      const payload: Record<string, any> = {
        company: companyId,
        financing_type: financingType,
        status: 'announced',
        announced_date: announcedDate,
        closing_date: closingDate || null,
        amount_raised_usd: parseFloat(amountRaised.replace(/,/g, '')),
        price_per_share: parseFloat(pricePerShare),
        shares_issued: parseInt(sharesIssued.replace(/,/g, '')) || 0,
        has_warrants: hasWarrants || unitType === 'units',
        warrant_strike_price: hasWarrants && warrantStrikePrice ? parseFloat(warrantStrikePrice) : null,
        warrant_expiry_date: hasWarrants && warrantExpiryDate ? warrantExpiryDate : null,
        use_of_proceeds: useOfProceeds || '',
        lead_agent: leadAgent || '',
        press_release_url: pressReleaseUrl || '',
        notes: notes || '',
      };

      const response = await fetch(`${API_URL}/financings/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`,
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || errorData.detail || 'Failed to create financing');
      }

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
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-xl font-semibold text-white">Create New Financing</h2>
              <p className="text-sm text-slate-400">{companyName}</p>
            </div>
            <button onClick={onClose} className="text-slate-400 hover:text-white">
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Progress Steps */}
          <div className="flex items-center justify-center gap-2 mb-6">
            {[1, 2, 3].map((s) => (
              <div key={s} className="flex items-center">
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                    step >= s ? 'bg-gold-500 text-white' : 'bg-slate-700 text-slate-400'
                  }`}
                >
                  {s}
                </div>
                {s < 3 && (
                  <div className={`w-12 h-1 ${step > s ? 'bg-gold-500' : 'bg-slate-700'}`} />
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
                          ? 'border-gold-500 bg-gold-500/10'
                          : 'border-slate-700 hover:border-slate-600'
                      }`}
                    >
                      <p className={`font-medium ${financingType === type.value ? 'text-gold-400' : 'text-white'}`}>
                        {type.label}
                      </p>
                      <p className="text-xs text-slate-400 mt-1">{type.description}</p>
                    </button>
                  ))}
                </div>
              </div>

              {/* Unit Structure (for private placements) */}
              {(financingType === 'private_placement' || financingType === 'bought_deal') && (
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-3">
                    Offering Structure <span className="text-red-400">*</span>
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
                            ? 'border-gold-500 bg-gold-500/10'
                            : 'border-slate-700 hover:border-slate-600'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <div>
                            <p className={`font-medium ${unitType === type.value ? 'text-gold-400' : 'text-white'}`}>
                              {type.label}
                            </p>
                            <p className="text-xs text-slate-400 mt-1">{type.description}</p>
                          </div>
                          {unitType === type.value && (
                            <svg className="w-5 h-5 text-gold-500" fill="currentColor" viewBox="0 0 20 20">
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
                    Target Amount (USD) <span className="text-red-400">*</span>
                  </label>
                  <div className="relative">
                    <span className="absolute left-3 top-2.5 text-slate-400">$</span>
                    <input
                      type="text"
                      value={amountRaised}
                      onChange={(e) => setAmountRaised(formatCurrency(e.target.value))}
                      onBlur={calculateShares}
                      placeholder="1,000,000"
                      className="w-full bg-slate-800 border border-slate-700 rounded-lg pl-7 pr-4 py-2 text-white placeholder-slate-500 focus:ring-2 focus:ring-gold-500 focus:border-transparent"
                    />
                  </div>
                </div>

                {/* Price Per Share/Unit */}
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Price Per {unitType === 'units' ? 'Unit' : 'Share'} <span className="text-red-400">*</span>
                  </label>
                  <div className="relative">
                    <span className="absolute left-3 top-2.5 text-slate-400">$</span>
                    <input
                      type="text"
                      value={pricePerShare}
                      onChange={(e) => setPricePerShare(e.target.value.replace(/[^0-9.]/g, ''))}
                      onBlur={calculateShares}
                      placeholder="0.50"
                      className="w-full bg-slate-800 border border-slate-700 rounded-lg pl-7 pr-4 py-2 text-white placeholder-slate-500 focus:ring-2 focus:ring-gold-500 focus:border-transparent"
                    />
                  </div>
                </div>
              </div>

              {/* Calculated Shares */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  {unitType === 'units' ? 'Units' : 'Shares'} to be Issued
                </label>
                <input
                  type="text"
                  value={sharesIssued}
                  onChange={(e) => setSharesIssued(formatCurrency(e.target.value))}
                  placeholder="Auto-calculated"
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white placeholder-slate-500 focus:ring-2 focus:ring-gold-500 focus:border-transparent"
                />
                <p className="text-xs text-slate-500 mt-1">Auto-calculated based on amount and price</p>
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
                          className="w-full bg-slate-800 border border-slate-700 rounded-lg pl-7 pr-4 py-2 text-white placeholder-slate-500 focus:ring-2 focus:ring-gold-500 focus:border-transparent"
                        />
                      </div>
                      <p className="text-xs text-slate-500 mt-1">Price to exercise each warrant</p>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-slate-300 mb-2">
                        Warrant Expiry Date
                      </label>
                      <input
                        type="date"
                        value={warrantExpiryDate}
                        onChange={(e) => setWarrantExpiryDate(e.target.value)}
                        className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-gold-500 focus:border-transparent"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      Warrants Per Unit
                    </label>
                    <select
                      value={warrantRatio}
                      onChange={(e) => setWarrantRatio(e.target.value)}
                      className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-gold-500 focus:border-transparent"
                    >
                      <option value="0.5">1/2 warrant per unit</option>
                      <option value="1">1 warrant per unit (full warrant)</option>
                      <option value="2">2 warrants per unit</option>
                    </select>
                  </div>
                </div>
              )}

              {/* Dates */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Announced Date <span className="text-red-400">*</span>
                  </label>
                  <input
                    type="date"
                    value={announcedDate}
                    onChange={(e) => setAnnouncedDate(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-gold-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Expected Closing Date
                  </label>
                  <input
                    type="date"
                    value={closingDate}
                    onChange={(e) => setClosingDate(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-gold-500 focus:border-transparent"
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
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white placeholder-slate-500 focus:ring-2 focus:ring-gold-500 focus:border-transparent resize-none"
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
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white placeholder-slate-500 focus:ring-2 focus:ring-gold-500 focus:border-transparent"
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
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white placeholder-slate-500 focus:ring-2 focus:ring-gold-500 focus:border-transparent"
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
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white placeholder-slate-500 focus:ring-2 focus:ring-gold-500 focus:border-transparent resize-none"
                />
              </div>

              {/* Summary */}
              <div className="p-4 bg-gold-500/10 border border-gold-500/30 rounded-lg">
                <h4 className="text-sm font-medium text-gold-400 mb-3">Financing Summary</h4>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div className="text-slate-400">Type:</div>
                  <div className="text-white">{FINANCING_TYPES.find(t => t.value === financingType)?.label}</div>
                  <div className="text-slate-400">Amount:</div>
                  <div className="text-white">${amountRaised || '---'}</div>
                  <div className="text-slate-400">Price:</div>
                  <div className="text-white">${pricePerShare || '---'} per {unitType === 'units' ? 'unit' : 'share'}</div>
                  <div className="text-slate-400">{unitType === 'units' ? 'Units' : 'Shares'}:</div>
                  <div className="text-white">{sharesIssued || '---'}</div>
                  {hasWarrants && (
                    <>
                      <div className="text-slate-400">Warrants:</div>
                      <div className="text-white">${warrantStrikePrice || '---'} strike, expires {warrantExpiryDate || '---'}</div>
                    </>
                  )}
                </div>
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
                className="flex-1"
                onClick={() => setStep(step + 1)}
              >
                Continue
              </Button>
            ) : (
              <Button
                variant="primary"
                className="flex-1"
                onClick={handleCreate}
                disabled={creating || !amountRaised || !pricePerShare || !announcedDate}
              >
                {creating ? 'Creating...' : 'Create Financing'}
              </Button>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}
