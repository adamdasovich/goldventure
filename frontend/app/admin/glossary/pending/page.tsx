'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';

interface GlossarySubmission {
  id: number;
  term: string;
  definition: string;
  category: string;
  keywords: string;
  related_links: { text: string; url: string }[];
  submitted_by: number;
  submitted_by_username: string;
  submitted_at: string;
  status: 'pending' | 'approved' | 'rejected';
  status_display: string;
}

export default function PendingGlossaryTermsPage() {
  const router = useRouter();
  const [submissions, setSubmissions] = useState<GlossarySubmission[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<number | null>(null);
  const [expandedId, setExpandedId] = useState<number | null>(null);

  const categories = [
    { value: 'reporting', label: 'Reporting & Standards' },
    { value: 'geology', label: 'Geology & Resources' },
    { value: 'finance', label: 'Finance & Investment' },
    { value: 'regulatory', label: 'Regulatory & Legal' },
    { value: 'operations', label: 'Mining Operations' },
    { value: 'general', label: 'General Terms' }
  ];

  const getCategoryLabel = (category: string) => {
    return categories.find(c => c.value === category)?.label || category;
  };

  useEffect(() => {
    fetchPendingSubmissions();
  }, []);

  const fetchPendingSubmissions = async () => {
    try {
      const token = localStorage.getItem('accessToken');
      if (!token) {
        setError('Unauthorized: Please log in');
        setIsLoading(false);
        router.push('/');
        return;
      }

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/glossary/submissions/pending/`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setSubmissions(data);
        setError(null);
      } else if (response.status === 403) {
        setError('Unauthorized: Superuser access required');
        router.push('/');
      } else {
        setError('Failed to load pending submissions');
      }
    } catch (err) {
      console.error('Error fetching pending submissions:', err);
      setError('An error occurred while loading submissions');
    } finally {
      setIsLoading(false);
    }
  };

  const handleApprove = async (submissionId: number) => {
    if (!confirm('Approve this glossary term submission?')) return;

    setActionLoading(submissionId);
    try {
      const token = localStorage.getItem('accessToken');
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/glossary/submissions/${submissionId}/approve/`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );

      if (response.ok) {
        // Remove from pending list
        setSubmissions(prev => prev.filter(s => s.id !== submissionId));
        alert('Term approved successfully!');
      } else {
        const errorData = await response.json();
        alert(`Failed to approve: ${errorData.error || 'Unknown error'}`);
      }
    } catch (err) {
      console.error('Error approving submission:', err);
      alert('An error occurred while approving');
    } finally {
      setActionLoading(null);
    }
  };

  const handleReject = async (submissionId: number) => {
    const reason = prompt('Enter rejection reason (optional):');
    if (reason === null) return; // User cancelled

    setActionLoading(submissionId);
    try {
      const token = localStorage.getItem('accessToken');
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/glossary/submissions/${submissionId}/reject/`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ reason: reason || 'No reason provided' })
        }
      );

      if (response.ok) {
        // Remove from pending list
        setSubmissions(prev => prev.filter(s => s.id !== submissionId));
        alert('Term rejected successfully');
      } else {
        const errorData = await response.json();
        alert(`Failed to reject: ${errorData.error || 'Unknown error'}`);
      }
    } catch (err) {
      console.error('Error rejecting submission:', err);
      alert('An error occurred while rejecting');
    } finally {
      setActionLoading(null);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-900 p-8">
        <div className="max-w-7xl mx-auto">
          <p className="text-slate-300">Loading pending submissions...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-slate-900 p-8">
        <div className="max-w-7xl mx-auto">
          <Card variant="glass-card">
            <CardHeader>
              <CardTitle className="text-red-400">Error</CardTitle>
              <CardDescription>{error}</CardDescription>
            </CardHeader>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900">
      {/* Header */}
      <div className="bg-gradient-to-b from-slate-800 to-slate-900 border-b border-slate-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold text-gradient-gold mb-2">
                Pending Glossary Terms
              </h1>
              <p className="text-slate-300">
                Review and approve user-submitted glossary term definitions
              </p>
            </div>
            <Button
              variant="ghost"
              onClick={() => router.push('/admin/companies')}
            >
              ← Back to Admin
            </Button>
          </div>
        </div>
      </div>

      {/* Submissions List */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {submissions.length === 0 ? (
          <Card variant="glass-card">
            <CardHeader>
              <CardTitle>No Pending Submissions</CardTitle>
              <CardDescription>
                There are no glossary terms waiting for review.
              </CardDescription>
            </CardHeader>
          </Card>
        ) : (
          <div className="space-y-6">
            <div className="flex items-center justify-between mb-4">
              <p className="text-slate-400">
                {submissions.length} submission{submissions.length !== 1 ? 's' : ''} pending review
              </p>
            </div>

            {submissions.map((submission) => (
              <Card key={submission.id} variant="glass-card">
                <CardHeader>
                  <div className="space-y-4">
                    {/* Header Row */}
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <CardTitle className="text-2xl text-gold-400 mb-2">
                          {submission.term}
                        </CardTitle>
                        <div className="flex items-center gap-3 text-sm text-slate-400">
                          <span>Submitted by: {submission.submitted_by_username}</span>
                          <span>•</span>
                          <span>{new Date(submission.submitted_at).toLocaleDateString()}</span>
                          <span>•</span>
                          <span className="px-2 py-1 rounded bg-slate-700/50">
                            {getCategoryLabel(submission.category)}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Definition */}
                    <div className="bg-slate-800/50 rounded-lg p-4">
                      <h3 className="text-sm font-medium text-slate-300 mb-2">Definition:</h3>
                      <p className="text-slate-200 leading-relaxed">
                        {submission.definition}
                      </p>
                    </div>

                    {/* Keywords */}
                    {submission.keywords && (
                      <div>
                        <h3 className="text-sm font-medium text-slate-300 mb-2">Keywords:</h3>
                        <p className="text-slate-400 text-sm">{submission.keywords}</p>
                      </div>
                    )}

                    {/* Related Links */}
                    {submission.related_links && submission.related_links.length > 0 && (
                      <div>
                        <h3 className="text-sm font-medium text-slate-300 mb-2">Related Links:</h3>
                        <div className="flex flex-wrap gap-2">
                          {submission.related_links.map((link, idx) => (
                            <a
                              key={idx}
                              href={link.url}
                              className="text-sm text-gold-400 hover:text-gold-300 underline"
                              target="_blank"
                              rel="noopener noreferrer"
                            >
                              {link.text} →
                            </a>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Action Buttons */}
                    <div className="flex items-center gap-3 pt-4 border-t border-slate-700">
                      <Button
                        variant="primary"
                        size="sm"
                        onClick={() => handleApprove(submission.id)}
                        disabled={actionLoading === submission.id}
                      >
                        {actionLoading === submission.id ? 'Processing...' : '✓ Approve'}
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleReject(submission.id)}
                        disabled={actionLoading === submission.id}
                        className="text-red-400 hover:text-red-300 hover:bg-red-500/10"
                      >
                        ✕ Reject
                      </Button>
                    </div>
                  </div>
                </CardHeader>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
