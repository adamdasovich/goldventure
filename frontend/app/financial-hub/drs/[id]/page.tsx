'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import {
  ArrowLeft,
  Building2,
  Shield,
  Calendar,
  FileText,
  CheckCircle,
  Clock,
  Download,
  Hash,
  TrendingUp,
  Award,
  ExternalLink,
  Mail,
  Info,
  AlertCircle
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

interface DRSDocumentDetail {
  id: number;
  agreement: SubscriptionAgreement;
  document_type: string;
  certificate_number: string;
  shares_quantity: number;
  issued_date: string;
  delivered_at: string | null;
  file_path: string;
  cusip_number: string | null;
  created_at: string;
  updated_at: string;
}

export default function DRSDocumentDetail() {
  const router = useRouter();
  const params = useParams();
  const [document, setDocument] = useState<DRSDocumentDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (params.id) {
      fetchDocument(params.id as string);
    }
  }, [params.id]);

  const fetchDocument = async (id: string) => {
    try {
      const token = localStorage.getItem('accessToken');
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/api'}/drs/documents/${id}/`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setDocument(data);
      } else {
        alert('Failed to load DRS document details');
        router.push('/financial-hub/drs');
      }
    } catch (error) {
      console.error('Error fetching DRS document:', error);
      alert('Error loading DRS document');
      router.push('/financial-hub/drs');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = () => {
    if (document) {
      window.open(document.file_path, '_blank');
    }
  };

  const getDocumentTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      certificate: 'Share Certificate',
      statement: 'Account Statement',
      confirmation: 'Confirmation of Ownership',
      transfer: 'Transfer Document',
    };
    return labels[type] || type.toUpperCase();
  };

  const getDocumentTypeDescription = (type: string) => {
    const descriptions: Record<string, string> = {
      certificate: 'Official share certificate showing your ownership of the specified number of shares',
      statement: 'Account statement showing your current holdings and transaction history',
      confirmation: 'Confirmation of share ownership registered in your name',
      transfer: 'Document confirming transfer of shares to your DRS account',
    };
    return descriptions[type] || 'DRS document for your investment';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-slate-600 dark:text-slate-300">Loading DRS document...</p>
        </div>
      </div>
    );
  }

  if (!document) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-900 flex items-center justify-center">
        <div className="text-center">
          <Shield className="w-16 h-16 text-slate-300 dark:text-slate-600 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-slate-900 dark:text-white mb-2">
            Document Not Found
          </h3>
          <button
            onClick={() => router.push('/financial-hub/drs')}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Back to DRS Documents
          </button>
        </div>
      </div>
    );
  }

  const shareValue = parseFloat(document.agreement.financing.price_per_share) * document.shares_quantity;

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      <div className="container mx-auto px-4 py-12 max-w-6xl">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => router.push('/financial-hub/drs')}
            className="flex items-center gap-2 text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white mb-4 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to DRS Documents
          </button>

          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-4xl font-bold text-slate-900 dark:text-white mb-2">
                {getDocumentTypeLabel(document.document_type)}
              </h1>
              <p className="text-lg text-slate-600 dark:text-slate-300">
                {document.agreement.financing.company.name}
              </p>
            </div>
            <button
              onClick={handleDownload}
              className="px-6 py-3 bg-indigo-600 text-white font-semibold rounded-lg hover:bg-indigo-700 transition-colors inline-flex items-center gap-2"
            >
              <Download className="w-5 h-5" />
              Download
            </button>
          </div>
        </div>

        {/* Delivery Status Banner */}
        {document.delivered_at ? (
          <div className="mb-6 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-xl p-6">
            <div className="flex items-start gap-4">
              <CheckCircle className="w-6 h-6 text-green-600 dark:text-green-400 mt-1 flex-shrink-0" />
              <div className="flex-1">
                <h3 className="font-semibold text-green-900 dark:text-green-100 mb-2">
                  Document Delivered
                </h3>
                <p className="text-green-800 dark:text-green-200">
                  This document was delivered on {new Date(document.delivered_at).toLocaleDateString()} and is ready for download.
                </p>
              </div>
            </div>
          </div>
        ) : (
          <div className="mb-6 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-xl p-6">
            <div className="flex items-start gap-4">
              <Clock className="w-6 h-6 text-yellow-600 dark:text-yellow-400 mt-1 flex-shrink-0" />
              <div className="flex-1">
                <h3 className="font-semibold text-yellow-900 dark:text-yellow-100 mb-2">
                  Pending Delivery
                </h3>
                <p className="text-yellow-800 dark:text-yellow-200">
                  This document has been issued and is pending delivery. It will be available for download once delivered.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Certificate Details */}
        <div className="bg-white dark:bg-slate-800 rounded-xl shadow-md p-6 mb-6">
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-6 flex items-center gap-2">
            <Shield className="w-6 h-6 text-indigo-600 dark:text-indigo-400" />
            Certificate Details
          </h2>

          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">Certificate Number</p>
              <p className="text-2xl font-mono font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <Hash className="w-6 h-6" />
                {document.certificate_number}
              </p>
            </div>

            <div>
              <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">Document Type</p>
              <p className="text-2xl font-bold text-indigo-600 dark:text-indigo-400">
                {getDocumentTypeLabel(document.document_type)}
              </p>
            </div>

            <div>
              <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">Number of Shares</p>
              <p className="text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <TrendingUp className="w-6 h-6" />
                {document.shares_quantity.toLocaleString()}
              </p>
            </div>

            <div>
              <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">Share Value</p>
              <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                ${shareValue.toLocaleString()}
              </p>
              <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
                @ ${parseFloat(document.agreement.financing.price_per_share).toFixed(2)} per share
              </p>
            </div>

            {document.cusip_number && (
              <div>
                <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">CUSIP Number</p>
                <p className="text-lg font-mono font-semibold text-slate-900 dark:text-white">
                  {document.cusip_number}
                </p>
              </div>
            )}

            <div>
              <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">Issued Date</p>
              <p className="text-lg font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                <Calendar className="w-5 h-5" />
                {new Date(document.issued_date).toLocaleDateString()}
              </p>
            </div>

            {document.delivered_at && (
              <div>
                <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">Delivered On</p>
                <p className="text-lg font-semibold text-green-600 dark:text-green-400 flex items-center gap-2">
                  <Mail className="w-5 h-5" />
                  {new Date(document.delivered_at).toLocaleDateString()}
                </p>
              </div>
            )}
          </div>

          <div className="mt-6 p-4 bg-indigo-50 dark:bg-indigo-900/20 border border-indigo-200 dark:border-indigo-800 rounded-lg">
            <div className="flex items-start gap-3">
              <Info className="w-5 h-5 text-indigo-600 dark:text-indigo-400 mt-0.5 flex-shrink-0" />
              <div>
                <h3 className="font-semibold text-indigo-900 dark:text-indigo-100 mb-1">About This Document</h3>
                <p className="text-indigo-800 dark:text-indigo-200">
                  {getDocumentTypeDescription(document.document_type)}
                </p>
              </div>
            </div>
          </div>

          <div className="mt-6 grid md:grid-cols-2 gap-4 text-sm pt-6 border-t border-slate-200 dark:border-slate-700">
            <div className="flex items-center gap-2 text-slate-600 dark:text-slate-300">
              <Clock className="w-4 h-4" />
              <span>Created: {new Date(document.created_at).toLocaleString()}</span>
            </div>
            <div className="flex items-center gap-2 text-slate-600 dark:text-slate-300">
              <Clock className="w-4 h-4" />
              <span>Updated: {new Date(document.updated_at).toLocaleString()}</span>
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
                #{document.agreement.id}
              </p>
            </div>

            <div>
              <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">Agreement Status</p>
              <p className="text-lg font-semibold text-slate-900 dark:text-white">
                {document.agreement.status.replace('_', ' ').toUpperCase()}
              </p>
            </div>

            <div>
              <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">Total Investment</p>
              <p className="text-lg font-semibold text-slate-900 dark:text-white">
                ${parseFloat(document.agreement.investment_amount).toLocaleString()}
              </p>
            </div>

            {document.agreement.shares_allocated !== null && (
              <div>
                <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">Total Shares Allocated</p>
                <p className="text-lg font-semibold text-slate-900 dark:text-white">
                  {document.agreement.shares_allocated.toLocaleString()}
                </p>
              </div>
            )}

            {document.agreement.warrants_allocated !== null && document.agreement.warrants_allocated > 0 && (
              <div>
                <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">Warrants Allocated</p>
                <p className="text-lg font-semibold text-slate-900 dark:text-white">
                  {document.agreement.warrants_allocated.toLocaleString()}
                </p>
              </div>
            )}

            {document.agreement.signed_at && (
              <div>
                <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">Signed On</p>
                <p className="text-lg font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400" />
                  {new Date(document.agreement.signed_at).toLocaleDateString()}
                </p>
              </div>
            )}
          </div>

          <div className="mt-6">
            <button
              onClick={() => router.push(`/financial-hub/agreements/${document.agreement.id}`)}
              className="px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors inline-flex items-center gap-2"
            >
              View Agreement Details
              <ExternalLink className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Company Information */}
        <div className="bg-white dark:bg-slate-800 rounded-xl shadow-md p-6 mb-6">
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-6 flex items-center gap-2">
            <Building2 className="w-6 h-6 text-slate-600 dark:text-slate-400" />
            Company Information
          </h2>

          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">Company Name</p>
              <p className="text-lg font-semibold text-slate-900 dark:text-white">
                {document.agreement.financing.company.name}
              </p>
            </div>

            <div>
              <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">Ticker Symbol</p>
              <p className="text-lg font-semibold text-slate-900 dark:text-white">
                {document.agreement.financing.company.ticker_symbol}
              </p>
            </div>

            <div>
              <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">Financing Round</p>
              <p className="text-lg font-semibold text-slate-900 dark:text-white">
                #{document.agreement.financing.id}
              </p>
            </div>

            <div>
              <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">Price Per Share</p>
              <p className="text-lg font-semibold text-slate-900 dark:text-white">
                ${parseFloat(document.agreement.financing.price_per_share).toFixed(2)}
              </p>
            </div>
          </div>

          <div className="mt-6">
            <button
              onClick={() => router.push(`/companies/${document.agreement.financing.company.id}`)}
              className="px-6 py-3 bg-slate-600 text-white font-semibold rounded-lg hover:bg-slate-700 transition-colors inline-flex items-center gap-2"
            >
              View Company Profile
              <ExternalLink className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Important Information */}
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl p-6">
          <div className="flex items-start gap-4">
            <Award className="w-8 h-8 text-blue-600 dark:text-blue-400 mt-1 flex-shrink-0" />
            <div>
              <h3 className="text-lg font-semibold text-blue-900 dark:text-blue-100 mb-3">
                Important Information
              </h3>
              <ul className="space-y-2 text-blue-800 dark:text-blue-200 text-sm">
                <li className="flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
                  <span>This certificate represents direct ownership of shares registered in your name</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
                  <span>Keep this document in a safe place as proof of ownership</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
                  <span>You can download and print this certificate at any time</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
                  <span>Contact support if you need assistance with your DRS documents</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
