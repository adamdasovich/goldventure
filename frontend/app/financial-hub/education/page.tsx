'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  BookOpen,
  CheckCircle,
  Clock,
  ArrowLeft,
  PlayCircle,
  FileText,
  Award
} from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import LogoMono from '@/components/LogoMono';
import { LoginModal, RegisterModal } from '@/components/auth';
import { useAuth } from '@/contexts/AuthContext';

interface EducationalModule {
  id: number;
  module_type: string;
  title: string;
  description: string;
  estimated_read_time_minutes: number;
  is_required: boolean;
  completion_status: {
    completed: boolean;
    completed_at: string | null;
    time_spent_seconds: number;
    passed: boolean;
  } | null;
}

export default function EducationHub() {
  const router = useRouter();
  const [modules, setModules] = useState<EducationalModule[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedModule, setSelectedModule] = useState<EducationalModule | null>(null);
  const [showLogin, setShowLogin] = useState(false);
  const [showRegister, setShowRegister] = useState(false);
  const { user, logout } = useAuth();

  useEffect(() => {
    fetchModules();
  }, []);

  const fetchModules = async () => {
    try {
      const token = localStorage.getItem('accessToken');
      const response = await fetch('http://localhost:8000/api/education/modules/', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setModules(data);
      }
    } catch (error) {
      console.error('Error fetching modules:', error);
    } finally {
      setLoading(false);
    }
  };

  const getModuleIcon = (moduleType: string) => {
    switch (moduleType) {
      case 'basics':
        return BookOpen;
      case 'regulations':
        return FileText;
      case 'investor_rights':
        return Award;
      case 'risk_disclosure':
        return FileText;
      case 'subscription_agreement':
        return FileText;
      case 'drs':
        return Award;
      default:
        return BookOpen;
    }
  };

  const completedCount = modules.filter(m => m.completion_status?.completed).length;
  const totalCount = modules.length;
  const progressPercentage = totalCount > 0 ? (completedCount / totalCount) * 100 : 0;

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gold-400 mx-auto mb-4"></div>
          <p className="text-slate-300">Loading modules...</p>
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
              Educational Hub
            </h1>
            <p className="text-xl text-slate-300 max-w-3xl mx-auto">
              Learn about mining company financing, Canadian securities regulations, and your rights as an investor.
            </p>
          </div>
        </div>
      </section>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 -mt-8">{/* Overlap section */}

        {/* Progress Section */}
        <div className="mb-8 p-6 backdrop-blur-sm bg-slate-800/50 border border-slate-700/50 rounded-xl">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">
              Your Progress
            </h3>
            <span className="text-sm font-medium text-slate-300">
              {completedCount} of {totalCount} modules completed
            </span>
          </div>

          {/* Progress Bar */}
          <div className="w-full bg-slate-700/50 rounded-full h-3 overflow-hidden">
            <div
              className="h-full transition-all duration-500"
              style={{
                width: `${progressPercentage}%`,
                background: 'linear-gradient(90deg, #d4af37 0%, #f4c430 100%)'
              }}
            />
          </div>

          <p className="mt-3 text-sm text-slate-300">
            {completedCount === totalCount
              ? 'Congratulations! You have completed all educational modules.'
              : 'Complete all modules to fully prepare for investor accreditation.'
            }
          </p>
        </div>

        {/* Modules Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-16">
          {modules.map((module) => {
            const Icon = getModuleIcon(module.module_type);
            const isCompleted = module.completion_status?.completed;

            return (
              <button
                key={module.id}
                onClick={() => router.push(`/financial-hub/education/${module.id}`)}
                className="group p-6 backdrop-blur-sm bg-slate-800/50 border border-slate-700/50 rounded-xl hover:bg-slate-800/80 hover:border-gold-400/30 hover:-translate-y-1 transition-all duration-300 text-left"
              >
                {/* Header */}
                <div className="flex items-start justify-between mb-4">
                  <div className="p-3 rounded-lg" style={{ backgroundColor: 'rgba(212, 175, 55, 0.2)', border: '2px solid #d4af37' }}>
                    <Icon className="w-6 h-6" style={{ color: '#d4af37' }} />
                  </div>
                  {isCompleted && (
                    <CheckCircle className="w-6 h-6 text-green-400" />
                  )}
                </div>

                {/* Content */}
                <h3 className="text-xl font-semibold text-white mb-2">
                  {module.title}
                </h3>
                <p className="text-slate-300 mb-4 line-clamp-2">
                  {module.description}
                </p>

                {/* Meta Info */}
                <div className="flex items-center gap-4 text-sm text-slate-400">
                  <div className="flex items-center gap-1">
                    <Clock className="w-4 h-4" />
                    <span>{module.estimated_read_time_minutes} min read</span>
                  </div>
                  {module.is_required && (
                    <span className="px-2 py-1 bg-purple-500/20 text-purple-300 border border-purple-500/30 rounded text-xs font-medium">
                      Required
                    </span>
                  )}
                </div>

                {/* Action */}
                <div className="mt-4 flex items-center gap-2 text-gold-400 font-medium">
                  {isCompleted ? (
                    <>
                      <span>Review</span>
                      <PlayCircle className="w-4 h-4" />
                    </>
                  ) : (
                    <>
                      <span>Start Learning</span>
                      <PlayCircle className="w-4 h-4 transition-transform group-hover:translate-x-1" />
                    </>
                  )}
                </div>
              </button>
            );
          })}
        </div>

        {/* Empty State */}
        {modules.length === 0 && (
          <div className="text-center py-12">
            <BookOpen className="w-16 h-16 text-slate-600 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-white mb-2">
              No Modules Available
            </h3>
            <p className="text-slate-300">
              Educational modules will appear here once they are published.
            </p>
          </div>
        )}

        {/* Help Section */}
        <div className="mt-12 p-6 backdrop-blur-sm bg-slate-800/30 border border-gold-400/20 rounded-xl">
          <h3 className="text-lg font-semibold text-white mb-2">
            Why Complete These Modules?
          </h3>
          <ul className="space-y-2 text-slate-300">
            <li className="flex items-start gap-2">
              <CheckCircle className="w-5 h-5 text-gold-400 mt-0.5 flex-shrink-0" />
              <span>Understand the fundamentals of mining company financing</span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle className="w-5 h-5 text-gold-400 mt-0.5 flex-shrink-0" />
              <span>Learn about Canadian securities regulations and compliance</span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle className="w-5 h-5 text-gold-400 mt-0.5 flex-shrink-0" />
              <span>Know your rights and obligations as an investor</span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle className="w-5 h-5 text-gold-400 mt-0.5 flex-shrink-0" />
              <span>Be prepared for the accredited investor qualification process</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}
