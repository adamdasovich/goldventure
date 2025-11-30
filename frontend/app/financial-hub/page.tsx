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

interface QualificationStatus {
  status: string;
  criteria_met: string | null;
  qualified_at: string | null;
}

export default function FinancialHub() {
  const router = useRouter();
  const [qualificationStatus, setQualificationStatus] = useState<QualificationStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchQualificationStatus();
  }, []);

  const fetchQualificationStatus = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/api/qualifications/status/', {
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
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      <div className="container mx-auto px-4 py-12">
        {/* Header */}
        <div className="mb-12">
          <h1 className="text-4xl font-bold text-slate-900 dark:text-white mb-4">
            Financial Hub
          </h1>
          <p className="text-lg text-slate-600 dark:text-slate-300 max-w-3xl">
            Your comprehensive platform for participating in mining company financing rounds.
            Complete your education, get qualified, and invest in opportunities.
          </p>
        </div>

        {/* Qualification Status Banner */}
        {!loading && (
          <div className={`mb-8 p-6 rounded-lg ${
            qualificationStatus?.status === 'qualified'
              ? 'bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800'
              : 'bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800'
          }`}>
            <div className="flex items-start gap-4">
              {qualificationStatus?.status === 'qualified' ? (
                <CheckCircle className="w-6 h-6 text-green-600 dark:text-green-400 mt-1" />
              ) : (
                <Clock className="w-6 h-6 text-yellow-600 dark:text-yellow-400 mt-1" />
              )}
              <div className="flex-1">
                <h3 className="font-semibold text-lg text-slate-900 dark:text-white mb-1">
                  {qualificationStatus?.status === 'qualified'
                    ? 'Accredited Investor Status: Qualified'
                    : 'Accredited Investor Status: Not Qualified'
                  }
                </h3>
                <p className="text-slate-600 dark:text-slate-300">
                  {qualificationStatus?.status === 'qualified'
                    ? `You are qualified as an accredited investor and can participate in financing rounds.`
                    : 'Complete the accreditation questionnaire to unlock investment opportunities.'
                  }
                </p>
                {!qualificationStatus && (
                  <button
                    onClick={() => router.push('/financial-hub/qualification')}
                    className="mt-3 inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
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
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {modules.map((module) => {
            const Icon = module.icon;
            const isLocked = module.status === 'locked';

            return (
              <button
                key={module.id}
                onClick={() => !isLocked && router.push(module.href)}
                disabled={isLocked}
                className={`
                  group relative p-6 bg-white dark:bg-slate-800 rounded-xl shadow-md
                  transition-all duration-300
                  ${isLocked
                    ? 'opacity-50 cursor-not-allowed'
                    : 'hover:shadow-xl hover:-translate-y-1 cursor-pointer'
                  }
                `}
              >
                {/* Status Badge */}
                {module.status === 'completed' && (
                  <div className="absolute top-4 right-4">
                    <CheckCircle className="w-6 h-6 text-green-500" />
                  </div>
                )}

                {/* Icon */}
                <div className={`${module.color} w-14 h-14 rounded-lg flex items-center justify-center mb-4 transition-transform group-hover:scale-110`}>
                  <Icon className="w-7 h-7 text-white" />
                </div>

                {/* Content */}
                <h3 className="text-xl font-semibold text-slate-900 dark:text-white mb-2">
                  {module.title}
                </h3>
                <p className="text-slate-600 dark:text-slate-300 mb-4 min-h-[48px]">
                  {module.description}
                </p>

                {/* Action */}
                <div className="flex items-center gap-2 text-blue-600 dark:text-blue-400 font-medium">
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
        <div className="mt-12 p-8 bg-blue-50 dark:bg-blue-900/20 rounded-xl border border-blue-200 dark:border-blue-800">
          <h3 className="text-xl font-semibold text-slate-900 dark:text-white mb-3">
            Need Help Getting Started?
          </h3>
          <p className="text-slate-600 dark:text-slate-300 mb-4">
            We recommend completing the modules in this order:
          </p>
          <ol className="list-decimal list-inside space-y-2 text-slate-700 dark:text-slate-300">
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
