'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/Button';
import { CreateFinancingModal } from '@/components/company/CreateFinancingModal';

// Financing types for the dropdown
const financingTypes = [
  { value: 'private_placement', label: 'Private Placement' },
  { value: 'bought_deal', label: 'Bought Deal' },
  { value: 'flow_through', label: 'Flow-Through Shares' },
  { value: 'warrant_exercise', label: 'Warrant Exercise' },
  { value: 'rights_offering', label: 'Rights Offering' },
  { value: 'public_offering', label: 'Public Offering' },
  { value: 'debt', label: 'Debt Financing' },
  { value: 'convertible', label: 'Convertible Debenture' },
  { value: 'other', label: 'Other' },
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

  // Default to private placement as it's most common for junior miners
  return 'private_placement';
};

// Interface for the closed financing form data
interface ClosedFinancingFormData {
  company_id: number;
  financing_type: string;
  amount_raised_usd: string;
  price_per_share: string;
  shares_issued: string;
  has_warrants: boolean;
  warrant_strike_price: string;
  warrant_expiry_date: string;
  announced_date: string;
  closing_date: string;
  lead_agent: string;
  use_of_proceeds: string;
  press_release_url: string;
  notes: string;
}

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
  reviewed_by: string | null;
  reviewed_at: string | null;
  created_financing_id: number | null;
  review_notes: string;
}

