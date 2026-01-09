'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import LogoMono from '@/components/LogoMono';
import { LoginModal, RegisterModal } from '@/components/auth';
import { InvestmentInterestModal } from '@/components/financing';
import { useAuth } from '@/contexts/AuthContext';

interface Company {
  id: number;
  name: string;
  ticker_symbol: string;
  exchange: string;
  logo_url?: string;
}

interface Financing {
  id: number;
  financing_type: string;
  financing_type_display: string;
  status: string;
  status_display: string;
  announced_date: string;
  closing_date: string | null;
  amount_raised_usd: number;
  price_per_share: number | null;
  shares_issued: number | null;
  has_warrants: boolean;
  warrant_strike_price: number | null;
  warrant_expiry_date: string | null;
  use_of_proceeds: string;
  lead_agent: string;
  press_release_url: string;
  notes: string;
}

interface FinancingAggregate {
  total_subscriptions: number;
  total_subscribers: number;
  total_committed_amount: number;
  total_funded_amount: number;
  total_shares_allocated: number;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

export default function CompanyFinancingPage() {
  const params = useParams();
  const router = useRouter();
  const companyId = params.id as string;
  const { user, logout } = useAuth();
  const accessToken = typeof window !== 'undefined' ? localStorage.getItem('accessToken') : null;

  const [company, setCompany] = useState<Company | null>(null);
  const [financings, setFinancings] = useState<Financing[]>([]);
  const [selectedFinancing, setSelectedFinancing] = useState<Financing | null>(null);
  const [aggregate, setAggregate] = useState<FinancingAggregate | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showLogin, setShowLogin] = useState(false);
  const [showRegister, setShowRegister] = useState(false);
  const [showInterestModal, setShowInterestModal] = useState(false);
  const [interestStatus, setInterestStatus] = useState<{
    has_interest: boolean;
    interest_id: number | null;
    status: string | null;
    shares_requested: number | null;
    investment_amount: string | null;
  } | null>(null);
  const [interestAggregate, setInterestAggregate] = useState<{
    total_interest_count: number;
    total_shares_requested: number;
    total_amount_interested: string;
    percentage_filled: string;
  } | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editAmount, setEditAmount] = useState('');
  const [isUpdating, setIsUpdating] = useState(false);
  const [isCancelling, setIsCancelling] = useState(false);

  useEffect(() => {
    if (!user) {
      // Redirect non-logged-in users to login
      setShowLogin(true);
    }
  }, [user]);

  useEffect(() => {
    if (companyId) {
      fetchCompanyAndFinancings();
    }
  }, [companyId]);

  const fetchCompanyAndFinancings = async () => {
    try {
      setLoading(true);

      // Fetch company details
      const companyRes = await fetch(`${API_URL}/companies/${companyId}/`);
      if (!companyRes.ok) throw new Error('Failed to fetch company');
      const companyData = await companyRes.json();
      setCompany(companyData);

      // Fetch company financings
      const financingsRes = await fetch(`${API_URL}/financings/?company=${companyId}`);
      if (!financingsRes.ok) throw new Error('Failed to fetch financings');
      const financingsData = await financingsRes.json();
      const financingsList = financingsData.results || financingsData;
      setFinancings(financingsList);

      // Select the first active financing if available
      const activeFinancing = financingsList.find(
        (f: Financing) => f.status === 'announced' || f.status === 'closing'
      );
      if (activeFinancing) {
        setSelectedFinancing(activeFinancing);
        fetchFinancingAggregate(activeFinancing.id);
      } else if (financingsList.length > 0) {
        setSelectedFinancing(financingsList[0]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load financing data');
    } finally {
      setLoading(false);
    }
  };

  const fetchFinancingAggregate = async (financingId: number) => {
    try {
      const headers: Record<string, string> = {};
      if (accessToken) {
        headers['Authorization'] = `Bearer ${accessToken}`;
      }
      const res = await fetch(`${API_URL}/investments/aggregates/?financing=${financingId}`, {
        headers,
      });
      if (res.ok) {
        const data = await res.json();
        const aggregates = data.results || data;
        if (aggregates.length > 0) {
          setAggregate(aggregates[0]);
        }
      }
    } catch (err) {
      console.error('Failed to fetch aggregate:', err);
    }
  };

  const fetchMyInterestStatus = async (financingId: number) => {
    if (!accessToken) return;
    try {
      const res = await fetch(`${API_URL}/investment-interest/my-interest/${financingId}/`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
        },
      });
      if (res.ok) {
        const data = await res.json();
        setInterestStatus(data);
      }
    } catch (err) {
      console.error('Failed to fetch interest status:', err);
    }
  };

  const fetchInterestAggregate = async (financingId: number) => {
    try {
      const res = await fetch(`${API_URL}/investment-interest/aggregate/${financingId}/`);
      if (res.ok) {
        const data = await res.json();
        setInterestAggregate(data);
      }
    } catch (err) {
      console.error('Failed to fetch interest aggregate:', err);
    }
  };

  // Fetch interest data when financing is selected
  useEffect(() => {
    if (selectedFinancing) {
      fetchInterestAggregate(selectedFinancing.id);
      if (user && accessToken) {
        fetchMyInterestStatus(selectedFinancing.id);
      }
    }
  }, [selectedFinancing, user, accessToken]);

  const handleExpressInterest = async () => {
    if (!user || !selectedFinancing) {
      setShowLogin(true);
      return;
    }
    setShowInterestModal(true);
  };

  const handleInterestSuccess = () => {
    setShowInterestModal(false);
    if (selectedFinancing) {
      fetchMyInterestStatus(selectedFinancing.id);
      fetchInterestAggregate(selectedFinancing.id);
    }
  };

  const handleCancelInterest = async () => {
    if (!interestStatus?.interest_id || !accessToken) return;

    if (!confirm('Are you sure you want to cancel your interest in this financing?')) {
      return;
    }

    setIsCancelling(true);
    try {
      const res = await fetch(`${API_URL}/investment-interest/${interestStatus.interest_id}/withdraw/`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
        },
      });

      if (res.ok) {
        // Reset interest status
        setInterestStatus({
          has_interest: false,
          interest_id: null,
          status: null,
          shares_requested: null,
          investment_amount: null,
        });
        // Refresh aggregate
        if (selectedFinancing) {
          fetchInterestAggregate(selectedFinancing.id);
        }
      } else {
        const data = await res.json();
        alert(data.error || 'Failed to cancel interest');
      }
    } catch (err) {
      console.error('Failed to cancel interest:', err);
      alert('Failed to cancel interest');
    } finally {
      setIsCancelling(false);
    }
  };

  const handleStartEdit = () => {
    setEditAmount(interestStatus?.investment_amount || '');
    setIsEditing(true);
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
    setEditAmount('');
  };

  const handleUpdateInterest = async () => {
    if (!interestStatus?.interest_id || !accessToken || !selectedFinancing) return;

    const amount = parseFloat(editAmount);
    if (isNaN(amount) || amount <= 0) {
      alert('Please enter a valid amount');
      return;
    }

    // Calculate shares based on price per share
    const pricePerShare = selectedFinancing.price_per_share || 0;
    const sharesRequested = pricePerShare > 0 ? Math.floor(amount / pricePerShare) : 0;

    setIsUpdating(true);
    try {
      const res = await fetch(`${API_URL}/investment-interest/${interestStatus.interest_id}/update/`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          investment_amount: amount,
          shares_requested: sharesRequested,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        // Update local state
        setInterestStatus({
          ...interestStatus,
          shares_requested: data.shares_requested,
          investment_amount: data.investment_amount,
        });
        setIsEditing(false);
        // Refresh aggregate
        fetchInterestAggregate(selectedFinancing.id);
      } else {
        const data = await res.json();
        alert(data.error || 'Failed to update interest');
      }
    } catch (err) {
      console.error('Failed to update interest:', err);
      alert('Failed to update interest');
    } finally {
      setIsUpdating(false);
    }
  };

  const formatCurrency = (amount: number, currency: string = 'CAD') => {
    return new Intl.NumberFormat('en-CA', {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'long',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const getStatusBadgeVariant = (status: string): 'gold' | 'copper' | 'slate' => {
    switch (status) {
      case 'announced':
        return 'gold';
      case 'closing':
        return 'copper';
      default:
        return 'slate';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gold-400"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <Card variant="glass-card" className="max-w-md">
          <CardContent className="p-6 text-center">
            <div className="text-red-400 mb-4">{error}</div>
            <Button variant="primary" onClick={() => router.back()}>
              Go Back
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900">
      {/* Navigation */}
      <nav className="glass-nav sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <Link href="/" className="flex items-center space-x-3">
              <LogoMono className="h-10" />
            </Link>
            <div className="flex items-center space-x-4">
              <Button variant="ghost" size="sm" onClick={() => router.push('/companies')}>
                Companies
              </Button>
              <Button variant="ghost" size="sm" onClick={() => router.push('/financial-hub')}>
                Financial Hub
              </Button>
              {user ? (
                <div className="flex items-center space-x-3">
                  <span className="text-sm text-slate-300">
                    {user.full_name || user.username}
                  </span>
                  <Button variant="ghost" size="sm" onClick={logout}>
                    Logout
                  </Button>
                </div>
              ) : (
                <>
                  <Button variant="ghost" size="sm" onClick={() => setShowLogin(true)}>
                    Login
                  </Button>
                  <Button variant="primary" size="sm" onClick={() => setShowRegister(true)}>
                    Register
                  </Button>
                </>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* Auth Modals */}
      {showLogin && (
        <LoginModal
          onClose={() => setShowLogin(false)}
          onSwitchToRegister={() => {
            setShowLogin(false);
            setShowRegister(true);
          }}
        />
      )}
      {showRegister && (
        <RegisterModal
          onClose={() => setShowRegister(false)}
          onSwitchToLogin={() => {
            setShowRegister(false);
            setShowLogin(true);
          }}
        />
      )}

      {/* Investment Interest Modal */}
      {showInterestModal && selectedFinancing && company && (
        <InvestmentInterestModal
          financing={selectedFinancing}
          company={company}
          onClose={() => setShowInterestModal(false)}
          onSuccess={handleInterestSuccess}
        />
      )}

      {/* Company Header */}
      <section className="py-8 px-4 sm:px-6 lg:px-8 border-b border-slate-800">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center gap-4">
            {company?.logo_url ? (
              <img
                src={company.logo_url}
                alt={company.name}
                className="w-16 h-16 rounded-lg object-contain bg-white p-2"
              />
            ) : (
              <div className="w-16 h-16 rounded-lg bg-gradient-to-br from-gold-500/20 to-copper-500/20 flex items-center justify-center">
                <span className="text-2xl font-bold text-gold-400">
                  {company?.name.charAt(0)}
                </span>
              </div>
            )}
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-2xl font-bold text-white">{company?.name}</h1>
                <Badge variant="copper">
                  {company?.exchange}:{company?.ticker_symbol}
                </Badge>
              </div>
              <Link
                href={`/companies/${companyId}`}
                className="text-sm text-gold-400 hover:text-gold-300 transition-colors"
              >
                View Company Profile
              </Link>
            </div>
          </div>
        </div>
      </section>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {financings.length === 0 ? (
          <Card variant="glass-card">
            <CardContent className="p-12 text-center">
              <svg className="w-16 h-16 mx-auto text-slate-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <h2 className="text-xl font-semibold text-white mb-2">No Active Financing</h2>
              <p className="text-slate-400 mb-6">
                {company?.name} does not have any active financing rounds at this time.
              </p>
              <Button variant="secondary" onClick={() => router.push(`/companies/${companyId}`)}>
                View Company Profile
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Main Content */}
            <div className="lg:col-span-2 space-y-6">
              {/* Financing Overview */}
              <Card variant="glass-card">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-xl text-gold-400">Financing Overview</CardTitle>
                    {selectedFinancing && (
                      <Badge variant={getStatusBadgeVariant(selectedFinancing.status)}>
                        {selectedFinancing.status === 'announced' ? 'Open' :
                         selectedFinancing.status === 'closing' ? 'Closing Soon' :
                         selectedFinancing.status}
                      </Badge>
                    )}
                  </div>
                  {selectedFinancing && (
                    <CardDescription>
                      {selectedFinancing.financing_type_display}
                    </CardDescription>
                  )}
                </CardHeader>
                <CardContent>
                  {selectedFinancing ? (
                    <div className="space-y-6">
                      {/* Key Metrics */}
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="bg-slate-800/50 rounded-lg p-4">
                          <p className="text-sm text-slate-400 mb-1">Target Raise</p>
                          <p className="text-xl font-bold text-gold-400">
                            {formatCurrency(selectedFinancing.amount_raised_usd)}
                          </p>
                        </div>
                        {selectedFinancing.price_per_share && (
                          <div className="bg-slate-800/50 rounded-lg p-4">
                            <p className="text-sm text-slate-400 mb-1">Price per Share</p>
                            <p className="text-xl font-bold text-white">
                              ${Number(selectedFinancing.price_per_share).toFixed(3)}
                            </p>
                          </div>
                        )}
                        {selectedFinancing.closing_date && (
                          <div className="bg-slate-800/50 rounded-lg p-4">
                            <p className="text-sm text-slate-400 mb-1">Closing Date</p>
                            <p className="text-xl font-bold text-white">
                              {formatDate(selectedFinancing.closing_date)}
                            </p>
                          </div>
                        )}
                        {selectedFinancing.shares_issued && (
                          <div className="bg-slate-800/50 rounded-lg p-4">
                            <p className="text-sm text-slate-400 mb-1">Shares Offered</p>
                            <p className="text-xl font-bold text-white">
                              {selectedFinancing.shares_issued.toLocaleString()}
                            </p>
                          </div>
                        )}
                      </div>

                      {/* Warrants Info */}
                      {selectedFinancing.has_warrants && (
                        <div className="bg-slate-800/30 rounded-lg p-4 border border-slate-700">
                          <h4 className="font-semibold text-white mb-2 flex items-center gap-2">
                            <svg className="w-5 h-5 text-gold-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            Includes Warrants
                          </h4>
                          <div className="grid grid-cols-2 gap-4 text-sm">
                            {selectedFinancing.warrant_strike_price && (
                              <div>
                                <span className="text-slate-400">Strike Price:</span>
                                <span className="text-white ml-2">${Number(selectedFinancing.warrant_strike_price).toFixed(3)}</span>
                              </div>
                            )}
                            {selectedFinancing.warrant_expiry_date && (
                              <div>
                                <span className="text-slate-400">Expiry:</span>
                                <span className="text-white ml-2">{formatDate(selectedFinancing.warrant_expiry_date)}</span>
                              </div>
                            )}
                          </div>
                        </div>
                      )}

                      {/* Use of Proceeds */}
                      {selectedFinancing.use_of_proceeds && (
                        <div>
                          <h4 className="font-semibold text-white mb-2">Use of Proceeds</h4>
                          <p className="text-slate-300 text-sm leading-relaxed">
                            {selectedFinancing.use_of_proceeds}
                          </p>
                        </div>
                      )}

                      {/* Lead Agent */}
                      {selectedFinancing.lead_agent && (
                        <div>
                          <h4 className="font-semibold text-white mb-2">Lead Agent</h4>
                          <p className="text-slate-300">{selectedFinancing.lead_agent}</p>
                        </div>
                      )}

                      {/* Press Release Link */}
                      {selectedFinancing.press_release_url && (
                        <a
                          href={selectedFinancing.press_release_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-2 text-gold-400 hover:text-gold-300 transition-colors"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                          </svg>
                          View Press Release
                        </a>
                      )}
                    </div>
                  ) : (
                    <p className="text-slate-400">No financing selected</p>
                  )}
                </CardContent>
              </Card>

              {/* Investor Interest Tracker */}
              {interestAggregate && (
                <Card variant="glass-card">
                  <CardHeader>
                    <CardTitle className="text-lg text-gold-400">Investor Interest</CardTitle>
                    <CardDescription>Real-time investment interest from platform users</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                      <div className="bg-slate-800/50 rounded-lg p-4 text-center">
                        <p className="text-3xl font-bold text-gold-400">{interestAggregate.total_interest_count}</p>
                        <p className="text-sm text-slate-400">Interested Investors</p>
                      </div>
                      <div className="bg-slate-800/50 rounded-lg p-4 text-center">
                        <p className="text-3xl font-bold text-white">
                          {interestAggregate.total_shares_requested.toLocaleString()}
                        </p>
                        <p className="text-sm text-slate-400">Shares Requested</p>
                      </div>
                      <div className="bg-slate-800/50 rounded-lg p-4 text-center">
                        <p className="text-3xl font-bold text-white">
                          {formatCurrency(Number(interestAggregate.total_amount_interested))}
                        </p>
                        <p className="text-sm text-slate-400">Total Interest</p>
                      </div>
                    </div>

                    {/* Progress Bar */}
                    {selectedFinancing && (
                      <div className="mt-6">
                        <div className="flex justify-between text-sm mb-2">
                          <span className="text-slate-400">Interest Level</span>
                          <span className="text-gold-400">
                            {Number(interestAggregate.percentage_filled).toFixed(1)}%
                          </span>
                        </div>
                        <div className="h-3 bg-slate-700 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-gradient-to-r from-gold-500 to-copper-500 rounded-full transition-all duration-500"
                            style={{
                              width: `${Math.min(Number(interestAggregate.percentage_filled), 100)}%`
                            }}
                          ></div>
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}

              {/* Documents Section */}
              <Card variant="glass-card">
                <CardHeader>
                  <CardTitle className="text-lg text-gold-400">Documents & Forms</CardTitle>
                  <CardDescription>Required documents for participating in this financing</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg">
                      <div className="flex items-center gap-3">
                        <svg className="w-8 h-8 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                        </svg>
                        <div>
                          <p className="font-medium text-white">Private Placement Memorandum</p>
                          <p className="text-sm text-slate-400">PDF Document</p>
                        </div>
                      </div>
                      <Button variant="secondary" size="sm">
                        Download
                      </Button>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg">
                      <div className="flex items-center gap-3">
                        <svg className="w-8 h-8 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        <div>
                          <p className="font-medium text-white">Subscription Agreement</p>
                          <p className="text-sm text-slate-400">PDF Form</p>
                        </div>
                      </div>
                      <Button variant="secondary" size="sm">
                        Download
                      </Button>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg">
                      <div className="flex items-center gap-3">
                        <svg className="w-8 h-8 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <div>
                          <p className="font-medium text-white">Accredited Investor Questionnaire</p>
                          <p className="text-sm text-slate-400">PDF Form</p>
                        </div>
                      </div>
                      <Button variant="secondary" size="sm">
                        Download
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Sidebar */}
            <div className="space-y-6">
              {/* CTA Card */}
              <Card variant="glass-card" className="border-gold-500/30">
                <CardContent className="p-6">
                  <h3 className="text-lg font-semibold text-white mb-4">Participate in this Financing</h3>

                  {!user ? (
                    <div className="space-y-4">
                      <p className="text-sm text-slate-400">
                        Sign in to express interest and access investment documents.
                      </p>
                      <Button variant="primary" className="w-full" onClick={() => setShowLogin(true)}>
                        Sign In to Continue
                      </Button>
                      <Button variant="secondary" className="w-full" onClick={() => setShowRegister(true)}>
                        Create Account
                      </Button>
                    </div>
                  ) : interestStatus?.has_interest ? (
                    <div className="space-y-4">
                      <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-4">
                        <div className="text-center">
                          <svg className="w-12 h-12 mx-auto text-green-400 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          <p className="text-green-400 font-medium">Interest Registered!</p>

                          {isEditing ? (
                            <div className="mt-3 space-y-3">
                              <div>
                                <label className="block text-sm text-slate-400 mb-1">Investment Amount (CAD)</label>
                                <input
                                  type="number"
                                  value={editAmount}
                                  onChange={(e) => setEditAmount(e.target.value)}
                                  className="w-full px-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-white text-center focus:outline-none focus:border-gold-400"
                                  placeholder="Enter amount"
                                  min="0"
                                  step="100"
                                />
                              </div>
                              <div className="flex gap-2">
                                <Button
                                  variant="primary"
                                  size="sm"
                                  className="flex-1"
                                  onClick={handleUpdateInterest}
                                  disabled={isUpdating}
                                >
                                  {isUpdating ? 'Saving...' : 'Save'}
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  className="flex-1"
                                  onClick={handleCancelEdit}
                                  disabled={isUpdating}
                                >
                                  Cancel
                                </Button>
                              </div>
                            </div>
                          ) : (
                            <>
                              <p className="text-sm text-slate-400 mt-1">
                                {interestStatus.shares_requested?.toLocaleString()} shares ({formatCurrency(Number(interestStatus.investment_amount) || 0)})
                              </p>
                              <p className="text-xs text-slate-500 mt-2">
                                Status: {interestStatus.status === 'pending' ? 'Pending Review' : interestStatus.status}
                              </p>
                            </>
                          )}
                        </div>

                        {/* Edit and Cancel buttons - only show if status is pending and not editing */}
                        {interestStatus.status === 'pending' && !isEditing && (
                          <div className="flex gap-2 mt-4 pt-4 border-t border-green-500/20">
                            <Button
                              variant="ghost"
                              size="sm"
                              className="flex-1 text-slate-300 hover:text-white"
                              onClick={handleStartEdit}
                            >
                              <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                              </svg>
                              Edit Amount
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="flex-1 text-red-400 hover:text-red-300 hover:bg-red-500/10"
                              onClick={handleCancelInterest}
                              disabled={isCancelling}
                            >
                              {isCancelling ? (
                                'Cancelling...'
                              ) : (
                                <>
                                  <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                  </svg>
                                  Cancel Interest
                                </>
                              )}
                            </Button>
                          </div>
                        )}
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      <Button
                        type="button"
                        variant="primary"
                        className="w-full"
                        onClick={handleExpressInterest}
                      >
                        Participate in this Financing
                      </Button>
                      <p className="text-xs text-slate-500 text-center">
                        Register your interest to receive investment documents and next steps.
                      </p>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Learn More */}
              <Card variant="glass-card">
                <CardContent className="p-6">
                  <h3 className="text-lg font-semibold text-white mb-4">Learn About Private Placements</h3>
                  <p className="text-sm text-slate-400 mb-4">
                    New to private placements? Visit our Financial Hub to learn about the process,
                    requirements, and what to expect.
                  </p>
                  <Button
                    variant="secondary"
                    className="w-full"
                    onClick={() => router.push('/financial-hub')}
                  >
                    Visit Financial Hub
                  </Button>
                </CardContent>
              </Card>

              {/* Other Financings */}
              {financings.length > 1 && (
                <Card variant="glass-card">
                  <CardHeader>
                    <CardTitle className="text-sm text-slate-400">Other Financing Rounds</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {financings
                        .filter(f => f.id !== selectedFinancing?.id)
                        .slice(0, 3)
                        .map(financing => (
                          <button
                            key={financing.id}
                            onClick={() => {
                              setSelectedFinancing(financing);
                              fetchFinancingAggregate(financing.id);
                            }}
                            className="w-full text-left p-3 bg-slate-800/30 hover:bg-slate-800/50 rounded-lg transition-all"
                          >
                            <div className="flex items-center justify-between">
                              <span className="text-sm text-white">{financing.financing_type_display}</span>
                              <Badge variant="slate" className="text-xs">
                                {financing.status}
                              </Badge>
                            </div>
                            <p className="text-xs text-slate-400 mt-1">
                              {formatDate(financing.announced_date)}
                            </p>
                          </button>
                        ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <footer className="py-8 px-4 border-t border-slate-800 mt-12">
        <div className="max-w-7xl mx-auto text-center text-slate-400 text-sm">
          <p>&copy; {new Date().getFullYear()} GoldVenture. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
