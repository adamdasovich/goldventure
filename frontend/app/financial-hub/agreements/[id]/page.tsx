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
  TrendingUp,
  CreditCard,
  Shield,
  AlertCircle,
  Download,
  Edit3
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
  has_warrants: boolean;
  warrant_exercise_price: string | null;
  warrant_expiry_years: number | null;
}

interface InvestmentTransaction {
  id: number;
  transaction_type: string;
  amount: string;
  status: string;
  transaction_date: string;
  notes: string;
}

interface PaymentInstruction {
  id: number;
  payment_method: string;
  amount: string;
  instructions: string;
  due_date: string;
  paid_at: string | null;
}

interface DRSDocument {
  id: number;
  document_type: string;
  document_url: string;
  num_shares: number;
  issue_date: string;
  delivered_at: string | null;
  delivery_status: string;
}

interface SubscriptionAgreementDetail {
  id: number;
  investor: {
    id: number;
    username: string;
    email: string;
  };
  company: Company;
  financing: Financing;
  status: string;
  status_display: string;
  total_investment_amount: string;
  num_shares: number | null;
  warrant_shares: number | null;
  investor_signed_at: string | null;
  docusign_envelope_id: string | null;
  created_at: string;
  updated_at: string;
  transactions: InvestmentTransaction[];
  payment_instruction: PaymentInstruction | null;
  drs_documents: DRSDocument[];
}

