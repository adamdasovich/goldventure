'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/Button';
import { CreateFinancingModal } from '@/components/company/CreateFinancingModal';

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
                      onClick={() => handleOpenFinancingModal(flag)}
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
    </div>
  );
}
