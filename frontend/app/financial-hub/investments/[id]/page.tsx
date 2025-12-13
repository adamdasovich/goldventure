'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import {
  ArrowLeft,
  Building2,
  DollarSign,
  Calendar,
  FileText,
  CheckCircle,
  Clock,
  Activity,
  AlertCircle,
  TrendingUp,
  Hash,
  Info,
  ExternalLink
} from 'lucide-react';

interface Company {
  id: number;
  name: string;
  ticker_symbol: string;
}

interface Financing {
  id: number;
  company: Company;
  price_per_share: string;
  min_subscription: string;
  max_subscription: string;
}

interface SubscriptionAgreement {
  id: number;
  financing: Financing;
  investment_amount: string;
  shares_allocated: number | null;
  warrants_allocated: number | null;
  status: string;
  signed_at: string | null;
}

interface InvestmentTransactionDetail {
  id: number;
  agreement: SubscriptionAgreement;
  transaction_type: string;
  amount: string;
  status: string;
  transaction_date: string;
  reference_number: string;
  notes: string;
  created_at: string;
  updated_at: string;
}

export default function TransactionDetail() {
  const router = useRouter();
  const params = useParams();
  const [transaction, setTransaction] = useState<InvestmentTransactionDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (params.id) {
      fetchTransaction(params.id as string);
    }
  }, [params.id]);

  const fetchTransaction = async (id: string) => {
    try {
      const token = localStorage.getItem('accessToken');
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/api'}/investments/transactions/${id}/`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setTransaction(data);
      } else {
        alert('Failed to load transaction details');
        router.push('/financial-hub/investments');
      }
    } catch (error) {
      console.error('Error fetching transaction:', error);
      alert('Error loading transaction');
      router.push('/financial-hub/investments');
    } finally {
      setLoading(false);
    }
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
      <span className={`inline-flex items-center gap-1.5 px-4 py-2 rounded-full text-sm font-medium ${config.color}`}>
        <Icon className="w-4 h-4" />
        {config.label}
      </span>
    );
  };

  const getTransactionTypeInfo = (type: string) => {
    const types: Record<string, { label: string; color: string; description: string }> = {
      investment: {
        label: 'Investment',
        color: 'text-green-600 dark:text-green-400',
        description: 'Initial investment in the financing round'
      },
      dividend: {
        label: 'Dividend',
        color: 'text-blue-600 dark:text-blue-400',
        description: 'Dividend payment from company'
      },
      refund: {
        label: 'Refund',
        color: 'text-orange-600 dark:text-orange-400',
        description: 'Refund of investment amount'
      },
      fee: {
        label: 'Fee',
        color: 'text-red-600 dark:text-red-400',
        description: 'Administrative or processing fee'
      },
      transfer: {
        label: 'Transfer',
        color: 'text-purple-600 dark:text-purple-400',
        description: 'Transfer between accounts'
      },
    };
    return types[type] || types.investment;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-slate-600 dark:text-slate-300">Loading transaction details...</p>
        </div>
      </div>
    );
  }

  if (!transaction) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-900 flex items-center justify-center">
        <div className="text-center">
          <Activity className="w-16 h-16 text-slate-300 dark:text-slate-600 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-slate-900 dark:text-white mb-2">
            Transaction Not Found
          </h3>
          <button
            onClick={() => router.push('/financial-hub/investments')}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Back to Investments
          </button>
        </div>
      </div>
    );
  }

  const typeInfo = getTransactionTypeInfo(transaction.transaction_type);

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      <div className="container mx-auto px-4 py-12 max-w-6xl">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => router.push('/financial-hub/investments')}
            className="flex items-center gap-2 text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white mb-4 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Investments
          </button>

          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-4xl font-bold text-slate-900 dark:text-white mb-2">
                Transaction #{transaction.id}
              </h1>
              <p className="text-lg text-slate-600 dark:text-slate-300">
                {transaction.agreement.financing.company.name}
              </p>
            </div>
            {getStatusBadge(transaction.status)}
          </div>
        </div>

        {/* Transaction Summary */}
        <div className="bg-white dark:bg-slate-800 rounded-xl shadow-md p-6 mb-6">
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-6 flex items-center gap-2">
            <Activity className="w-6 h-6 text-blue-600 dark:text-blue-400" />
            Transaction Details
          </h2>

          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">Transaction Type</p>
              <p className={`text-2xl font-bold ${typeInfo.color}`}>
                {typeInfo.label}
              </p>
              <p className="text-sm text-slate-600 dark:text-slate-300 mt-1">
                {typeInfo.description}
              </p>
            </div>

            <div>
              <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">Amount</p>
              <p className="text-2xl font-bold text-slate-900 dark:text-white">
                ${parseFloat(transaction.amount).toLocaleString()}
              </p>
            </div>

            <div>
              <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">Transaction Date</p>
              <p className="text-lg font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                <Calendar className="w-5 h-5" />
                {new Date(transaction.transaction_date).toLocaleString()}
              </p>
            </div>

            {transaction.reference_number && (
              <div>
                <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">Reference Number</p>
                <p className="text-lg font-mono font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                  <Hash className="w-5 h-5" />
                  {transaction.reference_number}
                </p>
              </div>
            )}
          </div>

          {transaction.notes && (
            <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
              <div className="flex items-start gap-3">
                <Info className="w-5 h-5 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
                <div>
                  <h3 className="font-semibold text-blue-900 dark:text-blue-100 mb-1">Notes</h3>
                  <p className="text-blue-800 dark:text-blue-200 whitespace-pre-wrap">
                    {transaction.notes}
                  </p>
                </div>
              </div>
            </div>
          )}

          <div className="mt-6 grid md:grid-cols-2 gap-4 text-sm pt-6 border-t border-slate-200 dark:border-slate-700">
            <div className="flex items-center gap-2 text-slate-600 dark:text-slate-300">
              <Clock className="w-4 h-4" />
              <span>Created: {new Date(transaction.created_at).toLocaleString()}</span>
            </div>
            <div className="flex items-center gap-2 text-slate-600 dark:text-slate-300">
              <Clock className="w-4 h-4" />
              <span>Updated: {new Date(transaction.updated_at).toLocaleString()}</span>
            </div>
          </div>
        </div>

        {/* Related Agreement */}
        <div className="bg-white dark:bg-slate-800 rounded-xl shadow-md p-6 mb-6">
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-6 flex items-center gap-2">
            <FileText className="w-6 h-6 text-green-600 dark:text-green-400" />
            Related Subscription Agreement
          </h2>

          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">Agreement ID</p>
              <p className="text-lg font-semibold text-slate-900 dark:text-white">
                #{transaction.agreement.id}
              </p>
            </div>

            <div>
              <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">Agreement Status</p>
              <p className="text-lg font-semibold text-slate-900 dark:text-white">
                {transaction.agreement.status.replace('_', ' ').toUpperCase()}
              </p>
            </div>

            <div>
              <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">Total Investment</p>
              <p className="text-lg font-semibold text-slate-900 dark:text-white">
                ${parseFloat(transaction.agreement.investment_amount).toLocaleString()}
              </p>
            </div>

            {transaction.agreement.shares_allocated !== null && (
              <div>
                <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">Shares Allocated</p>
                <p className="text-lg font-semibold text-slate-900 dark:text-white">
                  {transaction.agreement.shares_allocated.toLocaleString()}
                </p>
              </div>
            )}

            {transaction.agreement.warrants_allocated !== null && transaction.agreement.warrants_allocated > 0 && (
              <div>
                <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">Warrants Allocated</p>
                <p className="text-lg font-semibold text-slate-900 dark:text-white">
                  {transaction.agreement.warrants_allocated.toLocaleString()}
                </p>
              </div>
            )}

            {transaction.agreement.signed_at && (
              <div>
                <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">Signed On</p>
                <p className="text-lg font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400" />
                  {new Date(transaction.agreement.signed_at).toLocaleDateString()}
                </p>
              </div>
            )}
          </div>

          <div className="mt-6">
            <button
              onClick={() => router.push(`/financial-hub/agreements/${transaction.agreement.id}`)}
              className="px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors inline-flex items-center gap-2"
            >
              View Agreement Details
              <ExternalLink className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Company & Financing Information */}
        <div className="bg-white dark:bg-slate-800 rounded-xl shadow-md p-6">
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-6 flex items-center gap-2">
            <Building2 className="w-6 h-6 text-slate-600 dark:text-slate-400" />
            Company & Financing Information
          </h2>

          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">Company Name</p>
              <p className="text-lg font-semibold text-slate-900 dark:text-white">
                {transaction.agreement.financing.company.name}
              </p>
            </div>

            <div>
              <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">Ticker Symbol</p>
              <p className="text-lg font-semibold text-slate-900 dark:text-white">
                {transaction.agreement.financing.company.ticker_symbol}
              </p>
            </div>

            <div>
              <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">Financing Round</p>
              <p className="text-lg font-semibold text-slate-900 dark:text-white">
                #{transaction.agreement.financing.id}
              </p>
            </div>

            <div>
              <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">Price Per Share</p>
              <p className="text-lg font-semibold text-slate-900 dark:text-white">
                ${parseFloat(transaction.agreement.financing.price_per_share).toFixed(2)}
              </p>
            </div>

            <div>
              <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">Min Subscription</p>
              <p className="text-lg font-semibold text-slate-900 dark:text-white">
                ${parseFloat(transaction.agreement.financing.min_subscription).toLocaleString()}
              </p>
            </div>

            <div>
              <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">Max Subscription</p>
              <p className="text-lg font-semibold text-slate-900 dark:text-white">
                ${parseFloat(transaction.agreement.financing.max_subscription).toLocaleString()}
              </p>
            </div>
          </div>

          <div className="mt-6">
            <button
              onClick={() => router.push(`/companies/${transaction.agreement.financing.company.id}`)}
              className="px-6 py-3 bg-slate-600 text-white font-semibold rounded-lg hover:bg-slate-700 transition-colors inline-flex items-center gap-2"
            >
              View Company Profile
              <ExternalLink className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Status Timeline */}
        {transaction.status === 'completed' && (
          <div className="mt-6 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-xl p-6">
            <div className="flex items-start gap-4">
              <CheckCircle className="w-8 h-8 text-green-600 dark:text-green-400 mt-1 flex-shrink-0" />
              <div>
                <h3 className="text-lg font-semibold text-green-900 dark:text-green-100 mb-2">
                  Transaction Completed
                </h3>
                <p className="text-green-800 dark:text-green-200">
                  This transaction has been successfully processed and completed. All funds have been transferred and recorded.
                </p>
              </div>
            </div>
          </div>
        )}

        {transaction.status === 'pending' && (
          <div className="mt-6 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-xl p-6">
            <div className="flex items-start gap-4">
              <Clock className="w-8 h-8 text-yellow-600 dark:text-yellow-400 mt-1 flex-shrink-0" />
              <div>
                <h3 className="text-lg font-semibold text-yellow-900 dark:text-yellow-100 mb-2">
                  Transaction Pending
                </h3>
                <p className="text-yellow-800 dark:text-yellow-200">
                  This transaction is awaiting processing. It will be completed once the payment is verified and funds are transferred.
                </p>
              </div>
            </div>
          </div>
        )}

        {transaction.status === 'failed' && (
          <div className="mt-6 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-6">
            <div className="flex items-start gap-4">
              <AlertCircle className="w-8 h-8 text-red-600 dark:text-red-400 mt-1 flex-shrink-0" />
              <div>
                <h3 className="text-lg font-semibold text-red-900 dark:text-red-100 mb-2">
                  Transaction Failed
                </h3>
                <p className="text-red-800 dark:text-red-200">
                  This transaction could not be completed. Please contact support for assistance or try submitting a new transaction.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