export default function AgreementDetail() {
  const router = useRouter();
  const params = useParams();
  const [agreement, setAgreement] = useState<SubscriptionAgreementDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [signing, setSigning] = useState(false);

  useEffect(() => {
    if (params.id) {
      fetchAgreement(params.id as string);
    }
  }, [params.id]);

  const fetchAgreement = async (id: string) => {
    try {
      const token = localStorage.getItem('accessToken');
      const response = await fetch(`http://localhost:8000/api/agreements/${id}/`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setAgreement(data);
      } else {
        alert('Failed to load agreement details');
        router.push('/financial-hub/agreements');
      }
    } catch (error) {
      console.error('Error fetching agreement:', error);
      alert('Error loading agreement');
      router.push('/financial-hub/agreements');
    } finally {
      setLoading(false);
    }
  };

  const handleSign = async () => {
    if (!agreement) return;

    setSigning(true);
    try {
      const token = localStorage.getItem('accessToken');
      const response = await fetch(`http://localhost:8000/api/agreements/${agreement.id}/sign/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        await fetchAgreement(params.id as string);
        alert('Agreement signed successfully!');
      } else {
        const error = await response.json();
        alert(`Failed to sign agreement: ${error.error || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error signing agreement:', error);
      alert('Error signing agreement');
    } finally {
      setSigning(false);
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
      <span className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium ${config.color}`}>
        <Icon className="w-4 h-4" />
        {config.label}
      </span>
    );
  };

  const getTransactionStatusBadge = (status: string) => {
    const colors: Record<string, string> = {
      pending: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300',
      processing: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
      completed: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300',
      failed: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300',
      cancelled: 'bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-300',
      refunded: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-300',
      on_hold: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300',
    };

    return (
      <span className={`px-2 py-1 rounded text-xs font-medium ${colors[status] || colors.pending}`}>
        {status.replace('_', ' ').toUpperCase()}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-slate-600 dark:text-slate-300">Loading agreement details...</p>
        </div>
      </div>
    );
  }

  if (!agreement) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-900 flex items-center justify-center">
        <div className="text-center">
          <FileText className="w-16 h-16 text-slate-300 dark:text-slate-600 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-slate-900 dark:text-white mb-2">
            Agreement Not Found
          </h3>
          <button
            onClick={() => router.push('/financial-hub/agreements')}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Back to Agreements
          </button>
        </div>
      </div>
    );
  }

  const canSign = agreement.status === 'pending_signature';
  const showPaymentInfo = ['payment_pending', 'payment_received', 'shares_allocated', 'drs_issued', 'completed'].includes(agreement.status);

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      <div className="container mx-auto px-4 py-12 max-w-6xl">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => router.push('/financial-hub/agreements')}
            className="flex items-center gap-2 text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white mb-4 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Agreements
          </button>

          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-4xl font-bold text-slate-900 dark:text-white mb-2">
                Subscription Agreement #{agreement.id}
              </h1>
              <p className="text-lg text-slate-600 dark:text-slate-300">
                {agreement.financing.company.name} - Financing Round #{agreement.financing.id}
              </p>
            </div>
            {getStatusBadge(agreement.status)}
          </div>
        </div>

        {/* Sign Agreement Alert */}
        {canSign && (
          <div className="mb-6 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-xl p-6">
            <div className="flex items-start gap-4">
              <AlertCircle className="w-6 h-6 text-yellow-600 dark:text-yellow-400 mt-1 flex-shrink-0" />
              <div className="flex-1">
                <h3 className="font-semibold text-yellow-900 dark:text-yellow-100 mb-2">
                  Signature Required
                </h3>
                <p className="text-yellow-800 dark:text-yellow-200 mb-4">
                  This subscription agreement is ready for your signature. Please review all terms carefully before signing.
                </p>
                <button
                  onClick={handleSign}
                  disabled={signing}
                  className="px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed inline-flex items-center gap-2"
                >
                  {signing ? (
                    <>
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                      Signing...
                    </>
                  ) : (
                    <>
                      <Edit3 className="w-5 h-5" />
                      Sign Agreement
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Investment Summary */}
        <div className="bg-white dark:bg-slate-800 rounded-xl shadow-md p-6 mb-6">
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-6 flex items-center gap-2">
            <TrendingUp className="w-6 h-6 text-blue-600 dark:text-blue-400" />
            Investment Summary
          </h2>

          <div className="grid md:grid-cols-3 gap-6">
            <div>
              <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">Investment Amount</p>
              <p className="text-2xl font-bold text-slate-900 dark:text-white">
                ${parseFloat(agreement.total_investment_amount).toLocaleString()}
              </p>
            </div>

            <div>
              <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">Price Per Share</p>
              <p className="text-2xl font-bold text-slate-900 dark:text-white">
                ${parseFloat(agreement.financing.price_per_share).toFixed(2)}
              </p>
            </div>

            {agreement.num_shares !== null && (
              <div>
                <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">Shares Allocated</p>
                <p className="text-2xl font-bold text-slate-900 dark:text-white">
                  {agreement.num_shares.toLocaleString()}
                </p>
              </div>
            )}
          </div>

          {agreement.financing.has_warrants && (
            <div className="mt-6 p-4 bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800 rounded-lg">
              <h3 className="font-semibold text-purple-900 dark:text-purple-100 mb-2">
                Warrant Information
              </h3>
              <div className="grid md:grid-cols-3 gap-4">
                {agreement.warrant_shares !== null && (
                  <div>
                    <p className="text-sm text-purple-700 dark:text-purple-300 mb-1">Warrants Allocated</p>
                    <p className="text-lg font-semibold text-purple-900 dark:text-purple-100">
                      {agreement.warrant_shares.toLocaleString()}
                    </p>
                  </div>
                )}
                <div>
                  <p className="text-sm text-purple-700 dark:text-purple-300 mb-1">Exercise Price</p>
                  <p className="text-lg font-semibold text-purple-900 dark:text-purple-100">
                    ${agreement.financing.warrant_exercise_price}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-purple-700 dark:text-purple-300 mb-1">Expiry</p>
                  <p className="text-lg font-semibold text-purple-900 dark:text-purple-100">
                    {agreement.financing.warrant_expiry_years} years
                  </p>
                </div>
              </div>
            </div>
          )}

          <div className="mt-6 grid md:grid-cols-2 gap-4 text-sm">
            <div className="flex items-center gap-2 text-slate-600 dark:text-slate-300">
              <Calendar className="w-4 h-4" />
              <span>Created: {new Date(agreement.created_at).toLocaleString()}</span>
            </div>
            {agreement.investor_signed_at && (
              <div className="flex items-center gap-2 text-green-600 dark:text-green-400">
                <CheckCircle className="w-4 h-4" />
                <span>Signed: {new Date(agreement.investor_signed_at).toLocaleString()}</span>
              </div>
            )}
          </div>
        </div>

        {/* Payment Instructions */}
        {showPaymentInfo && agreement.payment_instruction && agreement.payment_instruction.length > 0 && (
          <div className="bg-white dark:bg-slate-800 rounded-xl shadow-md p-6 mb-6">
            <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-6 flex items-center gap-2">
              <CreditCard className="w-6 h-6 text-green-600 dark:text-green-400" />
              Payment Instructions
            </h2>

            <div className="space-y-4">
              {agreement.payment_instruction.map((instruction) => (
                <div
                  key={instruction.id}
                  className={`p-4 rounded-lg border ${
                    instruction.paid_at
                      ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800'
                      : 'bg-orange-50 dark:bg-orange-900/20 border-orange-200 dark:border-orange-800'
                  }`}
                >
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h3 className="font-semibold text-slate-900 dark:text-white mb-1">
                        {instruction.payment_method.replace('_', ' ').toUpperCase()}
                      </h3>
                      <p className="text-2xl font-bold text-slate-900 dark:text-white">
                        ${parseFloat(instruction.amount).toLocaleString()}
                      </p>
                    </div>
                    {instruction.paid_at ? (
                      <span className="px-3 py-1 bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300 rounded-full text-sm font-medium">
                        Paid
                      </span>
                    ) : (
                      <span className="px-3 py-1 bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-300 rounded-full text-sm font-medium">
                        Pending
                      </span>
                    )}
                  </div>

                  <div className="mb-3">
                    <p className="text-sm text-slate-600 dark:text-slate-300 whitespace-pre-wrap">
                      {instruction.instructions}
                    </p>
                  </div>

                  <div className="flex items-center gap-4 text-sm">
                    <span className="text-slate-600 dark:text-slate-300">
                      Due: {new Date(instruction.due_date).toLocaleDateString()}
                    </span>
                    {instruction.paid_at && (
                      <span className="text-green-600 dark:text-green-400">
                        Paid: {new Date(instruction.paid_at).toLocaleDateString()}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Transaction History */}
        {agreement.transactions.length > 0 && (
          <div className="bg-white dark:bg-slate-800 rounded-xl shadow-md p-6 mb-6">
            <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-6 flex items-center gap-2">
              <DollarSign className="w-6 h-6 text-blue-600 dark:text-blue-400" />
              Transaction History
            </h2>

            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-slate-200 dark:border-slate-700">
                    <th className="text-left py-3 px-4 text-sm font-semibold text-slate-600 dark:text-slate-300">
                      Date
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-slate-600 dark:text-slate-300">
                      Type
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-slate-600 dark:text-slate-300">
                      Amount
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-slate-600 dark:text-slate-300">
                      Status
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-slate-600 dark:text-slate-300">
                      Notes
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {agreement.transactions.map((transaction) => (
                    <tr
                      key={transaction.id}
                      className="border-b border-slate-100 dark:border-slate-700/50 hover:bg-slate-50 dark:hover:bg-slate-700/50"
                    >
                      <td className="py-3 px-4 text-slate-900 dark:text-white">
                        {new Date(transaction.transaction_date).toLocaleDateString()}
                      </td>
                      <td className="py-3 px-4 text-slate-900 dark:text-white">
                        {transaction.transaction_type.replace('_', ' ').toUpperCase()}
                      </td>
                      <td className="py-3 px-4 text-slate-900 dark:text-white font-semibold">
                        ${parseFloat(transaction.amount).toLocaleString()}
                      </td>
                      <td className="py-3 px-4">
                        {getTransactionStatusBadge(transaction.status)}
                      </td>
                      <td className="py-3 px-4 text-slate-600 dark:text-slate-300 text-sm">
                        {transaction.notes || '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* DRS Documents */}
        {agreement.drs_documents.length > 0 && (
          <div className="bg-white dark:bg-slate-800 rounded-xl shadow-md p-6 mb-6">
            <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-6 flex items-center gap-2">
              <Shield className="w-6 h-6 text-indigo-600 dark:text-indigo-400" />
              DRS Documents
            </h2>

            <div className="space-y-4">
              {agreement.drs_documents.map((doc) => (
                <div
                  key={doc.id}
                  className="p-4 bg-indigo-50 dark:bg-indigo-900/20 border border-indigo-200 dark:border-indigo-800 rounded-lg"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h3 className="font-semibold text-indigo-900 dark:text-indigo-100 mb-2">
                        {doc.document_type.replace('_', ' ').toUpperCase()}
                      </h3>
                      <div className="grid md:grid-cols-3 gap-4 text-sm">
                        <div>
                          <p className="text-indigo-700 dark:text-indigo-300 mb-1">Shares</p>
                          <p className="font-semibold text-indigo-900 dark:text-indigo-100">
                            {doc.num_shares.toLocaleString()}
                          </p>
                        </div>
                        <div>
                          <p className="text-indigo-700 dark:text-indigo-300 mb-1">Issued</p>
                          <p className="font-semibold text-indigo-900 dark:text-indigo-100">
                            {new Date(doc.issue_date).toLocaleDateString()}
                          </p>
                        </div>
                        {doc.delivered_at && (
                          <div>
                            <p className="text-indigo-700 dark:text-indigo-300 mb-1">Delivered</p>
                            <p className="font-semibold text-indigo-900 dark:text-indigo-100">
                              {new Date(doc.delivered_at).toLocaleDateString()}
                            </p>
                          </div>
                        )}
                      </div>
                    </div>
                    <button
                      onClick={() => window.open(doc.document_url, '_blank')}
                      className="ml-4 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors inline-flex items-center gap-2"
                    >
                      <Download className="w-4 h-4" />
                      Download
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Company Information */}
        <div className="bg-white dark:bg-slate-800 rounded-xl shadow-md p-6">
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-6 flex items-center gap-2">
            <Building2 className="w-6 h-6 text-slate-600 dark:text-slate-400" />
            Company Information
          </h2>

          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">Company Name</p>
              <p className="text-lg font-semibold text-slate-900 dark:text-white">
                {agreement.financing.company.name}
              </p>
            </div>

            <div>
              <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">Ticker Symbol</p>
              <p className="text-lg font-semibold text-slate-900 dark:text-white">
                {agreement.financing.company.ticker_symbol}
              </p>
            </div>

            <div>
              <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">Min Subscription</p>
              <p className="text-lg font-semibold text-slate-900 dark:text-white">
                ${parseFloat(agreement.financing.min_subscription).toLocaleString()}
              </p>
            </div>

            <div>
              <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">Max Subscription</p>
              <p className="text-lg font-semibold text-slate-900 dark:text-white">
                ${parseFloat(agreement.financing.max_subscription).toLocaleString()}
              </p>
            </div>
          </div>

          <div className="mt-6">
            <button
              onClick={() => router.push(`/companies/${agreement.financing.company.id}`)}
              className="px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors inline-flex items-center gap-2"
            >
              View Company Details
              <ArrowLeft className="w-4 h-4 rotate-180" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
