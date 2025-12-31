'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';

interface Submitter {
  id: number;
  username: string;
  email: string;
}

interface PendingCompany {
  id: number;
  name: string;
  website_url: string;
  presentation: string;
  company_size: string;
  industry: string;
  location: string;
  contact_email: string;
  brief_description: string;
  created_at: string;
  submitter: Submitter;
}

interface PendingResponse {
  companies: PendingCompany[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

export default function PendingCompaniesPage() {
  const router = useRouter();
  const { accessToken, user } = useAuth();
  const [companies, setCompanies] = useState<PendingCompany[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [expandedCompany, setExpandedCompany] = useState<number | null>(null);
  const [showRejectModal, setShowRejectModal] = useState<PendingCompany | null>(null);
  const [rejectionReason, setRejectionReason] = useState('');
  const [actionInProgress, setActionInProgress] = useState<number | null>(null);

  useEffect(() => {
    if (!accessToken || !user?.is_superuser) {
      router.push('/admin/companies');
      return;
    }
    fetchPendingCompanies();
  }, [accessToken, user, page]);

  const fetchPendingCompanies = async () => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await fetch(`/api/companies/pending/?page=${page}&limit=20`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
        },
      });

      if (!response.ok) {
        if (response.status === 403) {
          setError('You do not have permission to view pending companies.');
          return;
        }
        throw new Error('Failed to fetch pending companies');
      }

      const data: PendingResponse = await response.json();
      setCompanies(data.companies);
      setTotal(data.total);
      setTotalPages(data.total_pages);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load pending companies');
    } finally {
      setIsLoading(false);
    }
  };

  const handleApprove = async (company: PendingCompany) => {
    if (!confirm(`Approve ${company.name}? This will make it visible to all users.`)) {
      return;
    }

    setActionInProgress(company.id);
    try {
      const response = await fetch(`/api/companies/${company.id}/approve/`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
        },
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || 'Failed to approve company');
      }

      // Remove from list
      setCompanies(prev => prev.filter(c => c.id !== company.id));
      setTotal(prev => prev - 1);

      // Show success (optional: add toast notification)
      alert(`${company.name} has been approved!`);
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to approve company');
    } finally {
      setActionInProgress(null);
    }
  };

  const handleReject = async () => {
    if (!showRejectModal) return;

    setActionInProgress(showRejectModal.id);
    try {
      const response = await fetch(`/api/companies/${showRejectModal.id}/reject/`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`,
        },
        body: JSON.stringify({ reason: rejectionReason }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || 'Failed to reject company');
      }

      // Remove from list
      setCompanies(prev => prev.filter(c => c.id !== showRejectModal.id));
      setTotal(prev => prev - 1);
      setShowRejectModal(null);
      setRejectionReason('');

      alert(`${showRejectModal.name} has been rejected.`);
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to reject company');
    } finally {
      setActionInProgress(null);
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (!user?.is_superuser) {
    return null;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-100">Pending Company Submissions</h2>
          <p className="text-slate-400 mt-1">
            Review and approve user-submitted companies
          </p>
        </div>
        <Link
          href="/admin/companies"
          className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-200 rounded-lg transition-colors flex items-center gap-2 text-sm"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Back to Admin
        </Link>
      </div>

      {error && (
        <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400">
          {error}
        </div>
      )}

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <svg className="animate-spin w-8 h-8 text-gold-500" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
        </div>
      ) : companies.length === 0 ? (
        <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-12 text-center">
          <svg className="w-16 h-16 text-slate-600 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <p className="text-slate-400 text-lg">No pending company submissions</p>
        </div>
      ) : (
        <>
          <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4 mb-4">
            <p className="text-slate-300">
              <span className="font-semibold text-gold-400">{total}</span> pending {total === 1 ? 'submission' : 'submissions'}
            </p>
          </div>

          <div className="space-y-4">
            {companies.map((company) => (
              <div key={company.id} className="bg-slate-800/50 border border-slate-700 rounded-lg overflow-hidden">
                <div className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <h3 className="text-xl font-bold text-slate-100 mb-2">{company.name}</h3>
                      <div className="flex flex-wrap gap-2 mb-3">
                        <span className="px-2 py-1 bg-slate-700 text-slate-300 text-xs rounded">
                          {company.company_size}
                        </span>
                        <span className="px-2 py-1 bg-blue-500/20 text-blue-400 text-xs rounded">
                          {company.industry}
                        </span>
                        <span className="px-2 py-1 bg-purple-500/20 text-purple-400 text-xs rounded">
                          {company.location}
                        </span>
                      </div>
                      <p className="text-slate-400 text-sm mb-2">
                        Submitted by <strong className="text-slate-300">{company.submitter.username}</strong> ({company.submitter.email}) on {formatDate(company.created_at)}
                      </p>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                    <div>
                      <label className="text-xs text-slate-500 uppercase tracking-wider">Website URL</label>
                      {company.website_url ? (
                        <a href={company.website_url} target="_blank" rel="noopener noreferrer" className="text-gold-400 hover:text-gold-300 flex items-center gap-1">
                          {company.website_url}
                          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                          </svg>
                        </a>
                      ) : (
                        <p className="text-slate-500 italic">Not provided</p>
                      )}
                    </div>
                    <div>
                      <label className="text-xs text-slate-500 uppercase tracking-wider">Contact Email</label>
                      <a href={`mailto:${company.contact_email}`} className="text-gold-400 hover:text-gold-300">
                        {company.contact_email}
                      </a>
                    </div>
                  </div>

                  <div className="mb-4">
                    <label className="text-xs text-slate-500 uppercase tracking-wider">Brief Description</label>
                    <p className="text-slate-300 mt-1">{company.brief_description}</p>
                  </div>

                  {company.presentation && (
                    <div className="mb-4">
                      <button
                        onClick={() => setExpandedCompany(expandedCompany === company.id ? null : company.id)}
                        className="text-gold-400 hover:text-gold-300 text-sm flex items-center gap-1"
                      >
                        {expandedCompany === company.id ? 'Hide' : 'Show'} Full Presentation
                        <svg className={`w-4 h-4 transition-transform ${expandedCompany === company.id ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                      </button>
                      {expandedCompany === company.id && (
                        <div className="mt-2 p-4 bg-slate-900/50 rounded border border-slate-700">
                          <p className="text-slate-300 whitespace-pre-wrap">{company.presentation}</p>
                        </div>
                      )}
                    </div>
                  )}

                  <div className="flex justify-end gap-3 pt-4 border-t border-slate-700">
                    <button
                      onClick={() => setShowRejectModal(company)}
                      disabled={actionInProgress === company.id}
                      className="px-4 py-2 border border-red-500/50 text-red-400 hover:bg-red-500/10 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Reject
                    </button>
                    <button
                      onClick={() => handleApprove(company)}
                      disabled={actionInProgress === company.id}
                      className="px-4 py-2 bg-emerald-500 hover:bg-emerald-600 text-white font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                    >
                      {actionInProgress === company.id ? (
                        <>
                          <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                          </svg>
                          Processing...
                        </>
                      ) : (
                        <>
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                          </svg>
                          Approve
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2 pt-4">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-200 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Previous
              </button>
              <span className="text-slate-400">
                Page {page} of {totalPages}
              </span>
              <button
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-200 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
              </button>
            </div>
          )}
        </>
      )}

      {/* Reject Modal */}
      {showRejectModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 max-w-md w-full">
            <h3 className="text-xl font-bold text-slate-100 mb-4">Reject {showRejectModal.name}?</h3>
            <p className="text-slate-400 mb-4">
              Optionally provide a reason for rejection (this will be stored for reference):
            </p>
            <textarea
              value={rejectionReason}
              onChange={(e) => setRejectionReason(e.target.value)}
              placeholder="Reason for rejection (optional)..."
              rows={4}
              className="w-full px-4 py-2 bg-slate-900 border border-slate-600 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-gold-500 mb-4"
            />
            <p className="text-xs text-slate-500 mb-4">{rejectionReason.length}/500 characters</p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => {
                  setShowRejectModal(null);
                  setRejectionReason('');
                }}
                className="px-4 py-2 border border-slate-600 text-slate-300 hover:bg-slate-700 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleReject}
                disabled={actionInProgress !== null}
                className="px-4 py-2 bg-red-500 hover:bg-red-600 text-white font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {actionInProgress === showRejectModal.id ? 'Rejecting...' : 'Confirm Rejection'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
