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

  useEffect(() => {
    fetchModules();
  }, []);

  const fetchModules = async () => {
    try {
      const token = localStorage.getItem('token');
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
      <div className="min-h-screen bg-slate-50 dark:bg-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-slate-600 dark:text-slate-300">Loading modules...</p>
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
            Educational Hub
          </h1>
          <p className="text-lg text-slate-600 dark:text-slate-300 max-w-3xl">
            Learn about mining company financing, Canadian securities regulations, and your rights as an investor.
          </p>
        </div>

        {/* Progress Section */}
        <div className="mb-8 p-6 bg-white dark:bg-slate-800 rounded-xl shadow-md">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
              Your Progress
            </h3>
            <span className="text-sm font-medium text-slate-600 dark:text-slate-300">
              {completedCount} of {totalCount} modules completed
            </span>
          </div>

          {/* Progress Bar */}
          <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-3 overflow-hidden">
            <div
              className="bg-gradient-to-r from-blue-500 to-purple-500 h-full transition-all duration-500"
              style={{ width: `${progressPercentage}%` }}
            />
          </div>

          <p className="mt-3 text-sm text-slate-600 dark:text-slate-300">
            {completedCount === totalCount
              ? 'Congratulations! You have completed all educational modules.'
              : 'Complete all modules to fully prepare for investor accreditation.'
            }
          </p>
        </div>

        {/* Modules Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {modules.map((module) => {
            const Icon = getModuleIcon(module.module_type);
            const isCompleted = module.completion_status?.completed;

            return (
              <button
                key={module.id}
                onClick={() => router.push(`/financial-hub/education/${module.id}`)}
                className="group p-6 bg-white dark:bg-slate-800 rounded-xl shadow-md hover:shadow-xl transition-all duration-300 hover:-translate-y-1 text-left"
              >
                {/* Header */}
                <div className="flex items-start justify-between mb-4">
                  <div className="bg-blue-100 dark:bg-blue-900/30 p-3 rounded-lg">
                    <Icon className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                  </div>
                  {isCompleted && (
                    <CheckCircle className="w-6 h-6 text-green-500" />
                  )}
                </div>

                {/* Content */}
                <h3 className="text-xl font-semibold text-slate-900 dark:text-white mb-2">
                  {module.title}
                </h3>
                <p className="text-slate-600 dark:text-slate-300 mb-4 line-clamp-2">
                  {module.description}
                </p>

                {/* Meta Info */}
                <div className="flex items-center gap-4 text-sm text-slate-500 dark:text-slate-400">
                  <div className="flex items-center gap-1">
                    <Clock className="w-4 h-4" />
                    <span>{module.estimated_read_time_minutes} min read</span>
                  </div>
                  {module.is_required && (
                    <span className="px-2 py-1 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 rounded text-xs font-medium">
                      Required
                    </span>
                  )}
                </div>

                {/* Action */}
                <div className="mt-4 flex items-center gap-2 text-blue-600 dark:text-blue-400 font-medium">
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
            <BookOpen className="w-16 h-16 text-slate-300 dark:text-slate-600 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-slate-900 dark:text-white mb-2">
              No Modules Available
            </h3>
            <p className="text-slate-600 dark:text-slate-300">
              Educational modules will appear here once they are published.
            </p>
          </div>
        )}

        {/* Help Section */}
        <div className="mt-12 p-6 bg-blue-50 dark:bg-blue-900/20 rounded-xl border border-blue-200 dark:border-blue-800">
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">
            Why Complete These Modules?
          </h3>
          <ul className="space-y-2 text-slate-600 dark:text-slate-300">
            <li className="flex items-start gap-2">
              <CheckCircle className="w-5 h-5 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
              <span>Understand the fundamentals of mining company financing</span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle className="w-5 h-5 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
              <span>Learn about Canadian securities regulations and compliance</span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle className="w-5 h-5 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
              <span>Know your rights and obligations as an investor</span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle className="w-5 h-5 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
              <span>Be prepared for the accredited investor qualification process</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}