export default function NewsFlagsPage() {
  const { user } = useAuth();
  const [flags, setFlags] = useState<NewsReleaseFlag[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('pending');
  const [selectedFlag, setSelectedFlag] = useState<NewsReleaseFlag | null>(null);
  const [showFinancingModal, setShowFinancingModal] = useState(false);
  const [showDismissModal, setShowDismissModal] = useState(false);
  const [dismissNotes, setDismissNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [showCloseFinancingModal, setShowCloseFinancingModal] = useState(false);
  const [closingDate, setClosingDate] = useState('');

  // State for the new "Add Closed Financing from Flag" modal
  const [showAddClosedFinancingModal, setShowAddClosedFinancingModal] = useState(false);
  const [closedFinancingForm, setClosedFinancingForm] = useState<ClosedFinancingFormData>({
    company_id: 0,
    financing_type: 'private_placement',
    amount_raised_usd: '',
    price_per_share: '',
    shares_issued: '',
    has_warrants: false,
    warrant_strike_price: '',
    warrant_expiry_date: '',
    announced_date: '',
    closing_date: '',
    lead_agent: '',
    use_of_proceeds: '',
    press_release_url: '',
    notes: '',
  });

  const accessToken = typeof window !== 'undefined' ? localStorage.getItem('accessToken') : null;

  useEffect(() => {
    fetchFlags();
  }, [statusFilter]);

  const fetchFlags = async () => {
    try {
      setLoading(true);
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/news-flags/?status=${statusFilter}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
          }
        }
      );

      if (!response.ok) throw new Error('Failed to fetch news flags');

      const data = await response.json();
      setFlags(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenFinancingModal = (flag: NewsReleaseFlag) => {
    setSelectedFlag(flag);
    setShowFinancingModal(true);
  };

  const handleFinancingCreated = async () => {
    // After financing is created via CreateFinancingModal, mark the flag as reviewed
    if (selectedFlag) {
      try {
        // Mark the flag as reviewed_financing
        await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/news-flags/${selectedFlag.id}/mark-reviewed/`,
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
            },
            body: JSON.stringify({ notes: 'Financing created from news flag' })
          }
        );
      } catch (err) {
        console.error('Failed to mark flag as reviewed:', err);
      }
    }

    setShowFinancingModal(false);
    setSelectedFlag(null);
    fetchFlags();
  };

  const handleCloseFinancingModal = () => {
    setShowFinancingModal(false);
    setSelectedFlag(null);
  };

  const handleDismissFlag = async () => {
    if (!selectedFlag) return;

    try {
      setSubmitting(true);
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/news-flags/${selectedFlag.id}/dismiss/`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
          },
          body: JSON.stringify({ notes: dismissNotes })
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to dismiss flag');
      }

      alert('Flag dismissed successfully!');
      setShowDismissModal(false);
      setSelectedFlag(null);
      setDismissNotes('');
      fetchFlags();
    } catch (err: any) {
      alert(`Error: ${err.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  const handleCloseFinancing = async () => {
    if (!selectedFlag) return;

    try {
      setSubmitting(true);
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/news-flags/${selectedFlag.id}/close-financing/`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
          },
          body: JSON.stringify({
            closing_date: closingDate || undefined
          })
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to close financing');
      }

      const data = await response.json();
      alert(`Financing closed successfully! ${data.financing?.company_name || ''}`);
      setShowCloseFinancingModal(false);
      setSelectedFlag(null);
      setClosingDate('');
      fetchFlags();
    } catch (err: any) {
      alert(`Error: ${err.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  // Handler to open the Add Closed Financing modal with pre-filled data from the flag
  const handleOpenAddClosedFinancing = (flag: NewsReleaseFlag) => {
    setSelectedFlag(flag);

    // Pre-fill form with data from the news flag
    const inferredType = inferFinancingType(flag.detected_keywords);

    setClosedFinancingForm({
      company_id: flag.company_id,
      financing_type: inferredType,
      amount_raised_usd: '',
      price_per_share: '',
      shares_issued: '',
      has_warrants: false,
      warrant_strike_price: '',
      warrant_expiry_date: '',
      announced_date: flag.news_date ? flag.news_date.split('T')[0] : '',
      closing_date: flag.news_date ? flag.news_date.split('T')[0] : '',
      lead_agent: '',
      use_of_proceeds: '',
      press_release_url: flag.news_url || '',
      notes: `Created from news flag: "${flag.news_title}"`,
    });

    setShowAddClosedFinancingModal(true);
  };

  // Handler to submit the closed financing form
  const handleSubmitClosedFinancing = async () => {
    if (!selectedFlag) return;

    // Validation
    if (!closedFinancingForm.financing_type) {
      alert('Please select a financing type');
      return;
    }
    if (!closedFinancingForm.amount_raised_usd || parseFloat(closedFinancingForm.amount_raised_usd) <= 0) {
      alert('Please enter a valid amount raised');
      return;
    }
    if (!closedFinancingForm.closing_date) {
      alert('Please enter a closing date');
      return;
    }

    try {
      setSubmitting(true);

      // Prepare the data for submission
      const submitData = {
        company_id: closedFinancingForm.company_id,
        financing_type: closedFinancingForm.financing_type,
        amount_raised_usd: parseFloat(closedFinancingForm.amount_raised_usd),
        price_per_share: closedFinancingForm.price_per_share ? parseFloat(closedFinancingForm.price_per_share) : null,
        shares_issued: closedFinancingForm.shares_issued ? parseInt(closedFinancingForm.shares_issued) : null,
        has_warrants: closedFinancingForm.has_warrants,
        warrant_strike_price: closedFinancingForm.warrant_strike_price ? parseFloat(closedFinancingForm.warrant_strike_price) : null,
        warrant_expiry_date: closedFinancingForm.warrant_expiry_date || null,
        announced_date: closedFinancingForm.announced_date || null,
        closing_date: closedFinancingForm.closing_date,
        lead_agent: closedFinancingForm.lead_agent || null,
        use_of_proceeds: closedFinancingForm.use_of_proceeds || null,
        press_release_url: closedFinancingForm.press_release_url || null,
        notes: closedFinancingForm.notes || null,
        source_news_flag_id: selectedFlag.id,  // Link to the news flag for duplicate detection
      };

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/closed-financings/create/`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
          },
          body: JSON.stringify(submitData)
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to create closed financing');
      }

      const data = await response.json();

      // Show success message including info about duplicate removal if applicable
      let successMessage = `Closed financing created successfully for ${selectedFlag.company_name}!`;
      if (data.duplicates_removed && data.duplicates_removed > 0) {
        successMessage += ` (${data.duplicates_removed} duplicate financing round(s) removed)`;
      }
      alert(successMessage);

      // Reset form and close modal
      setShowAddClosedFinancingModal(false);
      setSelectedFlag(null);
      setClosedFinancingForm({
        company_id: 0,
        financing_type: 'private_placement',
        amount_raised_usd: '',
        price_per_share: '',
        shares_issued: '',
        has_warrants: false,
        warrant_strike_price: '',
        warrant_expiry_date: '',
        announced_date: '',
        closing_date: '',
        lead_agent: '',
        use_of_proceeds: '',
        press_release_url: '',
        notes: '',
      });

      // Refresh the flags list
      fetchFlags();
    } catch (err: any) {
      alert(`Error: ${err.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  if (!user?.is_superuser) {
    return (
      <div className="text-center py-12">
        <h1 className="text-2xl font-bold text-slate-100 mb-4">Access Denied</h1>
        <p className="text-slate-400">Only superusers can access this page.</p>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-100 mb-2">
          News Release Financing Flags
        </h1>
        <p className="text-slate-400">
          Review news releases flagged for potential financing announcements
        </p>
      </div>

      {/* Status Filter */}
      <div className="mb-6 flex gap-2">
        {['pending', 'reviewed_financing', 'reviewed_false_positive'].map((status) => (
          <button
            key={status}
            onClick={() => setStatusFilter(status)}
            className={`px-4 py-2 rounded-lg transition-colors ${
              statusFilter === status
                ? 'bg-gold-500 text-slate-900'
                : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
            }`}
          >
            {status.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
          </button>
        ))}
      </div>

      {/* Loading/Error States */}
      {loading && (
        <div className="text-center py-12">
          <div className="animate-spin w-8 h-8 border-2 border-gold-500 border-t-transparent rounded-full mx-auto" />
        </div>
      )}

      {error && (
        <div className="bg-red-500/10 border border-red-500/50 rounded-lg p-4 mb-6">
          <p className="text-red-400">{error}</p>
        </div>
      )}

      {/* Flags List */}
      {!loading && !error && flags.length === 0 && (
        <div className="text-center py-12">
          <p className="text-slate-400">No {statusFilter} flags found.</p>
        </div>
      )}

      {!loading && !error && flags.length > 0 && (
        <div className="space-y-4">
          {flags.map((flag) => (
            <div
              key={flag.id}
              className="bg-slate-800/50 border border-slate-700 rounded-lg p-6"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-slate-100 mb-1">
                    {flag.company_name}
                  </h3>
                  <p className="text-slate-300 mb-2">{flag.news_title}</p>
                  <div className="flex items-center gap-4 text-sm text-slate-400">
                    <span>Release Date: {new Date(flag.news_date).toLocaleDateString()}</span>
                    <span>Flagged: {new Date(flag.flagged_at).toLocaleDateString()}</span>
                  </div>
                </div>
                {flag.status === 'pending' && (
                  <div className="flex gap-2 flex-wrap">
                    <Button
                      variant="primary"
                      onClick={() => handleOpenFinancingModal(flag)}
                      size="sm"
                    >
                      Create Financing
                    </Button>
                    <Button
                      variant="primary"
                      onClick={() => handleOpenAddClosedFinancing(flag)}
                      size="sm"
                      className="bg-emerald-600 hover:bg-emerald-700"
                    >
                      + Add Closed Financing
                    </Button>
                    <Button
                      variant="secondary"
                      onClick={() => {
                        setSelectedFlag(flag);
                        setShowDismissModal(true);
                      }}
                      size="sm"
                    >
                      Dismiss
                    </Button>
                  </div>
                )}
                {flag.status === 'reviewed_financing' && flag.created_financing_id && (
                  <div className="flex gap-2">
                    <Button
                      variant="primary"
                      onClick={() => {
                        setSelectedFlag(flag);
                        setShowCloseFinancingModal(true);
                      }}
                      size="sm"
                    >
                      Close Financing
                    </Button>
                  </div>
                )}
              </div>

              {/* Detected Keywords */}
              <div className="mb-4">
                <p className="text-sm text-slate-500 mb-2">Detected Keywords:</p>
                <div className="flex flex-wrap gap-2">
                  {flag.detected_keywords.map((keyword, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-1 bg-gold-500/20 text-gold-400 text-xs rounded"
                    >
                      {keyword}
                    </span>
                  ))}
                </div>
              </div>

              {/* News Release Link */}
              <a
                href={flag.news_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-gold-400 hover:text-gold-300"
              >
                View News Release →
              </a>

              {/* Review Info */}
              {flag.status !== 'pending' && (
                <div className="mt-4 pt-4 border-t border-slate-700">
                  <p className="text-sm text-slate-400">
                    Reviewed by {flag.reviewed_by} on{' '}
                    {flag.reviewed_at && new Date(flag.reviewed_at).toLocaleDateString()}
                  </p>
                  {flag.review_notes && (
                    <p className="text-sm text-slate-500 mt-1">{flag.review_notes}</p>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Create Financing Modal - using the same component as company detail pages */}
      {showFinancingModal && selectedFlag && (
        <CreateFinancingModal
          companyId={selectedFlag.company_id}
          companyName={selectedFlag.company_name}
          accessToken={accessToken}
          onClose={handleCloseFinancingModal}
          onCreateComplete={handleFinancingCreated}
        />
      )}

      {/* Dismiss Modal */}
      {showDismissModal && selectedFlag && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-slate-800 rounded-lg p-6 max-w-md w-full">
            <h2 className="text-xl font-bold text-slate-100 mb-4">
              Dismiss Flag
            </h2>
            <p className="text-slate-400 mb-4">
              Are you sure you want to dismiss this flag as a false positive?
            </p>
            <div className="mb-4">
              <label className="block text-sm font-medium text-slate-300 mb-1">
                Reason (optional)
              </label>
              <textarea
                value={dismissNotes}
                onChange={(e) => setDismissNotes(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-100"
                rows={3}
                placeholder="Why is this a false positive?"
              />
            </div>
            <div className="flex gap-3">
              <Button
                variant="secondary"
                onClick={handleDismissFlag}
                disabled={submitting}
                className="flex-1"
              >
                {submitting ? 'Dismissing...' : 'Dismiss Flag'}
              </Button>
              <Button
                variant="primary"
                onClick={() => {
                  setShowDismissModal(false);
                  setSelectedFlag(null);
                  setDismissNotes('');
                }}
                disabled={submitting}
              >
                Cancel
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Close Financing Modal */}
      {showCloseFinancingModal && selectedFlag && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-slate-800 rounded-lg p-6 max-w-md w-full">
            <h2 className="text-xl font-bold text-slate-100 mb-4">
              Close Financing
            </h2>
            <p className="text-slate-400 mb-4">
              Mark this financing as closed. This will add it to the Closed Financings page
              and remove it from the news-flags queue.
            </p>
            <div className="mb-4 p-3 bg-slate-900 rounded-lg">
              <p className="text-sm text-slate-300">
                <span className="text-slate-500">Company:</span> {selectedFlag.company_name}
              </p>
              <p className="text-sm text-slate-300 mt-1">
                <span className="text-slate-500">News:</span> {selectedFlag.news_title}
              </p>
            </div>
            <div className="mb-4">
              <label htmlFor="closing-date" className="block text-sm font-medium text-slate-300 mb-1">
                Closing Date (optional)
              </label>
              <input
                type="date"
                id="closing-date"
                value={closingDate}
                onChange={(e) => setClosingDate(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-100"
                title="Closing date for the financing"
              />
              <p className="text-xs text-slate-500 mt-1">
                Leave blank to use the news release date
              </p>
            </div>
            <div className="flex gap-3">
              <Button
                variant="primary"
                onClick={handleCloseFinancing}
                disabled={submitting}
                className="flex-1"
              >
                {submitting ? 'Closing...' : 'Close Financing'}
              </Button>
              <Button
                variant="secondary"
                onClick={() => {
                  setShowCloseFinancingModal(false);
                  setSelectedFlag(null);
                  setClosingDate('');
                }}
                disabled={submitting}
              >
                Cancel
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Add Closed Financing from Flag Modal - Comprehensive Form */}
      {showAddClosedFinancingModal && selectedFlag && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50 overflow-y-auto">
          <div className="bg-slate-800 rounded-lg p-6 max-w-2xl w-full my-8">
            <h2 className="text-xl font-bold text-slate-100 mb-2">
              Add Closed Financing from Flag
            </h2>
            <p className="text-slate-400 mb-4 text-sm">
              Create a closed financing record pre-filled with data from the news flag.
              Any duplicate financing rounds for this company will be automatically removed.
            </p>

            {/* Pre-filled Info Banner */}
            <div className="mb-4 p-3 bg-emerald-900/30 border border-emerald-700/50 rounded-lg">
              <p className="text-sm text-emerald-300 font-medium mb-1">Pre-filled from News Flag:</p>
              <p className="text-sm text-slate-300">
                <span className="text-slate-500">Company:</span> {selectedFlag.company_name}
              </p>
              <p className="text-sm text-slate-300">
                <span className="text-slate-500">News:</span> {selectedFlag.news_title}
              </p>
              <p className="text-sm text-slate-300">
                <span className="text-slate-500">Keywords:</span> {selectedFlag.detected_keywords.join(', ')}
              </p>
            </div>

            {/* Form Fields */}
            <div className="space-y-4 max-h-[60vh] overflow-y-auto pr-2">
              {/* Financing Type */}
              <div>
                <label htmlFor="cf-financing-type" className="block text-sm font-medium text-slate-300 mb-1">
                  Financing Type <span className="text-red-400">*</span>
                </label>
                <select
                  id="cf-financing-type"
                  title="Financing Type"
                  value={closedFinancingForm.financing_type}
                  onChange={(e) => setClosedFinancingForm({ ...closedFinancingForm, financing_type: e.target.value })}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-100"
                >
                  {financingTypes.map((type) => (
                    <option key={type.value} value={type.value}>
                      {type.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Amount Raised */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">
                  Amount Raised (CAD) <span className="text-red-400">*</span>
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={closedFinancingForm.amount_raised_usd}
                  onChange={(e) => setClosedFinancingForm({ ...closedFinancingForm, amount_raised_usd: e.target.value })}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-100"
                  placeholder="e.g., 5000000"
                />
              </div>

              {/* Price Per Share */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">
                  Price Per Share (CAD)
                </label>
                <input
                  type="number"
                  step="0.001"
                  value={closedFinancingForm.price_per_share}
                  onChange={(e) => setClosedFinancingForm({ ...closedFinancingForm, price_per_share: e.target.value })}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-100"
                  placeholder="e.g., 0.15"
                />
              </div>

              {/* Shares Issued */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">
                  Shares Issued
                </label>
                <input
                  type="number"
                  value={closedFinancingForm.shares_issued}
                  onChange={(e) => setClosedFinancingForm({ ...closedFinancingForm, shares_issued: e.target.value })}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-100"
                  placeholder="e.g., 33333333"
                />
              </div>

              {/* Has Warrants */}
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="has-warrants"
                  checked={closedFinancingForm.has_warrants}
                  onChange={(e) => setClosedFinancingForm({ ...closedFinancingForm, has_warrants: e.target.checked })}
                  className="w-4 h-4 rounded border-slate-700 bg-slate-900"
                />
                <label htmlFor="has-warrants" className="text-sm font-medium text-slate-300">
                  Includes Warrants
                </label>
              </div>

              {/* Warrant Details (shown only if has_warrants) */}
              {closedFinancingForm.has_warrants && (
                <div className="grid grid-cols-2 gap-4 pl-6 border-l-2 border-slate-700">
                  <div>
                    <label htmlFor="cf-warrant-strike" className="block text-sm font-medium text-slate-300 mb-1">
                      Warrant Strike Price (CAD)
                    </label>
                    <input
                      type="number"
                      id="cf-warrant-strike"
                      title="Warrant Strike Price"
                      step="0.001"
                      value={closedFinancingForm.warrant_strike_price}
                      onChange={(e) => setClosedFinancingForm({ ...closedFinancingForm, warrant_strike_price: e.target.value })}
                      className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-100"
                      placeholder="e.g., 0.25"
                    />
                  </div>
                  <div>
                    <label htmlFor="cf-warrant-expiry" className="block text-sm font-medium text-slate-300 mb-1">
                      Warrant Expiry Date
                    </label>
                    <input
                      type="date"
                      id="cf-warrant-expiry"
                      title="Warrant Expiry Date"
                      value={closedFinancingForm.warrant_expiry_date}
                      onChange={(e) => setClosedFinancingForm({ ...closedFinancingForm, warrant_expiry_date: e.target.value })}
                      className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-100"
                    />
                  </div>
                </div>
              )}

              {/* Dates */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label htmlFor="cf-announced-date" className="block text-sm font-medium text-slate-300 mb-1">
                    Announced Date
                  </label>
                  <input
                    type="date"
                    id="cf-announced-date"
                    title="Announced Date"
                    value={closedFinancingForm.announced_date}
                    onChange={(e) => setClosedFinancingForm({ ...closedFinancingForm, announced_date: e.target.value })}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-100"
                  />
                </div>
                <div>
                  <label htmlFor="cf-closing-date" className="block text-sm font-medium text-slate-300 mb-1">
                    Closing Date <span className="text-red-400">*</span>
                  </label>
                  <input
                    type="date"
                    id="cf-closing-date"
                    title="Closing Date"
                    value={closedFinancingForm.closing_date}
                    onChange={(e) => setClosedFinancingForm({ ...closedFinancingForm, closing_date: e.target.value })}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-100"
                  />
                </div>
              </div>

              {/* Lead Agent */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">
                  Lead Agent / Underwriter
                </label>
                <input
                  type="text"
                  value={closedFinancingForm.lead_agent}
                  onChange={(e) => setClosedFinancingForm({ ...closedFinancingForm, lead_agent: e.target.value })}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-100"
                  placeholder="e.g., Canaccord Genuity"
                />
              </div>

              {/* Use of Proceeds */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">
                  Use of Proceeds
                </label>
                <textarea
                  value={closedFinancingForm.use_of_proceeds}
                  onChange={(e) => setClosedFinancingForm({ ...closedFinancingForm, use_of_proceeds: e.target.value })}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-100"
                  rows={2}
                  placeholder="e.g., Exploration drilling, working capital"
                />
              </div>

              {/* Press Release URL */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">
                  Press Release URL
                </label>
                <input
                  type="url"
                  value={closedFinancingForm.press_release_url}
                  onChange={(e) => setClosedFinancingForm({ ...closedFinancingForm, press_release_url: e.target.value })}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-100"
                  placeholder="https://..."
                />
              </div>

              {/* Notes */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">
                  Notes
                </label>
                <textarea
                  value={closedFinancingForm.notes}
                  onChange={(e) => setClosedFinancingForm({ ...closedFinancingForm, notes: e.target.value })}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-100"
                  rows={2}
                  placeholder="Additional notes..."
                />
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-3 mt-6 pt-4 border-t border-slate-700">
              <Button
                variant="primary"
                onClick={handleSubmitClosedFinancing}
                disabled={submitting}
                className="flex-1 bg-emerald-600 hover:bg-emerald-700"
              >
                {submitting ? 'Creating...' : 'Create Closed Financing'}
              </Button>
              <Button
                variant="secondary"
                onClick={() => {
                  setShowAddClosedFinancingModal(false);
                  setSelectedFlag(null);
                }}
                disabled={submitting}
              >
                Cancel
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
