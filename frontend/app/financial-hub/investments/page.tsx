'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  TrendingUp,
  ArrowLeft,
  Calendar,
  Building2,
  PieChart,
  Activity,
  CheckCircle,
  Clock,
  AlertCircle,
  ArrowRight,
  Wallet,
  BarChart3
} from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Card, CardContent } from '@/components/ui/Card';
import LogoMono from '@/components/LogoMono';
import { LoginModal, RegisterModal } from '@/components/auth';
import { useAuth } from '@/contexts/AuthContext';

interface Company {
  id: number;
  name: string;
  ticker_symbol: string;
}

interface Financing {
  id: number;
  company: Company;
  price_per_share: string;
}

interface SubscriptionAgreement {
  id: number;
  financing: Financing;
  total_investment_amount: string;
  num_shares: number | null;
  warrant_shares: number | null;
  status: string;
}

interface InvestmentTransaction {
  id: number;
  subscription_agreement: SubscriptionAgreement;
  amount: string;
  status: string;
  status_display: string;
  payment_date: string | null;
  payment_reference: string;
  shares_allocated: number | null;
  created_at: string;
}

interface PortfolioSummary {
  total_invested: number;
  total_shares: number;
  total_warrants: number;
  total_current_value: number;
  companies_count: number;
  pending_transactions: number;
  completed_transactions: number;
}

