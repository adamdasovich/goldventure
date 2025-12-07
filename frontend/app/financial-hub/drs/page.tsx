'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  Shield,
  ArrowLeft,
  Download,
  Calendar,
  Building2,
  FileText,
  CheckCircle,
  Clock,
  Award,
  ArrowRight,
  Info,
  TrendingUp,
  AlertCircle,
  Mail
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
}

interface SubscriptionAgreement {
  id: number;
  financing: Financing;
  total_investment_amount: string;
  num_shares: number | null;
}

interface DRSDocument {
  id: number;
  subscription_agreement: SubscriptionAgreement;
  document_type: string;
  certificate_number: string;
  num_shares: number;
  issue_date: string;
  delivered_at: string | null;
  delivery_status: string;
  document_url: string;
  created_at: string;
}

interface DRSSummary {
  total_documents: number;
  total_shares: number;
  delivered_documents: number;
  pending_documents: number;
  unique_companies: number;
}

export default function DRSDocuments() {
  const router = useRouter();
  const [documents, setDocuments] = useState<DRSDocument[]>([]);
  const [summary, setSummary] = useState<DRSSummary>({
    total_documents: 0,
    total_shares: 0,
    delivered_documents: 0,
    pending_documents: 0,
    unique_companies: 0,
  });
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'delivered' | 'pending'>('all');
  const [showLogin, setShowLogin] = useState(false);
  const [showRegister, setShowRegister] = useState(false);
  const { user, logout } = useAuth();

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    try {
      const token = localStorage.getItem('accessToken');
      const response = await fetch('https://api.juniorgoldminingintelligence.com/api/drs/documents/', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        const docsArray = Array.isArray(data) ? data : [];
        setDocuments(docsArray);
        calculateSummary(docsArray);
      } else {
        setDocuments([]);
        calculateSummary([]);
      }
    } catch (error) {
      console.error('Error fetching DRS documents:', error);
      setDocuments([]);
      calculateSummary([]);
    } finally {
      setLoading(false);
    }
  };

  const calculateSummary = (docs: DRSDocument[]) => {
    const uniqueCompanies = new Set(docs.map(d => d.subscription_agreement.financing.company.id));

    setSummary({
      total_documents: docs.length,
      total_shares: docs.reduce((sum, d) => sum + d.num_shares, 0),
      delivered_documents: docs.filter(d => d.delivered_at !== null).length,
      pending_documents: docs.filter(d => d.delivered_at === null).length,
      unique_companies: uniqueCompanies.size,
    });
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

  const getDocumentTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      certificate: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
      statement: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300',
      confirmation: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300',
      transfer: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-300',
    };
    return colors[type] || 'bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-300';
  };

  const filteredDocuments = documents.filter(doc => {
    if (filter === 'all') return true;
    if (filter === 'delivered') return doc.delivered_at !== null;
    if (filter === 'pending') return doc.delivered_at === null;
    return true;
  });

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gold-400 mx-auto mb-4"></div>
          <p className="text-slate-300">Loading DRS documents...</p>
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
              DRS Documents
            </h1>
            <p className="text-xl text-slate-300 max-w-3xl mx-auto">
              View and manage your Direct Registration System (DRS) documents and share certificates.
            </p>
          </div>
        </div>
      </section>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 -mt-8">{/* Overlap section */}

        {/* Educational Banner */}
        <div className="mb-8 backdrop-blur-sm bg-slate-800/30 border border-gold-400/20 rounded-xl p-6">
          <div className="flex items-start gap-4">
            <Shield className="w-8 h-8 text-gold-400 mt-1 flex-shrink-0" />
            <div className="flex-1">
              <h3 className="text-xl font-semibold text-white mb-2">
                What is DRS?
              </h3>
              <p className="text-slate-300 mb-4">
                The Direct Registration System (DRS) allows investors to hold securities in book-entry form directly with the issuer or transfer agent,
                rather than through a broker. This provides direct proof of ownership and eliminates the risk of broker insolvency.
              </p>
              <div className="grid md:grid-cols-3 gap-4">
                <div className="flex items-start gap-2">
                  <CheckCircle className="w-5 h-5 text-gold-400 mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="font-semibold text-white text-sm">Direct Ownership</p>
                    <p className="text-slate-300 text-sm">Shares registered in your name</p>
                  </div>
                </div>
                <div className="flex items-start gap-2">
                  <CheckCircle className="w-5 h-5 text-gold-400 mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="font-semibold text-white text-sm">No Broker Required</p>
                    <p className="text-slate-300 text-sm">Hold shares independently</p>
                  </div>
                </div>
                <div className="flex items-start gap-2">
                  <CheckCircle className="w-5 h-5 text-gold-400 mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="font-semibold text-white text-sm">Electronic Records</p>
                    <p className="text-slate-300 text-sm">Digital certificates & statements</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Summary Stats */}
        {documents.length > 0 && (
          <div className="grid md:grid-cols-5 gap-4 mb-8">
            <div className="backdrop-blur-sm bg-slate-800/50 border border-slate-700/50 rounded-xl p-6">
              <div className="flex items-center justify-between mb-2">
                <span className="text-slate-300 text-sm">Total Documents</span>
                <FileText className="w-5 h-5 text-gold-400" />
              </div>
              <p className="text-3xl font-bold text-white">
                {summary.total_documents}
              </p>
            </div>

            <div className="backdrop-blur-sm bg-slate-800/50 border border-slate-700/50 rounded-xl p-6">
              <div className="flex items-center justify-between mb-2">
                <span className="text-slate-300 text-sm">Total Shares</span>
                <TrendingUp className="w-5 h-5 text-green-400" />
              </div>
              <p className="text-3xl font-bold text-white">
                {summary.total_shares.toLocaleString()}
              </p>
            </div>

            <div className="backdrop-blur-sm bg-slate-800/50 border border-slate-700/50 rounded-xl p-6">
              <div className="flex items-center justify-between mb-2">
                <span className="text-slate-300 text-sm">Delivered</span>
                <CheckCircle className="w-5 h-5 text-green-400" />
              </div>
              <p className="text-3xl font-bold text-white">
                {summary.delivered_documents}
              </p>
            </div>

            <div className="backdrop-blur-sm bg-slate-800/50 border border-slate-700/50 rounded-xl p-6">
              <div className="flex items-center justify-between mb-2">
                <span className="text-slate-300 text-sm">Pending</span>
                <Clock className="w-5 h-5 text-yellow-400" />
              </div>
              <p className="text-3xl font-bold text-white">
                {summary.pending_documents}
              </p>
            </div>

            <div className="backdrop-blur-sm bg-slate-800/50 border border-slate-700/50 rounded-xl p-6">
              <div className="flex items-center justify-between mb-2">
                <span className="text-slate-300 text-sm">Companies</span>
                <Building2 className="w-5 h-5 text-purple-400" />
              </div>
              <p className="text-3xl font-bold text-white">
                {summary.unique_companies}
              </p>
            </div>
          </div>
        )}

        {/* Document Filters */}
        <div className="backdrop-blur-sm bg-slate-800/50 border border-slate-700/50 rounded-xl p-4 mb-6">
          <div className="flex items-center gap-4">
            <span className="text-sm font-semibold text-slate-300">Filter:</span>
            <div className="flex gap-2">
              {(['all', 'delivered', 'pending'] as const).map((f) => (
                <button
                  key={f}
                  onClick={() => setFilter(f)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    filter === f
                      ? 'bg-gold-400 text-slate-900'
                      : 'bg-slate-700/50 text-slate-300 hover:bg-slate-700'
                  }`}
                >
                  {f.charAt(0).toUpperCase() + f.slice(1)}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Documents List */}
        {filteredDocuments.length === 0 ? (
          <div className="backdrop-blur-sm bg-slate-800/50 border border-slate-700/50 rounded-xl p-12 text-center">
            <Shield className="w-16 h-16 text-slate-600 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-white mb-2">
              {filter === 'all' ? 'No DRS Documents Yet' : `No ${filter} Documents`}
            </h3>
            <p className="text-slate-300 mb-6">
              {filter === 'all'
                ? "You don't have any DRS documents yet. DRS certificates will be issued after your investments are completed and shares are allocated."
                : `You don't have any ${filter} DRS documents at the moment.`
              }
            </p>
            {filter === 'all' && (
              <button
                onClick={() => router.push('/financial-hub/investments')}
                className="px-6 py-3 bg-gold-400 text-slate-900 font-semibold rounded-lg hover:bg-gold-500 transition-colors inline-flex items-center gap-2"
              >
                View Investments
                <ArrowRight className="w-4 h-4" />
              </button>
            )}
          </div>
        ) : (
          <div className="space-y-4">
            {filteredDocuments.map((doc) => (
              <button
                key={doc.id}
                onClick={() => router.push(`/financial-hub/drs/${doc.id}`)}
                className="w-full backdrop-blur-sm bg-slate-800/50 border border-slate-700/50 rounded-xl hover:bg-slate-800/80 hover:border-gold-400/30 hover:-translate-y-1 transition-all duration-300 p-6 text-left"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <Building2 className="w-5 h-5 text-gold-400" />
                      <h3 className="text-xl font-semibold text-white">
                        {doc.subscription_agreement.financing.company.name}
                      </h3>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`px-3 py-1 rounded-full text-xs font-medium ${getDocumentTypeColor(doc.document_type)}`}>
                        {getDocumentTypeLabel(doc.document_type)}
                      </span>
                      {doc.delivered_at ? (
                        <span className="px-3 py-1 rounded-full text-xs font-medium bg-green-500/20 text-green-300 border border-green-500/30 inline-flex items-center gap-1">
                          <CheckCircle className="w-3.5 h-3.5" />
                          Delivered
                        </span>
                      ) : (
                        <span className="px-3 py-1 rounded-full text-xs font-medium bg-yellow-500/20 text-yellow-300 border border-yellow-500/30 inline-flex items-center gap-1">
                          <Clock className="w-3.5 h-3.5" />
                          Pending Delivery
                        </span>
                      )}
                    </div>
                  </div>
                  <Download className="w-6 h-6 text-gold-400" />
                </div>

                <div className="grid md:grid-cols-4 gap-4">
                  <div>
                    <p className="text-sm text-slate-400 mb-1">Certificate Number</p>
                    <p className="text-lg font-mono font-semibold text-white">
                      {doc.certificate_number}
                    </p>
                  </div>

                  <div>
                    <p className="text-sm text-slate-400 mb-1">Shares</p>
                    <p className="text-lg font-semibold text-white">
                      {doc.num_shares.toLocaleString()}
                    </p>
                  </div>

                  <div>
                    <p className="text-sm text-slate-400 mb-1">Issued Date</p>
                    <p className="text-lg font-semibold text-white flex items-center gap-1">
                      <Calendar className="w-4 h-4" />
                      {new Date(doc.issue_date).toLocaleDateString()}
                    </p>
                  </div>

                  {doc.delivered_at && (
                    <div>
                      <p className="text-sm text-slate-400 mb-1">Delivered On</p>
                      <p className="text-lg font-semibold text-green-400 flex items-center gap-1">
                        <Mail className="w-4 h-4" />
                        {new Date(doc.delivered_at).toLocaleDateString()}
                      </p>
                    </div>
                  )}
                </div>

                <div className="mt-4 flex items-center justify-between">
                  <p className="text-sm text-slate-300">
                    Agreement #{doc.subscription_agreement.id} - ${parseFloat(doc.subscription_agreement.total_investment_amount).toLocaleString()} investment
                  </p>
                  <div className="flex items-center text-gold-400 font-medium">
                    <span>View Details</span>
                    <ArrowRight className="w-4 h-4 ml-2" />
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}

        {/* Help Section */}
        <div className="mt-12 grid md:grid-cols-2 gap-6">
          <div className="p-6 backdrop-blur-sm bg-slate-800/30 border border-gold-400/20 rounded-xl">
            <Info className="w-8 h-8 text-gold-400 mb-3" />
            <h3 className="text-lg font-semibold text-white mb-2">
              About Your DRS Documents
            </h3>
            <ul className="space-y-2 text-sm text-slate-300">
              <li className="flex items-start gap-2">
                <CheckCircle className="w-4 h-4 text-gold-400 mt-0.5 flex-shrink-0" />
                <span>DRS certificates are issued after shares are allocated</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle className="w-4 h-4 text-gold-400 mt-0.5 flex-shrink-0" />
                <span>Documents are delivered electronically to your account</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle className="w-4 h-4 text-gold-400 mt-0.5 flex-shrink-0" />
                <span>You can download and print certificates at any time</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle className="w-4 h-4 text-gold-400 mt-0.5 flex-shrink-0" />
                <span>Keep your certificates in a safe place as proof of ownership</span>
              </li>
            </ul>
          </div>

          <div className="p-6 backdrop-blur-sm bg-slate-800/30 border border-gold-400/20 rounded-xl">
            <Award className="w-8 h-8 text-gold-400 mb-3" />
            <h3 className="text-lg font-semibold text-white mb-2">
              Benefits of DRS
            </h3>
            <ul className="space-y-2 text-sm text-slate-300">
              <li className="flex items-start gap-2">
                <CheckCircle className="w-4 h-4 text-gold-400 mt-0.5 flex-shrink-0" />
                <span>Direct ownership with no intermediary risk</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle className="w-4 h-4 text-gold-400 mt-0.5 flex-shrink-0" />
                <span>Voting rights directly in your name</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle className="w-4 h-4 text-gold-400 mt-0.5 flex-shrink-0" />
                <span>Dividends paid directly to you</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle className="w-4 h-4 text-gold-400 mt-0.5 flex-shrink-0" />
                <span>Protection from broker failures</span>
              </li>
            </ul>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="mt-6 grid md:grid-cols-3 gap-6 mb-16">
          <button
            onClick={() => router.push('/financial-hub/agreements')}
            className="p-6 backdrop-blur-sm bg-slate-800/50 border border-slate-700/50 rounded-xl hover:bg-slate-800/80 hover:border-gold-400/30 hover:-translate-y-1 transition-all duration-300 text-left"
          >
            <FileText className="w-8 h-8 text-purple-400 mb-3" />
            <h3 className="text-lg font-semibold text-white mb-2">
              Subscription Agreements
            </h3>
            <p className="text-sm text-slate-300">
              View your signed agreements
            </p>
          </button>

          <button
            onClick={() => router.push('/financial-hub/investments')}
            className="p-6 backdrop-blur-sm bg-slate-800/50 border border-slate-700/50 rounded-xl hover:bg-slate-800/80 hover:border-gold-400/30 hover:-translate-y-1 transition-all duration-300 text-left"
          >
            <TrendingUp className="w-8 h-8 text-green-400 mb-3" />
            <h3 className="text-lg font-semibold text-white mb-2">
              Investment Tracking
            </h3>
            <p className="text-sm text-slate-300">
              Monitor your portfolio
            </p>
          </button>

          <button
            onClick={() => router.push('/companies')}
            className="p-6 backdrop-blur-sm bg-slate-800/50 border border-slate-700/50 rounded-xl hover:bg-slate-800/80 hover:border-gold-400/30 hover:-translate-y-1 transition-all duration-300 text-left"
          >
            <Building2 className="w-8 h-8 text-gold-400 mb-3" />
            <h3 className="text-lg font-semibold text-white mb-2">
              Browse Companies
            </h3>
            <p className="text-sm text-slate-300">
              Find new opportunities
            </p>
          </button>
        </div>
      </div>
    </div>
  );
}
