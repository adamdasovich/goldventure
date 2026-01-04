'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  FileText,
  CheckCircle,
  Clock,
  ArrowLeft,
  ArrowRight,
  AlertCircle,
  DollarSign,
  Calendar,
  Building2,
  TrendingUp
} from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import LogoMono from '@/components/LogoMono';
import { LoginModal, RegisterModal } from '@/components/auth';
import { useAuth } from '@/contexts/AuthContext';

interface SubscriptionAgreement {
  id: number;
  financing_detail: {
    id: number;
    company: {
      id: number;
      name: string;
      ticker_symbol: string;
    };
    price_per_share: string;
    financing_type: string;
  };
  status: string;
  status_display: string;
  total_investment_amount: string;
  num_shares: number | null;
  warrant_shares: number | null;
  investor_signed_at: string | null;
  created_at: string;
  updated_at: string;
}

export default function SubscriptionAgreements() {
  const router = useRouter();
  const [agreements, setAgreements] = useState<SubscriptionAgreement[]>([]);
  const [loading, setLoading] = useState(true);
  const [qualified, setQualified] = useState(false);
  const [showLogin, setShowLogin] = useState(false);
  const [showRegister, setShowRegister] = useState(false);
  const { user, logout } = useAuth();

  useEffect(() => {
    checkQualification();
    fetchAgreements();
  }, []);

  const checkQualification = async () => {
    try {
      const token = localStorage.getItem('accessToken');
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/qualifications/status/`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setQualified(data.status === 'qualified');
      }
    } catch (error) {
      console.error('Error checking qualification:', error);
    }
  };

  const fetchAgreements = async () => {
    try {
      const token = localStorage.getItem('accessToken');
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/agreements/`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setAgreements(Array.isArray(data) ? data : []);
      } else {
        setAgreements([]);
      }
    } catch (error) {
      console.error('Error fetching agreements:', error);
      setAgreements([]);
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    const statusConfig: Record<string, { color: string; icon: any; label: string }> = {
      draft: { color: 'bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-300', icon: Clock, label: 'Draft' },
      pending_signature: { color: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300', icon: Clock, label: 'Pending Signature' },
      signed: { color: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300', icon: CheckCircle, label: 'Signed' },
      payment_pending: { color: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-300', icon: DollarSign, label: 'Payment Pending' },
      payment_received: { color: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300', icon: CheckCircle, label: 'Payment Received' },
      shares_allocated: { color: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300', icon: TrendingUp, label: 'Shares Allocated' },
      drs_issued: { color: 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300', icon: CheckCircle, label: 'DRS Issued' },
      completed: { color: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300', icon: CheckCircle, label: 'Completed' },
    };

    const config = statusConfig[status] || statusConfig.draft;
    const Icon = config.icon;

    return (
      <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-medium ${config.color}`}>
        <Icon className="w-4 h-4" />
        {config.label}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gold-400 mx-auto mb-4"></div>
          <p className="text-slate-300">Loading subscription agreements...</p>
        </div>
      </div>
    );
  }

  if (!qualified) {
    return (
      <div className="min-h-screen">
        {/* Navigation */}
        <nav className="glass-nav sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-24">
              <div className="flex items-center space-x-3 cursor-pointer" onClick={() => router.push('/')}>
                <LogoMono className="h-18" />
              </div>
              <div className="flex items-center space-x-4">
                <Button variant="ghost" size="sm" onClick={() => router.push('/')}>Dashboard</Button>
                <Button variant="ghost" size="sm" onClick={() => router.push('/companies')}>Companies</Button>
                <Button variant="ghost" size="sm" onClick={() => router.push('/metals')}>Metals</Button>
                <Button variant="ghost" size="sm" onClick={() => router.push('/financial-hub')}>Financial Hub</Button>

                {user ? (
                  <div className="flex items-center space-x-3">
                    <span className="text-sm text-slate-300">
                      Welcome, {user.full_name || user.username}
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

        <section className="relative py-20 px-4 sm:px-6 lg:px-8 overflow-hidden">
          <div className="absolute inset-0 bg-linear-to-b from-slate-900 via-slate-900 to-slate-800 opacity-50"></div>
          <div className="absolute inset-0" style={{
            backgroundImage: 'radial-gradient(circle at 50% 50%, rgba(212, 161, 42, 0.1) 0%, transparent 50%)'
          }}></div>

          <div className="relative max-w-4xl mx-auto">
            <button
              onClick={() => router.push('/financial-hub')}
              className="flex items-center gap-2 text-slate-300 hover:text-white mb-8 transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              Back to Financial Hub
            </button>

            <div className="backdrop-blur-sm bg-yellow-500/10 border-2 border-yellow-500/30 rounded-xl p-8 text-center">
              <AlertCircle className="w-16 h-16 text-yellow-400 mx-auto mb-4" />
              <h2 className="text-2xl font-bold text-white mb-3">
                Accreditation Required
              </h2>
              <p className="text-slate-300 mb-6">
                You must complete the Accredited Investor Qualification to access subscription agreements.
              </p>
              <button
                onClick={() => router.push('/financial-hub/qualification')}
                className="px-6 py-3 bg-gold-400 text-slate-900 font-semibold rounded-lg hover:bg-gold-500 transition-colors inline-flex items-center gap-2"
              >
                Complete Qualification
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </section>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      {/* Navigation */}
      <nav className="glass-nav sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-24">
            <div className="flex items-center space-x-3 cursor-pointer" onClick={() => router.push('/')}>
              <LogoMono className="h-18" />
            </div>
            <div className="flex items-center space-x-4">
              <Button variant="ghost" size="sm" onClick={() => router.push('/')}>Dashboard</Button>
              <Button variant="ghost" size="sm" onClick={() => router.push('/companies')}>Companies</Button>
              <Button variant="ghost" size="sm" onClick={() => router.push('/metals')}>Metals</Button>
              <Button variant="ghost" size="sm" onClick={() => router.push('/financial-hub')}>Financial Hub</Button>

              {user ? (
                <div className="flex items-center space-x-3">
                  <span className="text-sm text-slate-300">
                    Welcome, {user.full_name || user.username}
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

      {/* Hero Section */}
      <section className="relative py-20 px-4 sm:px-6 lg:px-8 overflow-hidden">
        <div className="absolute inset-0 bg-linear-to-b from-slate-900 via-slate-900 to-slate-800 opacity-50"></div>
        <div className="absolute inset-0" style={{
          backgroundImage: 'radial-gradient(circle at 50% 50%, rgba(212, 161, 42, 0.1) 0%, transparent 50%)'
        }}></div>

        <div className="relative max-w-7xl mx-auto">
          <button
            onClick={() => router.push('/financial-hub')}
            className="flex items-center gap-2 text-slate-300 hover:text-white mb-8 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Financial Hub
          </button>

          <div className="text-center mb-12">
            <h1 className="text-5xl md:text-6xl font-bold mb-6 text-gradient-gold animate-fade-in leading-tight pb-2">
              Subscription Agreements
            </h1>
            <p className="text-xl text-slate-300 max-w-3xl mx-auto">
              Review and manage your subscription agreements for mining company financing rounds.
            </p>
          </div>
        </div>
      </section>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 -mt-8">{/* Overlap section */}

        {/* Summary Stats */}
        {agreements.length > 0 && (
          <div className="grid md:grid-cols-4 gap-4 mb-8">
            <div className="backdrop-blur-sm bg-slate-800/50 border border-slate-700/50 rounded-xl p-6">
              <div className="flex items-center justify-between mb-2">
                <span className="text-slate-300 text-sm">Total Agreements</span>
                <FileText className="w-5 h-5 text-gold-400" />
              </div>
              <p className="text-3xl font-bold text-white">{agreements.length}</p>
            </div>

            <div className="backdrop-blur-sm bg-slate-800/50 border border-slate-700/50 rounded-xl p-6">
              <div className="flex items-center justify-between mb-2">
                <span className="text-slate-300 text-sm">Pending Signature</span>
                <Clock className="w-5 h-5 text-yellow-400" />
              </div>
              <p className="text-3xl font-bold text-white">
                {agreements.filter(a => a.status === 'pending_signature').length}
              </p>
            </div>

            <div className="backdrop-blur-sm bg-slate-800/50 border border-slate-700/50 rounded-xl p-6">
              <div className="flex items-center justify-between mb-2">
                <span className="text-slate-300 text-sm">Total Invested</span>
                <DollarSign className="w-5 h-5 text-green-400" />
              </div>
              <p className="text-3xl font-bold text-white">
                ${agreements.reduce((sum, a) => sum + parseFloat(a.total_investment_amount), 0).toLocaleString()}
              </p>
            </div>

            <div className="backdrop-blur-sm bg-slate-800/50 border border-slate-700/50 rounded-xl p-6">
              <div className="flex items-center justify-between mb-2">
                <span className="text-slate-300 text-sm">Completed</span>
                <CheckCircle className="w-5 h-5 text-green-400" />
              </div>
              <p className="text-3xl font-bold text-white">
                {agreements.filter(a => a.status === 'completed').length}
              </p>
            </div>
          </div>
        )}

        {/* Agreements List */}
        {agreements.length === 0 ? (
          <div className="backdrop-blur-sm bg-slate-800/50 border border-slate-700/50 rounded-xl p-12 text-center">
            <FileText className="w-16 h-16 text-slate-600 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-white mb-2">
              No Subscription Agreements Yet
            </h3>
            <p className="text-slate-300 mb-6">
              You haven't signed any subscription agreements. Browse available financing opportunities to get started.
            </p>
            <button
              onClick={() => router.push('/companies')}
              className="px-6 py-3 bg-gold-400 text-slate-900 font-semibold rounded-lg hover:bg-gold-500 transition-colors inline-flex items-center gap-2"
            >
              Browse Companies
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            {agreements.map((agreement) => (
              <button
                key={agreement.id}
                onClick={() => router.push(`/financial-hub/agreements/${agreement.id}`)}
                className="w-full backdrop-blur-sm bg-slate-800/50 border border-slate-700/50 rounded-xl hover:bg-slate-800/80 hover:border-gold-400/30 hover:-translate-y-1 transition-all duration-300 p-6 text-left"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <Building2 className="w-5 h-5 text-gold-400" />
                      <h3 className="text-xl font-semibold text-white">
                        {agreement.financing_detail.company.name}
                      </h3>
                    </div>
                    <p className="text-slate-300">
                      Financing Round #{agreement.financing_detail.id}
                    </p>
                  </div>
                  {getStatusBadge(agreement.status)}
                </div>

                <div className="grid md:grid-cols-4 gap-4">
                  <div>
                    <p className="text-sm text-slate-400 mb-1">Investment Amount</p>
                    <p className="text-lg font-semibold text-white">
                      ${parseFloat(agreement.total_investment_amount).toLocaleString()}
                    </p>
                  </div>

                  <div>
                    <p className="text-sm text-slate-400 mb-1">Price Per Share</p>
                    <p className="text-lg font-semibold text-white">
                      ${parseFloat(agreement.financing_detail.price_per_share).toFixed(2)}
                    </p>
                  </div>

                  {agreement.num_shares !== null && (
                    <div>
                      <p className="text-sm text-slate-400 mb-1">Shares Allocated</p>
                      <p className="text-lg font-semibold text-white">
                        {agreement.num_shares.toLocaleString()}
                      </p>
                    </div>
                  )}

                  {agreement.warrant_shares !== null && agreement.warrant_shares > 0 && (
                    <div>
                      <p className="text-sm text-slate-400 mb-1">Warrants</p>
                      <p className="text-lg font-semibold text-white">
                        {agreement.warrant_shares.toLocaleString()}
                      </p>
                    </div>
                  )}

                  <div>
                    <p className="text-sm text-slate-400 mb-1">
                      {agreement.investor_signed_at ? 'Signed On' : 'Created On'}
                    </p>
                    <p className="text-lg font-semibold text-white flex items-center gap-1">
                      <Calendar className="w-4 h-4" />
                      {new Date(agreement.investor_signed_at || agreement.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>

                <div className="mt-4 flex items-center justify-end text-gold-400 font-medium">
                  <span>View Details</span>
                  <ArrowRight className="w-4 h-4 ml-2 transition-transform group-hover:translate-x-1" />
                </div>
              </button>
            ))}
          </div>
        )}

        {/* Help Section */}
        <div className="mt-12 p-6 backdrop-blur-sm bg-slate-800/30 border border-gold-400/20 rounded-xl">
          <h3 className="text-lg font-semibold text-white mb-2">
            About Subscription Agreements
          </h3>
          <p className="text-slate-300 mb-4">
            A subscription agreement is a legal contract between you and the mining company outlining the terms of your investment in their financing round.
          </p>
          <ul className="space-y-2 text-slate-300 text-sm">
            <li className="flex items-start gap-2">
              <CheckCircle className="w-5 h-5 text-gold-400 mt-0.5 flex-shrink-0" />
              <span>Review all terms carefully before signing</span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle className="w-5 h-5 text-gold-400 mt-0.5 flex-shrink-0" />
              <span>Your shares will be allocated after payment is confirmed</span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle className="w-5 h-5 text-gold-400 mt-0.5 flex-shrink-0" />
              <span>DRS certificates will be issued once the financing round closes</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}
