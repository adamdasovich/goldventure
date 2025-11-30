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

interface SubscriptionAgreement {
  id: number;
  financing: {
    id: number;
    company: {
      id: number;
      name: string;
    };
    price_per_share: string;
  };
  status: string;
  investment_amount: string;
  shares_allocated: number | null;
  warrants_allocated: number | null;
  signed_at: string | null;
  created_at: string;
  updated_at: string;
}

export default function SubscriptionAgreements() {
  const router = useRouter();
  const [agreements, setAgreements] = useState<SubscriptionAgreement[]>([]);
  const [loading, setLoading] = useState(true);
  const [qualified, setQualified] = useState(false);

  useEffect(() => {
    checkQualification();
    fetchAgreements();
  }, []);

  const checkQualification = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/api/qualifications/status/', {
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
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/api/agreements/', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setAgreements(data);
      }
    } catch (error) {
      console.error('Error fetching agreements:', error);
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
      <div className="min-h-screen bg-slate-50 dark:bg-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-slate-600 dark:text-slate-300">Loading subscription agreements...</p>
        </div>
      </div>
    );
  }

  if (!qualified) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
        <div className="container mx-auto px-4 py-12 max-w-4xl">
          <button
            onClick={() => router.push('/financial-hub')}
            className="flex items-center gap-2 text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white mb-4 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Financial Hub
          </button>

          <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-xl p-8 text-center">
            <AlertCircle className="w-16 h-16 text-yellow-600 dark:text-yellow-400 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-3">
              Accreditation Required
            </h2>
            <p className="text-slate-600 dark:text-slate-300 mb-6">
              You must complete the Accredited Investor Qualification to access subscription agreements.
            </p>
            <button
              onClick={() => router.push('/financial-hub/qualification')}
              className="px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors inline-flex items-center gap-2"
            >
              Complete Qualification
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
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
            Subscription Agreements
          </h1>
          <p className="text-lg text-slate-600 dark:text-slate-300 max-w-3xl">
            Review and manage your subscription agreements for mining company financing rounds.
          </p>
        </div>

        {/* Summary Stats */}
        {agreements.length > 0 && (
          <div className="grid md:grid-cols-4 gap-4 mb-8">
            <div className="bg-white dark:bg-slate-800 rounded-xl shadow-md p-6">
              <div className="flex items-center justify-between mb-2">
                <span className="text-slate-600 dark:text-slate-300 text-sm">Total Agreements</span>
                <FileText className="w-5 h-5 text-blue-600 dark:text-blue-400" />
              </div>
              <p className="text-3xl font-bold text-slate-900 dark:text-white">{agreements.length}</p>
            </div>

            <div className="bg-white dark:bg-slate-800 rounded-xl shadow-md p-6">
              <div className="flex items-center justify-between mb-2">
                <span className="text-slate-600 dark:text-slate-300 text-sm">Pending Signature</span>
                <Clock className="w-5 h-5 text-yellow-600 dark:text-yellow-400" />
              </div>
              <p className="text-3xl font-bold text-slate-900 dark:text-white">
                {agreements.filter(a => a.status === 'pending_signature').length}
              </p>
            </div>

            <div className="bg-white dark:bg-slate-800 rounded-xl shadow-md p-6">
              <div className="flex items-center justify-between mb-2">
                <span className="text-slate-600 dark:text-slate-300 text-sm">Total Invested</span>
                <DollarSign className="w-5 h-5 text-green-600 dark:text-green-400" />
              </div>
              <p className="text-3xl font-bold text-slate-900 dark:text-white">
                ${agreements.reduce((sum, a) => sum + parseFloat(a.investment_amount), 0).toLocaleString()}
              </p>
            </div>

            <div className="bg-white dark:bg-slate-800 rounded-xl shadow-md p-6">
              <div className="flex items-center justify-between mb-2">
                <span className="text-slate-600 dark:text-slate-300 text-sm">Completed</span>
                <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400" />
              </div>
              <p className="text-3xl font-bold text-slate-900 dark:text-white">
                {agreements.filter(a => a.status === 'completed').length}
              </p>
            </div>
          </div>
        )}

        {/* Agreements List */}
        {agreements.length === 0 ? (
          <div className="bg-white dark:bg-slate-800 rounded-xl shadow-md p-12 text-center">
            <FileText className="w-16 h-16 text-slate-300 dark:text-slate-600 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-slate-900 dark:text-white mb-2">
              No Subscription Agreements Yet
            </h3>
            <p className="text-slate-600 dark:text-slate-300 mb-6">
              You haven't signed any subscription agreements. Browse available financing opportunities to get started.
            </p>
            <button
              onClick={() => router.push('/companies')}
              className="px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors inline-flex items-center gap-2"
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
                className="w-full bg-white dark:bg-slate-800 rounded-xl shadow-md hover:shadow-xl transition-all duration-300 hover:-translate-y-1 p-6 text-left"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <Building2 className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                      <h3 className="text-xl font-semibold text-slate-900 dark:text-white">
                        {agreement.financing.company.name}
                      </h3>
                    </div>
                    <p className="text-slate-600 dark:text-slate-300">
                      Financing Round #{agreement.financing.id}
                    </p>
                  </div>
                  {getStatusBadge(agreement.status)}
                </div>

                <div className="grid md:grid-cols-4 gap-4">
                  <div>
                    <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">Investment Amount</p>
                    <p className="text-lg font-semibold text-slate-900 dark:text-white">
                      ${parseFloat(agreement.investment_amount).toLocaleString()}
                    </p>
                  </div>

                  <div>
                    <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">Price Per Share</p>
                    <p className="text-lg font-semibold text-slate-900 dark:text-white">
                      ${parseFloat(agreement.financing.price_per_share).toFixed(2)}
                    </p>
                  </div>

                  {agreement.shares_allocated !== null && (
                    <div>
                      <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">Shares Allocated</p>
                      <p className="text-lg font-semibold text-slate-900 dark:text-white">
                        {agreement.shares_allocated.toLocaleString()}
                      </p>
                    </div>
                  )}

                  {agreement.warrants_allocated !== null && agreement.warrants_allocated > 0 && (
                    <div>
                      <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">Warrants</p>
                      <p className="text-lg font-semibold text-slate-900 dark:text-white">
                        {agreement.warrants_allocated.toLocaleString()}
                      </p>
                    </div>
                  )}

                  <div>
                    <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">
                      {agreement.signed_at ? 'Signed On' : 'Created On'}
                    </p>
                    <p className="text-lg font-semibold text-slate-900 dark:text-white flex items-center gap-1">
                      <Calendar className="w-4 h-4" />
                      {new Date(agreement.signed_at || agreement.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>

                <div className="mt-4 flex items-center justify-end text-blue-600 dark:text-blue-400 font-medium">
                  <span>View Details</span>
                  <ArrowRight className="w-4 h-4 ml-2 transition-transform group-hover:translate-x-1" />
                </div>
              </button>
            ))}
          </div>
        )}

        {/* Help Section */}
        <div className="mt-12 p-6 bg-blue-50 dark:bg-blue-900/20 rounded-xl border border-blue-200 dark:border-blue-800">
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">
            About Subscription Agreements
          </h3>
          <p className="text-slate-600 dark:text-slate-300 mb-4">
            A subscription agreement is a legal contract between you and the mining company outlining the terms of your investment in their financing round.
          </p>
          <ul className="space-y-2 text-slate-600 dark:text-slate-300 text-sm">
            <li className="flex items-start gap-2">
              <CheckCircle className="w-5 h-5 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
              <span>Review all terms carefully before signing</span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle className="w-5 h-5 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
              <span>Your shares will be allocated after payment is confirmed</span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle className="w-5 h-5 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
              <span>DRS certificates will be issued once the financing round closes</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}
