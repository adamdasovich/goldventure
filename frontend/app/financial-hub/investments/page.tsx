'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  TrendingUp,
  ArrowLeft,
  DollarSign,
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
      const response = await fetch('https://api.juniorgoldminingintelligence.com/api/investments/transactions/', {
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
    const statusConfig: Record<string, { color: string; icon: any; label: string }> = {
      pending: { color: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300', icon: Clock, label: 'Pending' },
      processing: { color: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300', icon: Activity, label: 'Processing' },
      completed: { color: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300', icon: CheckCircle, label: 'Completed' },
      failed: { color: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300', icon: AlertCircle, label: 'Failed' },
      cancelled: { color: 'bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-300', icon: AlertCircle, label: 'Cancelled' },
      refunded: { color: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-300', icon: AlertCircle, label: 'Refunded' },
      on_hold: { color: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300', icon: Clock, label: 'On Hold' },
    };

    const config = statusConfig[status] || statusConfig.pending;
    const Icon = config.icon;

    return (
      <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium ${config.color}`}>
        <Icon className="w-3.5 h-3.5" />
        {config.label}
      </span>
    );
  };

  const getTransactionTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      investment: 'text-green-600 dark:text-green-400',
      dividend: 'text-blue-600 dark:text-blue-400',
      refund: 'text-orange-600 dark:text-orange-400',
      fee: 'text-red-600 dark:text-red-400',
      transfer: 'text-purple-600 dark:text-purple-400',
    };
    return colors[type] || 'text-slate-600 dark:text-slate-400';
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
      <div className="min-h-screen bg-slate-50 dark:bg-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-slate-600 dark:text-slate-300">Loading investment data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
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
                  <Button variant="ghost" size="sm" onClick={() => setShowRegister(true)}>
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

      <div className="container mx-auto px-4 py-12">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => router.push('/financial-hub')}
            className="flex items-center gap-2 text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white mb-4 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Financial Hub
          </button>

          <h1 className="text-4xl font-bold text-slate-900 dark:text-white mb-4">
            Investment Tracking
          </h1>
          <p className="text-lg text-slate-600 dark:text-slate-300 max-w-3xl">
            Monitor your investment portfolio, track transactions, and view performance analytics.
          </p>
        </div>

        {/* Portfolio Summary */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white dark:bg-slate-800 rounded-xl shadow-md p-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-slate-600 dark:text-slate-300 text-sm">Total Invested</span>
              <Wallet className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            </div>
            <p className="text-3xl font-bold text-slate-900 dark:text-white">
              ${portfolio.total_invested.toLocaleString()}
            </p>
          </div>

          <div className="bg-white dark:bg-slate-800 rounded-xl shadow-md p-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-slate-600 dark:text-slate-300 text-sm">Current Value</span>
              <TrendingUp className="w-5 h-5 text-green-600 dark:text-green-400" />
            </div>
            <p className="text-3xl font-bold text-slate-900 dark:text-white">
              ${portfolio.total_current_value.toLocaleString()}
            </p>
            <p className={`text-sm mt-1 ${gainLoss >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
              {gainLoss >= 0 ? '+' : ''}{gainLossPercent}% ({gainLoss >= 0 ? '+' : ''}${gainLoss.toLocaleString()})
            </p>
          </div>

          <div className="bg-white dark:bg-slate-800 rounded-xl shadow-md p-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-slate-600 dark:text-slate-300 text-sm">Total Shares</span>
              <BarChart3 className="w-5 h-5 text-purple-600 dark:text-purple-400" />
            </div>
            <p className="text-3xl font-bold text-slate-900 dark:text-white">
              {portfolio.total_shares.toLocaleString()}
            </p>
            {portfolio.total_warrants > 0 && (
              <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
                +{portfolio.total_warrants.toLocaleString()} warrants
              </p>
            )}
          </div>

          <div className="bg-white dark:bg-slate-800 rounded-xl shadow-md p-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-slate-600 dark:text-slate-300 text-sm">Companies</span>
              <Building2 className="w-5 h-5 text-orange-600 dark:text-orange-400" />
            </div>
            <p className="text-3xl font-bold text-slate-900 dark:text-white">
              {portfolio.companies_count}
            </p>
            <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
              {portfolio.pending_transactions} pending
            </p>
          </div>
        </div>

        {/* Transaction Filters */}
        <div className="bg-white dark:bg-slate-800 rounded-xl shadow-md p-4 mb-6">
          <div className="flex items-center gap-4">
            <span className="text-sm font-semibold text-slate-700 dark:text-slate-300">Filter:</span>
            <div className="flex gap-2">
              {(['all', 'pending', 'completed', 'failed'] as const).map((f) => (
                <button
                  key={f}
                  onClick={() => setFilter(f)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    filter === f
                      ? 'bg-blue-600 text-white'
                      : 'bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-600'
                  }`}
                >
                  {f.charAt(0).toUpperCase() + f.slice(1)}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Transactions List */}
        {filteredTransactions.length === 0 ? (
          <div className="bg-white dark:bg-slate-800 rounded-xl shadow-md p-12 text-center">
            <Activity className="w-16 h-16 text-slate-300 dark:text-slate-600 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-slate-900 dark:text-white mb-2">
              {filter === 'all' ? 'No Transactions Yet' : `No ${filter} Transactions`}
            </h3>
            <p className="text-slate-600 dark:text-slate-300 mb-6">
              {filter === 'all'
                ? "You haven't made any investments yet. Start by reviewing available subscription agreements."
                : `You don't have any ${filter} transactions at the moment.`
              }
            </p>
            {filter === 'all' && (
              <button
                onClick={() => router.push('/financial-hub/agreements')}
                className="px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors inline-flex items-center gap-2"
              >
                View Agreements
                <ArrowRight className="w-4 h-4" />
              </button>
            )}
          </div>
        ) : (
          <div className="space-y-4">
            {filteredTransactions.map((transaction) => (
              <button
                key={transaction.id}
                onClick={() => router.push(`/financial-hub/investments/${transaction.id}`)}
                className="w-full bg-white dark:bg-slate-800 rounded-xl shadow-md hover:shadow-xl transition-all duration-300 hover:-translate-y-1 p-6 text-left"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <Building2 className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                      <h3 className="text-xl font-semibold text-slate-900 dark:text-white">
                        {transaction.subscription_agreement.financing.company.name}
                      </h3>
                    </div>
                    <p className="text-slate-600 dark:text-slate-300">
                      Agreement #{transaction.subscription_agreement.id}
                    </p>
                  </div>
                  {getStatusBadge(transaction.status)}
                </div>

                <div className="grid md:grid-cols-4 gap-4">
                  <div>
                    <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">Amount</p>
                    <p className="text-lg font-semibold text-slate-900 dark:text-white">
                      ${parseFloat(transaction.amount).toLocaleString()}
                    </p>
                  </div>

                  <div>
                    <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">Payment Date</p>
                    <p className="text-lg font-semibold text-slate-900 dark:text-white flex items-center gap-1">
                      <Calendar className="w-4 h-4" />
                      {transaction.payment_date ? new Date(transaction.payment_date).toLocaleDateString() : 'Pending'}
                    </p>
                  </div>

                  {transaction.payment_reference && (
                    <div>
                      <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">Reference</p>
                      <p className="text-sm font-mono text-slate-900 dark:text-white">
                        {transaction.payment_reference}
                      </p>
                    </div>
                  )}

                  {transaction.shares_allocated !== null && (
                    <div>
                      <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">Shares</p>
                      <p className="text-lg font-semibold text-slate-900 dark:text-white">
                        {transaction.shares_allocated.toLocaleString()}
                      </p>
                    </div>
                  )}
                </div>

                <div className="mt-4 flex items-center justify-end text-blue-600 dark:text-blue-400 font-medium">
                  <span>View Details</span>
                  <ArrowRight className="w-4 h-4 ml-2" />
                </div>
              </button>
            ))}
          </div>
        )}

        {/* Quick Actions */}
        <div className="mt-12 grid md:grid-cols-3 gap-6">
          <button
            onClick={() => router.push('/financial-hub/agreements')}
            className="p-6 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl hover:shadow-md transition-all"
          >
            <PieChart className="w-8 h-8 text-blue-600 dark:text-blue-400 mb-3" />
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">
              View Agreements
            </h3>
            <p className="text-sm text-slate-600 dark:text-slate-300">
              Review and manage your subscription agreements
            </p>
          </button>

          <button
            onClick={() => router.push('/financial-hub/drs')}
            className="p-6 bg-indigo-50 dark:bg-indigo-900/20 border border-indigo-200 dark:border-indigo-800 rounded-xl hover:shadow-md transition-all"
          >
            <CheckCircle className="w-8 h-8 text-indigo-600 dark:text-indigo-400 mb-3" />
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">
              DRS Documents
            </h3>
            <p className="text-sm text-slate-600 dark:text-slate-300">
              Access your share certificates and documentation
            </p>
          </button>

          <button
            onClick={() => router.push('/companies')}
            className="p-6 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-xl hover:shadow-md transition-all"
          >
            <Building2 className="w-8 h-8 text-green-600 dark:text-green-400 mb-3" />
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">
              Browse Companies
            </h3>
            <p className="text-sm text-slate-600 dark:text-slate-300">
              Discover new investment opportunities
            </p>
          </button>
        </div>
      </div>
    </div>
  );
}
