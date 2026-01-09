'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/Button';

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

interface FinancingFormData {
  financing_type: string;
  status: string;
  announced_date: string;
  amount_raised_usd: string;
  price_per_share: string;
  shares_issued: string;
  has_warrants: boolean;
  warrant_strike_price: string;
  use_of_proceeds: string;
  lead_agent: string;
  notes: string;
  review_notes: string;
}

export default function NewsFlagsPage() {
  const { user } = useAuth();
  const [flags, setFlags] = useState<NewsReleaseFlag[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('pending');
  const [selectedFlag, setSelectedFlag] = useState<NewsReleaseFlag | null>(null);
  const [showFinancingForm, setShowFinancingForm] = useState(false);
  const [showDismissModal, setShowDismissModal] = useState(false);
  const [dismissNotes, setDismissNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const [financingForm, setFinancingForm] = useState<FinancingFormData>({
    financing_type: 'private_placement',
    status: 'announced',
    announced_date: '',
    amount_raised_usd: '',
    price_per_share: '',
    shares_issued: '',
    has_warrants: false,
    warrant_strike_price: '',
    use_of_proceeds: '',
    lead_agent: '',
    notes: '',
    review_notes: 'Financing created from flagged news release'
  });

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

  const handleOpenFinancingForm = (flag: NewsReleaseFlag) => {
    setSelectedFlag(flag);
    setFinancingForm({
      ...financingForm,
      announced_date: flag.news_date
    });
    setShowFinancingForm(true);
  };

  const handleCreateFinancing = async () => {
    if (!selectedFlag) return;

    try {
      setSubmitting(true);
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/news-flags/${selectedFlag.id}/create-financing/`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
          },
          body: JSON.stringify(financingForm)
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to create financing');
      }

      alert('Financing created successfully!');
      setShowFinancingForm(false);
      setSelectedFlag(null);
      fetchFlags();
    } catch (err: any) {
      alert(`Error: ${err.message}`);
    } finally {
      setSubmitting(false);
    }
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
                  <div className="flex gap-2">
                    <Button
                      variant="primary"
                      onClick={() => handleOpenFinancingForm(flag)}
                      size="sm"
                    >
                      Create Financing
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

      {/* Financing Creation Modal */}
      {showFinancingForm && selectedFlag && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-slate-800 rounded-lg p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <h2 className="text-xl font-bold text-slate-100 mb-4">
              Create Financing Record
            </h2>
            <p className="text-slate-400 mb-6">
              {selectedFlag.company_name} - {selectedFlag.news_title}
            </p>

            <div className="space-y-4">
              {/* Financing Type */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">
                  Financing Type
                </label>
                <select
                  value={financingForm.financing_type}
                  onChange={(e) => setFinancingForm({ ...financingForm, financing_type: e.target.value })}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-100"
                >
                  <option value="private_placement">Private Placement</option>
                  <option value="bought_deal">Bought Deal</option>
                  <option value="rights_offering">Rights Offering</option>
                  <option value="flow_through">Flow-Through Shares</option>
                  <option value="warrant_exercise">Warrant Exercise</option>
                  <option value="debt">Debt Financing</option>
                  <option value="royalty_stream">Royalty/Stream</option>
                  <option value="other">Other</option>
                </select>
              </div>

              {/* Status */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">
                  Status
                </label>
                <select
                  value={financingForm.status}
                  onChange={(e) => setFinancingForm({ ...financingForm, status: e.target.value })}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-100"
                >
                  <option value="announced">Announced</option>
                  <option value="closing">Closing</option>
                  <option value="closed">Closed</option>
                  <option value="cancelled">Cancelled</option>
                </select>
              </div>

              {/* Amount Raised */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">
                  Amount Raised (CAD) *
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={financingForm.amount_raised_usd}
                  onChange={(e) => setFinancingForm({ ...financingForm, amount_raised_usd: e.target.value })}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-100"
                  required
                />
              </div>

              {/* Price Per Share */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">
                  Price Per Share
                </label>
                <input
                  type="number"
                  step="0.0001"
                  value={financingForm.price_per_share}
                  onChange={(e) => setFinancingForm({ ...financingForm, price_per_share: e.target.value })}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-100"
                />
              </div>

              {/* Shares Issued */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">
                  Shares Issued
                </label>
                <input
                  type="number"
                  value={financingForm.shares_issued}
                  onChange={(e) => setFinancingForm({ ...financingForm, shares_issued: e.target.value })}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-100"
                />
              </div>

              {/* Has Warrants */}
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="has_warrants"
                  checked={financingForm.has_warrants}
                  onChange={(e) => setFinancingForm({ ...financingForm, has_warrants: e.target.checked })}
                  className="w-4 h-4"
                />
                <label htmlFor="has_warrants" className="text-sm text-slate-300">
                  Includes Warrants
                </label>
              </div>

              {/* Warrant Strike Price */}
              {financingForm.has_warrants && (
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1">
                    Warrant Strike Price
                  </label>
                  <input
                    type="number"
                    step="0.0001"
                    value={financingForm.warrant_strike_price}
                    onChange={(e) => setFinancingForm({ ...financingForm, warrant_strike_price: e.target.value })}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-100"
                  />
                </div>
              )}

              {/* Lead Agent */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">
                  Lead Agent/Broker
                </label>
                <input
                  type="text"
                  value={financingForm.lead_agent}
                  onChange={(e) => setFinancingForm({ ...financingForm, lead_agent: e.target.value })}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-100"
                />
              </div>

              {/* Use of Proceeds */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">
                  Use of Proceeds
                </label>
                <textarea
                  value={financingForm.use_of_proceeds}
                  onChange={(e) => setFinancingForm({ ...financingForm, use_of_proceeds: e.target.value })}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-100"
                  rows={3}
                />
              </div>

              {/* Notes */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">
                  Notes
                </label>
                <textarea
                  value={financingForm.notes}
                  onChange={(e) => setFinancingForm({ ...financingForm, notes: e.target.value })}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-100"
                  rows={2}
                />
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <Button
                variant="primary"
                onClick={handleCreateFinancing}
                disabled={submitting || !financingForm.amount_raised_usd}
                className="flex-1"
              >
                {submitting ? 'Creating...' : 'Create Financing'}
              </Button>
              <Button
                variant="secondary"
                onClick={() => {
                  setShowFinancingForm(false);
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
    </div>
  );
}
