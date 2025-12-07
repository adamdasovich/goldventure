'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  BookOpen,
  Award,
  FileText,
  TrendingUp,
  Shield,
  CheckCircle,
  Clock,
  ArrowRight
} from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import LogoMono from '@/components/LogoMono';
import { LoginModal, RegisterModal } from '@/components/auth';
import { useAuth } from '@/contexts/AuthContext';

interface QualificationStatus {
  status: string;
  criteria_met: string | null;
  qualified_at: string | null;
}

export default function FinancialHub() {
  const router = useRouter();
  const [qualificationStatus, setQualificationStatus] = useState<QualificationStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [showLogin, setShowLogin] = useState(false);
  const [showRegister, setShowRegister] = useState(false);
  const { user, logout } = useAuth();

  useEffect(() => {
    fetchQualificationStatus();
  }, []);

  const fetchQualificationStatus = async () => {
    try {
      const token = localStorage.getItem('accessToken');
      const response = await fetch('https://api.juniorgoldminingintelligence.com/api/qualifications/status/', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setQualificationStatus(data);
      }
    } catch (error) {
      console.error('Error fetching qualification status:', error);
    } finally {
      setLoading(false);
    }
  };

  const modules = [
    {
      id: 'education',
      title: 'Educational Hub',
      description: 'Learn about mining company financing, Canadian regulations, and investor rights',
      icon: BookOpen,
      color: 'bg-blue-500',
      href: '/financial-hub/education',
      status: 'available'
    },
    {
      id: 'qualification',
      title: 'Accredited Investor Qualification',
      description: 'Complete the accreditation questionnaire to participate in financing rounds',
      icon: Award,
      color: 'bg-purple-500',
      href: '/financial-hub/qualification',
      status: qualificationStatus?.status === 'qualified' ? 'completed' : 'available'
    },
    {
      id: 'agreements',
      title: 'Subscription Agreements',
      description: 'Review and sign subscription agreements for investment opportunities',
      icon: FileText,
      color: 'bg-green-500',
      href: '/financial-hub/agreements',
      status: qualificationStatus?.status === 'qualified' ? 'available' : 'locked',
      requiresQualification: true
    },
    {
      id: 'investments',
      title: 'Investment Tracking',
      description: 'Track your investments, payments, and share allocations',
      icon: TrendingUp,
      color: 'bg-orange-500',
      href: '/financial-hub/investments',
      status: 'available'
    },
    {
      id: 'drs',
      title: 'DRS Education & Documents',
      description: 'Learn about Direct Registration System and access your share certificates',
      icon: Shield,
      color: 'bg-indigo-500',
      href: '/financial-hub/drs',
      status: 'available'
    }
  ];

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

      {/* Hero Section with Background Effects */}
      <section className="relative py-20 px-4 sm:px-6 lg:px-8 overflow-hidden">
        {/* Background gradient effect */}
        <div className="absolute inset-0 bg-linear-to-b from-slate-900 via-slate-900 to-slate-800 opacity-50"></div>
        <div className="absolute inset-0" style={{
          backgroundImage: 'radial-gradient(circle at 50% 50%, rgba(212, 161, 42, 0.1) 0%, transparent 50%)'
        }}></div>

        <div className="relative max-w-7xl mx-auto">
          {/* Header */}
          <div className="text-center mb-12">
            <h1 className="text-5xl md:text-6xl font-bold mb-6 text-gradient-gold animate-fade-in leading-tight pb-2">
              Financial Hub
            </h1>
            <p className="text-xl text-slate-300 max-w-3xl mx-auto">
              Your comprehensive platform for participating in mining company financing rounds.
              Complete your education, get qualified, and invest in opportunities.
            </p>
          </div>
        </div>
      </section>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 -mt-8">{/* Overlap section */}

        {/* Qualification Status Banner */}
        {!loading && (
          <div className={`mb-8 p-6 rounded-xl backdrop-blur-sm border-2 ${
            qualificationStatus?.status === 'qualified'
              ? 'bg-green-500/10 border-green-500/30'
              : 'bg-yellow-500/10 border-yellow-500/30'
          }`}>
            <div className="flex items-start gap-4">
              {qualificationStatus?.status === 'qualified' ? (
                <CheckCircle className="w-6 h-6 text-green-400 mt-1" />
              ) : (
                <Clock className="w-6 h-6 text-yellow-400 mt-1" />
              )}
              <div className="flex-1">
                <h3 className="font-semibold text-lg text-white mb-1">
                  {qualificationStatus?.status === 'qualified'
                    ? 'Accredited Investor Status: Qualified'
                    : 'Accredited Investor Status: Not Qualified'
                  }
                </h3>
                <p className="text-slate-300">
                  {qualificationStatus?.status === 'qualified'
                    ? `You are qualified as an accredited investor and can participate in financing rounds.`
                    : 'Complete the accreditation questionnaire to unlock investment opportunities.'
                  }
                </p>
                {!qualificationStatus && (
                  <button
                    onClick={() => router.push('/financial-hub/qualification')}
                    className="mt-3 inline-flex items-center gap-2 px-4 py-2 bg-gold-400 text-slate-900 font-semibold rounded-lg hover:bg-gold-500 transition-colors"
                  >
                    Get Qualified
                    <ArrowRight className="w-4 h-4" />
                  </button>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Module Cards Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-16">
          {modules.map((module) => {
            const Icon = module.icon;
            const isLocked = module.status === 'locked';

            return (
              <button
                key={module.id}
                onClick={() => !isLocked && router.push(module.href)}
                disabled={isLocked}
                className={`
                  group relative p-6 backdrop-blur-sm bg-slate-800/50 border border-slate-700/50 rounded-xl
                  transition-all duration-300
                  ${isLocked
                    ? 'opacity-50 cursor-not-allowed'
                    : 'hover:bg-slate-800/80 hover:border-gold-400/30 hover:-translate-y-1 cursor-pointer'
                  }
                `}
              >
                {/* Status Badge */}
                {module.status === 'completed' && (
                  <div className="absolute top-4 right-4">
                    <CheckCircle className="w-6 h-6 text-green-400" />
                  </div>
                )}

                {/* Icon */}
                <div className="w-14 h-14 rounded-lg flex items-center justify-center mb-4 transition-transform group-hover:scale-110"
                     style={{ backgroundColor: 'rgba(212, 175, 55, 0.2)', border: '2px solid #d4af37' }}>
                  <Icon className="w-7 h-7" style={{ color: '#d4af37' }} />
                </div>

                {/* Content */}
                <h3 className="text-xl font-semibold text-white mb-2">
                  {module.title}
                </h3>
                <p className="text-slate-300 mb-4 min-h-[48px]">
                  {module.description}
                </p>

                {/* Action */}
                <div className="flex items-center gap-2 text-gold-400 font-medium">
                  {isLocked ? (
                    <>
                      <Shield className="w-4 h-4" />
                      <span className="text-sm">Requires Accreditation</span>
                    </>
                  ) : (
                    <>
                      <span>Explore</span>
                      <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
                    </>
                  )}
                </div>
              </button>
            );
          })}
        </div>

        {/* Help Section */}
        <div className="mt-12 p-8 backdrop-blur-sm bg-slate-800/30 border border-gold-400/20 rounded-xl">
          <h3 className="text-xl font-semibold text-white mb-3">
            Need Help Getting Started?
          </h3>
          <p className="text-slate-300 mb-4">
            We recommend completing the modules in this order:
          </p>
          <ol className="list-decimal list-inside space-y-2 text-slate-300">
            <li>Complete the Educational Hub to understand mining financing</li>
            <li>Fill out the Accredited Investor Qualification questionnaire</li>
            <li>Review available financing opportunities and subscription agreements</li>
            <li>Track your investments and receive DRS documentation</li>
          </ol>
        </div>
      </div>
    </div>
  );
}
