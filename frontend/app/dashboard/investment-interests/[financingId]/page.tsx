'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import LogoMono from '@/components/LogoMono';
import { useAuth } from '@/contexts/AuthContext';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

interface InvestmentInterest {
  id: number;
  user_name: string;
  user_email: string;
  shares_requested: number;
  price_per_share: string;
  investment_amount: string;
  status: string;
  status_display: string;
  contact_email: string;
  contact_phone: string;
  is_accredited_investor: boolean;
  term_sheet_confirmed: boolean;
  subscription_agreement_confirmed: boolean;
  risk_acknowledged: boolean;
  created_at: string;
  updated_at: string;
}

interface FinancingDetails {
  id: number;
  company_name: string;
  company_id: number;
  financing_type: string;
  status: string;
  announced_date: string;
  closing_date: string;
  amount_raised_usd: string;
  price_per_share: string;
  shares_issued: number;
}

interface AggregateData {
  total_interest_count: number;
  total_shares_requested: number;
  total_amount_interested: string;
  percentage_filled: string;
}

export default function InvestmentInterestDetailPage() {
  const params = useParams();
  const router = useRouter();
  const financingId = params.financingId as string;
  const { user, accessToken, isLoading: authLoading } = useAuth();

  const [financing, setFinancing] = useState<FinancingDetails | null>(null);
  const [interests, setInterests] = useState<InvestmentInterest[]>([]);
  const [aggregate, setAggregate] = useState<AggregateData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [updatingStatus, setUpdatingStatus] = useState<number | null>(null);

  useEffect(() => {
    if (!authLoading && !user?.is_superuser) {
      router.push('/dashboard');
    }
  }, [user, authLoading, router]);

  useEffect(() => {
    if (accessToken && financingId && user?.is_superuser) {
      fetchData();
    }
  }, [accessToken, financingId, user]);

  const fetchData = async () => {
    setLoading(true);
    try {
      // Fetch financing details
      const financingRes = await fetch(`${API_URL}/financings/${financingId}/`, {
        headers: { 'Authorization': `Bearer ${accessToken}` },
      });
      if (financingRes.ok) {
        const data = await financingRes.json();
        setFinancing(data);
      }

      // Fetch investment interests list
      const interestsRes = await fetch(`${API_URL}/investment-interest/list/${financingId}/`, {
        headers: { 'Authorization': `Bearer ${accessToken}` },
      });
      if (interestsRes.ok) {
        const data = await interestsRes.json();
        setInterests(data.results || data);
      }

      // Fetch aggregate data
      const aggregateRes = await fetch(`${API_URL}/investment-interest/aggregate/${financingId}/`);
      if (aggregateRes.ok) {
        const data = await aggregateRes.json();
        setAggregate(data);
      }
    } catch (err) {
      console.error('Failed to fetch data:', err);
      setError('Failed to load investment interest data');
    } finally {
      setLoading(false);
    }
  };

  const handleStatusUpdate = async (interestId: number, newStatus: string) => {
    setUpdatingStatus(interestId);
    try {
      const res = await fetch(`${API_URL}/investment-interest/${interestId}/status/`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ status: newStatus }),
      });
      if (res.ok) {
        // Refresh the list
        await fetchData();
      } else {
        const data = await res.json();
        alert(data.error || 'Failed to update status');
      }
    } catch (err) {
      console.error('Failed to update status:', err);
      alert('Failed to update status');
    } finally {
      setUpdatingStatus(null);
    }
  };

  const formatCurrency = (amount: string | number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(Number(amount));
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

  const getStatusBadgeVariant = (status: string): 'gold' | 'copper' | 'slate' => {
    switch (status) {
      case 'pending': return 'gold';
      case 'qualified': return 'copper';
      case 'contacted': return 'copper';
      case 'converted': return 'slate';
      case 'withdrawn': return 'slate';
      case 'rejected': return 'slate';
      default: return 'slate';
    }
  };

  if (authLoading || loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-gold-500"></div>
      </div>
    );
  }

  if (!user?.is_superuser) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gradient-dark">
      {/* Navigation */}
      <nav className="glass-nav sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-24">
            <div className="flex items-center space-x-3 cursor-pointer" onClick={() => router.push('/')}>
              <LogoMono className="h-18" />
            </div>
            <div className="flex items-center space-x-4">
              <Badge variant="copper">Superuser</Badge>
              <Button variant="ghost" size="sm" onClick={() => router.push('/dashboard')}>
                Back to Dashboard
              </Button>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Page Header */}
        <div className="mb-8">
          <Button variant="ghost" size="sm" onClick={() => router.push('/dashboard')} className="mb-4">
            <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to Dashboard
          </Button>
          <h1 className="text-3xl font-bold text-gradient-gold">Investment Interest Details</h1>
          {financing && (
            <p className="text-slate-400 mt-2">
              {financing.company_name} - {financing.financing_type.replace('_', ' ').toUpperCase()}
            </p>
          )}
        </div>

        {error ? (
          <Card variant="glass-card">
            <CardContent className="py-8 text-center">
              <p className="text-red-400">{error}</p>
              <Button variant="primary" className="mt-4" onClick={fetchData}>
                Try Again
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-6">
            {/* Financing Summary */}
            {financing && (
              <Card variant="glass-card">
                <CardHeader>
                  <CardTitle className="text-gold-400">Financing Summary</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="bg-slate-800/50 rounded-lg p-4">
                      <p className="text-sm text-slate-400">Target Amount</p>
                      <p className="text-xl font-bold text-white">
                        {formatCurrency(financing.amount_raised_usd || 0)}
                      </p>
                    </div>
                    <div className="bg-slate-800/50 rounded-lg p-4">
                      <p className="text-sm text-slate-400">Price Per Share</p>
                      <p className="text-xl font-bold text-white">
                        ${Number(financing.price_per_share || 0).toFixed(4)}
                      </p>
                    </div>
                    <div className="bg-slate-800/50 rounded-lg p-4">
                      <p className="text-sm text-slate-400">Status</p>
                      <Badge variant={financing.status === 'closing' ? 'gold' : 'slate'}>
                        {financing.status.toUpperCase()}
                      </Badge>
                    </div>
                    <div className="bg-slate-800/50 rounded-lg p-4">
                      <p className="text-sm text-slate-400">Closing Date</p>
                      <p className="text-xl font-bold text-white">
                        {financing.closing_date || 'TBD'}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Aggregate Interest Data */}
            {aggregate && (
              <Card variant="glass-card">
                <CardHeader>
                  <CardTitle className="text-gold-400">Interest Summary</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="bg-slate-800/50 rounded-lg p-4 text-center">
                      <p className="text-3xl font-bold text-gold-400">{aggregate.total_interest_count}</p>
                      <p className="text-sm text-slate-400">Investors</p>
                    </div>
                    <div className="bg-slate-800/50 rounded-lg p-4 text-center">
                      <p className="text-3xl font-bold text-white">
                        {aggregate.total_shares_requested.toLocaleString()}
                      </p>
                      <p className="text-sm text-slate-400">Shares Requested</p>
                    </div>
                    <div className="bg-slate-800/50 rounded-lg p-4 text-center">
                      <p className="text-3xl font-bold text-white">
                        {formatCurrency(aggregate.total_amount_interested)}
                      </p>
                      <p className="text-sm text-slate-400">Total Interest</p>
                    </div>
                    <div className="bg-slate-800/50 rounded-lg p-4 text-center">
                      <p className="text-3xl font-bold text-green-400">
                        {Number(aggregate.percentage_filled).toFixed(1)}%
                      </p>
                      <p className="text-sm text-slate-400">Filled</p>
                    </div>
                  </div>

                  {/* Progress Bar */}
                  <div className="mt-6">
                    <div className="h-4 bg-slate-700 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-gold-500 to-copper-500 rounded-full transition-all duration-500"
                        style={{ width: `${Math.min(Number(aggregate.percentage_filled), 100)}%` }}
                      ></div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Investor List */}
            <Card variant="glass-card">
              <CardHeader>
                <CardTitle className="text-gold-400">Investor Details</CardTitle>
                <CardDescription>
                  Complete list of investors who have expressed interest
                </CardDescription>
              </CardHeader>
              <CardContent>
                {interests.length === 0 ? (
                  <p className="text-slate-400 text-center py-8">No investment interests yet</p>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b border-slate-700">
                          <th className="text-left py-3 px-4 text-slate-400 font-medium">Investor</th>
                          <th className="text-left py-3 px-4 text-slate-400 font-medium">Contact</th>
                          <th className="text-right py-3 px-4 text-slate-400 font-medium">Shares</th>
                          <th className="text-right py-3 px-4 text-slate-400 font-medium">Amount</th>
                          <th className="text-center py-3 px-4 text-slate-400 font-medium">Status</th>
                          <th className="text-center py-3 px-4 text-slate-400 font-medium">Confirmations</th>
                          <th className="text-left py-3 px-4 text-slate-400 font-medium">Date</th>
                          <th className="text-center py-3 px-4 text-slate-400 font-medium">Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {interests.map((interest) => (
                          <tr key={interest.id} className="border-b border-slate-800 hover:bg-slate-800/30">
                            <td className="py-4 px-4">
                              <p className="text-white font-medium">{interest.user_name}</p>
                              <p className="text-sm text-slate-400">{interest.user_email}</p>
                            </td>
                            <td className="py-4 px-4">
                              <p className="text-white text-sm">{interest.contact_email}</p>
                              <p className="text-sm text-slate-400">{interest.contact_phone || '-'}</p>
                            </td>
                            <td className="py-4 px-4 text-right">
                              <p className="text-white font-medium">
                                {interest.shares_requested.toLocaleString()}
                              </p>
                            </td>
                            <td className="py-4 px-4 text-right">
                              <p className="text-gold-400 font-medium">
                                {formatCurrency(interest.investment_amount)}
                              </p>
                            </td>
                            <td className="py-4 px-4 text-center">
                              <Badge variant={getStatusBadgeVariant(interest.status)}>
                                {interest.status_display || interest.status}
                              </Badge>
                            </td>
                            <td className="py-4 px-4">
                              <div className="flex justify-center gap-1">
                                {interest.is_accredited_investor && (
                                  <span title="Accredited Investor" className="text-green-400">
                                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                                    </svg>
                                  </span>
                                )}
                                {interest.term_sheet_confirmed && (
                                  <span title="Term Sheet Confirmed" className="text-blue-400">
                                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                                      <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" />
                                    </svg>
                                  </span>
                                )}
                                {interest.risk_acknowledged && (
                                  <span title="Risk Acknowledged" className="text-yellow-400">
                                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                                      <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                                    </svg>
                                  </span>
                                )}
                              </div>
                            </td>
                            <td className="py-4 px-4">
                              <p className="text-sm text-slate-400">{formatDate(interest.created_at)}</p>
                            </td>
                            <td className="py-4 px-4">
                              <div className="flex justify-center gap-2">
                                {interest.status === 'pending' && (
                                  <>
                                    <Button
                                      variant="ghost"
                                      size="sm"
                                      onClick={() => handleStatusUpdate(interest.id, 'qualified')}
                                      disabled={updatingStatus === interest.id}
                                      className="text-green-400 hover:text-green-300"
                                    >
                                      Qualify
                                    </Button>
                                    <Button
                                      variant="ghost"
                                      size="sm"
                                      onClick={() => handleStatusUpdate(interest.id, 'rejected')}
                                      disabled={updatingStatus === interest.id}
                                      className="text-red-400 hover:text-red-300"
                                    >
                                      Reject
                                    </Button>
                                  </>
                                )}
                                {interest.status === 'qualified' && (
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => handleStatusUpdate(interest.id, 'contacted')}
                                    disabled={updatingStatus === interest.id}
                                    className="text-blue-400 hover:text-blue-300"
                                  >
                                    Mark Contacted
                                  </Button>
                                )}
                                {interest.status === 'contacted' && (
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => handleStatusUpdate(interest.id, 'converted')}
                                    disabled={updatingStatus === interest.id}
                                    className="text-gold-400 hover:text-gold-300"
                                  >
                                    Convert
                                  </Button>
                                )}
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Export Button */}
            <div className="flex justify-end">
              <Button
                variant="primary"
                onClick={() => window.open(`${API_URL}/investment-interest/export/${financingId}/?format=csv`, '_blank')}
              >
                <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                Export to CSV
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