export default function InvestmentTracking() {
  const router = useRouter();
  const [transactions, setTransactions] = useState<InvestmentTransaction[]>([]);
  const [portfolio, setPortfolio] = useState<PortfolioSummary>({
    total_invested: 0,
    total_shares: 0,
    total_warrants: 0,
    total_current_value: 0,
    companies_count: 0,
    pending_transactions: 0,
    completed_transactions: 0,
  });
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'pending' | 'completed' | 'failed'>('all');
  const [showLogin, setShowLogin] = useState(false);
  const [showRegister, setShowRegister] = useState(false);
  const { user, logout } = useAuth();

  useEffect(() => {
    fetchTransactions();
  }, []);

  const fetchTransactions = async () => {
    try {
      const token = localStorage.getItem('accessToken');
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/investments/transactions/`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        const txnsArray = Array.isArray(data) ? data : [];
        setTransactions(txnsArray);
        calculatePortfolioSummary(txnsArray);
      } else {
        setTransactions([]);
        calculatePortfolioSummary([]);
      }
    } catch (error) {
      console.error('Error fetching transactions:', error);
      setTransactions([]);
      calculatePortfolioSummary([]);
    } finally {
      setLoading(false);
    }
  };

  const calculatePortfolioSummary = (txns: InvestmentTransaction[]) => {
    const uniqueAgreements = new Map<number, SubscriptionAgreement>();

    txns.forEach(txn => {
      if (!uniqueAgreements.has(txn.subscription_agreement.id)) {
        uniqueAgreements.set(txn.subscription_agreement.id, txn.subscription_agreement);
      }
    });

    const agreements = Array.from(uniqueAgreements.values());
    const uniqueCompanies = new Set(agreements.map(a => a.financing.company.id));

    const totalInvested = agreements.reduce((sum, a) => sum + parseFloat(a.total_investment_amount), 0);
    const totalShares = agreements.reduce((sum, a) => sum + (a.num_shares || 0), 0);
    const totalWarrants = agreements.reduce((sum, a) => sum + (a.warrant_shares || 0), 0);

    // Calculate current value (using current share prices - for now same as invested)
    const totalCurrentValue = agreements.reduce((sum, a) => {
      const shares = a.num_shares || 0;
      const price = parseFloat(a.financing.price_per_share);
      return sum + (shares * price);
    }, 0);

    setPortfolio({
      total_invested: totalInvested,
      total_shares: totalShares,
      total_warrants: totalWarrants,
      total_current_value: totalCurrentValue,
      companies_count: uniqueCompanies.size,
      pending_transactions: txns.filter(t => t.status === 'pending' || t.status === 'processing').length,
      completed_transactions: txns.filter(t => t.status === 'completed').length,
    });
  };

  const getStatusBadge = (status: string) => {
    const statusConfig: Record<string, { variant: 'gold' | 'copper' | 'success' | 'warning' | 'error' | 'info' | 'slate'; icon: any; label: string }> = {
      pending: { variant: 'warning', icon: Clock, label: 'Pending' },
      processing: { variant: 'info', icon: Activity, label: 'Processing' },
      completed: { variant: 'success', icon: CheckCircle, label: 'Completed' },
      failed: { variant: 'error', icon: AlertCircle, label: 'Failed' },
      cancelled: { variant: 'slate', icon: AlertCircle, label: 'Cancelled' },
      refunded: { variant: 'copper', icon: AlertCircle, label: 'Refunded' },
      on_hold: { variant: 'info', icon: Clock, label: 'On Hold' },
    };

    const config = statusConfig[status] || statusConfig.pending;
    const Icon = config.icon;

    return (
      <Badge variant={config.variant} className="inline-flex items-center gap-1.5">
        <Icon className="w-3.5 h-3.5" />
        {config.label}
      </Badge>
    );
  };

  const filteredTransactions = transactions.filter(txn => {
    if (filter === 'all') return true;
    if (filter === 'pending') return txn.status === 'pending' || txn.status === 'processing';
    if (filter === 'completed') return txn.status === 'completed';
    if (filter === 'failed') return txn.status === 'failed' || txn.status === 'cancelled';
    return true;
  });

  const gainLoss = portfolio.total_current_value - portfolio.total_invested;
  const gainLossPercent = portfolio.total_invested > 0
    ? ((gainLoss / portfolio.total_invested) * 100).toFixed(2)
    : '0.00';

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gold-400 mx-auto mb-4"></div>
          <p className="text-slate-300">Loading investment data...</p>
        </div>
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
              <Badge variant="copper">AI-Powered</Badge>
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
      <section className="relative py-16 px-4 sm:px-6 lg:px-8 overflow-hidden">
        <div className="absolute inset-0 bg-linear-to-b from-slate-900 via-slate-900 to-slate-800 opacity-50"></div>
        <div className="absolute inset-0" style={{
          backgroundImage: 'radial-gradient(circle at 50% 50%, rgba(212, 161, 42, 0.1) 0%, transparent 50%)'
        }}></div>

        <div className="relative max-w-7xl mx-auto">
          <button
            onClick={() => router.push('/financial-hub')}
            className="flex items-center gap-2 text-slate-400 hover:text-gold-400 mb-6 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Financial Hub
          </button>

          <Badge variant="gold" className="mb-4">
            Portfolio Tracker
          </Badge>
          <h1 className="text-4xl md:text-5xl font-bold mb-4 text-gradient-gold animate-fade-in leading-tight pb-2">
            Investment Tracking
          </h1>
          <p className="text-lg text-slate-300 max-w-3xl">
            Monitor your investment portfolio, track transactions, and view performance analytics.
          </p>
        </div>
      </section>

      {/* Main Content */}
      <section className="py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          {/* Portfolio Summary */}
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <Card variant="glass-card">
              <CardContent className="py-6">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-slate-400 text-sm">Total Invested</span>
                  <div className="w-10 h-10 rounded-lg flex items-center justify-center"
                       style={{ backgroundColor: 'rgba(59, 130, 246, 0.2)', border: '2px solid rgb(59, 130, 246)' }}>
                    <Wallet className="w-5 h-5 text-blue-400" />
                  </div>
                </div>
                <p className="text-3xl font-bold text-white">
                  ${portfolio.total_invested.toLocaleString()}
                </p>
              </CardContent>
            </Card>

            <Card variant="glass-card">
              <CardContent className="py-6">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-slate-400 text-sm">Current Value</span>
                  <div className="w-10 h-10 rounded-lg flex items-center justify-center"
                       style={{ backgroundColor: 'rgba(34, 197, 94, 0.2)', border: '2px solid rgb(34, 197, 94)' }}>
                    <TrendingUp className="w-5 h-5 text-green-400" />
                  </div>
                </div>
                <p className="text-3xl font-bold text-white">
                  ${portfolio.total_current_value.toLocaleString()}
                </p>
                <p className={`text-sm mt-1 ${gainLoss >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {gainLoss >= 0 ? '+' : ''}{gainLossPercent}% ({gainLoss >= 0 ? '+' : ''}${gainLoss.toLocaleString()})
                </p>
              </CardContent>
            </Card>

            <Card variant="glass-card">
              <CardContent className="py-6">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-slate-400 text-sm">Total Shares</span>
                  <div className="w-10 h-10 rounded-lg flex items-center justify-center"
                       style={{ backgroundColor: 'rgba(168, 85, 247, 0.2)', border: '2px solid rgb(168, 85, 247)' }}>
                    <BarChart3 className="w-5 h-5 text-purple-400" />
                  </div>
                </div>
                <p className="text-3xl font-bold text-white">
                  {portfolio.total_shares.toLocaleString()}
                </p>
                {portfolio.total_warrants > 0 && (
                  <p className="text-sm text-slate-400 mt-1">
                    +{portfolio.total_warrants.toLocaleString()} warrants
                  </p>
                )}
              </CardContent>
            </Card>

            <Card variant="glass-card">
              <CardContent className="py-6">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-slate-400 text-sm">Companies</span>
                  <div className="w-10 h-10 rounded-lg flex items-center justify-center"
                       style={{ backgroundColor: 'rgba(249, 115, 22, 0.2)', border: '2px solid rgb(249, 115, 22)' }}>
                    <Building2 className="w-5 h-5 text-orange-400" />
                  </div>
                </div>
                <p className="text-3xl font-bold text-white">
                  {portfolio.companies_count}
                </p>
                <p className="text-sm text-slate-400 mt-1">
                  {portfolio.pending_transactions} pending
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Transaction Filters */}
          <Card variant="glass-card" className="mb-6">
            <CardContent className="py-4">
              <div className="flex items-center gap-4">
                <span className="text-sm font-semibold text-slate-300">Filter:</span>
                <div className="flex gap-2">
                  {(['all', 'pending', 'completed', 'failed'] as const).map((f) => (
                    <Button
                      key={f}
                      variant={filter === f ? 'primary' : 'secondary'}
                      size="sm"
                      onClick={() => setFilter(f)}
                    >
                      {f.charAt(0).toUpperCase() + f.slice(1)}
                    </Button>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Transactions List */}
          {filteredTransactions.length === 0 ? (
            <Card variant="glass-strong" className="text-center py-12">
              <CardContent>
                <Activity className="w-16 h-16 text-slate-600 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-white mb-2">
                  {filter === 'all' ? 'No Transactions Yet' : `No ${filter} Transactions`}
                </h3>
                <p className="text-slate-400 mb-6">
                  {filter === 'all'
                    ? "You haven't made any investments yet. Start by reviewing available subscription agreements."
                    : `You don't have any ${filter} transactions at the moment.`
                  }
                </p>
                {filter === 'all' && (
                  <Button
                    variant="primary"
                    onClick={() => router.push('/financial-hub/agreements')}
                  >
                    View Agreements
                    <ArrowRight className="w-4 h-4 ml-2" />
                  </Button>
                )}
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {filteredTransactions.map((transaction, idx) => (
                <Card
                  key={transaction.id}
                  variant="glass-card"
                  className="hover:scale-[1.01] transition-transform cursor-pointer animate-slide-in-up"
                  style={{ animationDelay: `${idx * 50}ms` }}
                  onClick={() => router.push(`/financial-hub/investments/${transaction.id}`)}
                >
                  <CardContent className="py-6">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <div className="w-10 h-10 rounded-lg flex items-center justify-center"
                               style={{ backgroundColor: 'rgba(212, 175, 55, 0.2)', border: '2px solid #d4af37' }}>
                            <Building2 className="w-5 h-5 text-gold-400" />
                          </div>
                          <div>
                            <h3 className="text-xl font-semibold text-gold-400">
                              {transaction.subscription_agreement.financing.company.name}
                            </h3>
                            <p className="text-sm text-slate-400">
                              Agreement #{transaction.subscription_agreement.id}
                            </p>
                          </div>
                        </div>
                      </div>
                      {getStatusBadge(transaction.status)}
                    </div>

                    <div className="grid md:grid-cols-4 gap-4">
                      <div>
                        <p className="text-sm text-slate-500 mb-1">Amount</p>
                        <p className="text-lg font-semibold text-white">
                          ${parseFloat(transaction.amount).toLocaleString()}
                        </p>
                      </div>

                      <div>
                        <p className="text-sm text-slate-500 mb-1">Payment Date</p>
                        <p className="text-lg font-semibold text-white flex items-center gap-1">
                          <Calendar className="w-4 h-4 text-slate-400" />
                          {transaction.payment_date ? new Date(transaction.payment_date).toLocaleDateString() : 'Pending'}
                        </p>
                      </div>

                      {transaction.payment_reference && (
                        <div>
                          <p className="text-sm text-slate-500 mb-1">Reference</p>
                          <p className="text-sm font-mono text-slate-300">
                            {transaction.payment_reference}
                          </p>
                        </div>
                      )}

                      {transaction.shares_allocated !== null && (
                        <div>
                          <p className="text-sm text-slate-500 mb-1">Shares</p>
                          <p className="text-lg font-semibold text-white">
                            {transaction.shares_allocated.toLocaleString()}
                          </p>
                        </div>
                      )}
                    </div>

                    <div className="mt-4 flex items-center justify-end text-gold-400 font-medium">
                      <span>View Details</span>
                      <ArrowRight className="w-4 h-4 ml-2" />
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          {/* Quick Actions */}
          <div className="mt-12 grid md:grid-cols-3 gap-6">
            <button
              onClick={() => router.push('/financial-hub/agreements')}
              className="group p-6 backdrop-blur-sm bg-slate-800/50 border border-slate-700/50 rounded-xl
                transition-all duration-300 hover:bg-slate-800/80 hover:border-gold-400/30 hover:-translate-y-1 text-left"
            >
              <div className="w-12 h-12 rounded-lg flex items-center justify-center mb-4 transition-transform group-hover:scale-110"
                   style={{ backgroundColor: 'rgba(59, 130, 246, 0.2)', border: '2px solid rgb(59, 130, 246)' }}>
                <PieChart className="w-6 h-6 text-blue-400" />
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">
                View Agreements
              </h3>
              <p className="text-sm text-slate-400">
                Review and manage your subscription agreements
              </p>
              <div className="mt-4 flex items-center gap-2 text-gold-400 font-medium">
                <span>Explore</span>
                <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
              </div>
            </button>

            <button
              onClick={() => router.push('/financial-hub/drs')}
              className="group p-6 backdrop-blur-sm bg-slate-800/50 border border-slate-700/50 rounded-xl
                transition-all duration-300 hover:bg-slate-800/80 hover:border-gold-400/30 hover:-translate-y-1 text-left"
            >
              <div className="w-12 h-12 rounded-lg flex items-center justify-center mb-4 transition-transform group-hover:scale-110"
                   style={{ backgroundColor: 'rgba(99, 102, 241, 0.2)', border: '2px solid rgb(99, 102, 241)' }}>
                <CheckCircle className="w-6 h-6 text-indigo-400" />
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">
                DRS Documents
              </h3>
              <p className="text-sm text-slate-400">
                Access your share certificates and documentation
              </p>
              <div className="mt-4 flex items-center gap-2 text-gold-400 font-medium">
                <span>Explore</span>
                <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
              </div>
            </button>

            <button
              onClick={() => router.push('/companies')}
              className="group p-6 backdrop-blur-sm bg-slate-800/50 border border-slate-700/50 rounded-xl
                transition-all duration-300 hover:bg-slate-800/80 hover:border-gold-400/30 hover:-translate-y-1 text-left"
            >
              <div className="w-12 h-12 rounded-lg flex items-center justify-center mb-4 transition-transform group-hover:scale-110"
                   style={{ backgroundColor: 'rgba(34, 197, 94, 0.2)', border: '2px solid rgb(34, 197, 94)' }}>
                <Building2 className="w-6 h-6 text-green-400" />
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">
                Browse Companies
              </h3>
              <p className="text-sm text-slate-400">
                Discover new investment opportunities
              </p>
              <div className="mt-4 flex items-center gap-2 text-gold-400 font-medium">
                <span>Explore</span>
                <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
              </div>
            </button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 px-4 border-t border-slate-800">
        <div className="max-w-7xl mx-auto text-center text-slate-400 text-sm">
          <p>&copy; {new Date().getFullYear()} GoldVenture. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
