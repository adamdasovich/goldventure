'use client';

import { useState, useEffect, useMemo } from 'react';
import { useRouter, useParams } from 'next/navigation';
import {
  ArrowLeft,
  Clock,
  CheckCircle,
  BookOpen,
  Award
} from 'lucide-react';

// Basic HTML sanitization to prevent XSS attacks
// Removes script tags, event handlers, and dangerous attributes
function sanitizeHtml(html: string): string {
  if (!html) return '';

  // Remove script tags and their contents
  let sanitized = html.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '');

  // Remove event handlers (onclick, onerror, onload, etc.)
  sanitized = sanitized.replace(/\s*on\w+\s*=\s*["'][^"']*["']/gi, '');
  sanitized = sanitized.replace(/\s*on\w+\s*=\s*[^\s>]*/gi, '');

  // Remove javascript: and data: URLs in href/src attributes
  sanitized = sanitized.replace(/href\s*=\s*["']?\s*javascript:[^"'>]*/gi, 'href="#"');
  sanitized = sanitized.replace(/src\s*=\s*["']?\s*javascript:[^"'>]*/gi, 'src=""');
  sanitized = sanitized.replace(/href\s*=\s*["']?\s*data:[^"'>]*/gi, 'href="#"');

  // Remove iframe, object, embed tags
  sanitized = sanitized.replace(/<iframe\b[^>]*>.*?<\/iframe>/gi, '');
  sanitized = sanitized.replace(/<object\b[^>]*>.*?<\/object>/gi, '');
  sanitized = sanitized.replace(/<embed\b[^>]*>/gi, '');

  return sanitized;
}

interface EducationalModule {
  id: number;
  module_type: string;
  title: string;
  description: string;
  content: string;
  estimated_read_time_minutes: number;
  is_required: boolean;
  completion_status: {
    completed: boolean;
    completed_at: string | null;
    time_spent_seconds: number;
    passed: boolean;
  } | null;
}

export default function ModuleContent() {
  const router = useRouter();
  const params = useParams();
  const [module, setModule] = useState<EducationalModule | null>(null);
  const [loading, setLoading] = useState(true);
  const [startTime, setStartTime] = useState<number>(Date.now());
  const [completing, setCompleting] = useState(false);

  useEffect(() => {
    if (params.id) {
      fetchModule(params.id as string);
      setStartTime(Date.now());
    }
  }, [params.id]);

  const fetchModule = async (id: string) => {
    try {
      const token = localStorage.getItem('accessToken');
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/api'}/education/modules/${id}/`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setModule(data);
      }
    } catch (error) {
      console.error('Error fetching module:', error);
    } finally {
      setLoading(false);
    }
  };

  const markAsComplete = async () => {
    if (!module) return;

    setCompleting(true);
    const timeSpentSeconds = Math.floor((Date.now() - startTime) / 1000);

    try {
      const token = localStorage.getItem('accessToken');
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/api'}/education/modules/${module.id}/complete/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          time_spent_seconds: timeSpentSeconds,
          passed: true,
        }),
      });

      if (response.ok) {
        // Refresh module data
        await fetchModule(params.id as string);
        alert('Module completed successfully!');
      }
    } catch (error) {
      console.error('Error completing module:', error);
      alert('Failed to mark module as complete');
    } finally {
      setCompleting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-slate-600 dark:text-slate-300">Loading module...</p>
        </div>
      </div>
    );
  }

  if (!module) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-900 flex items-center justify-center">
        <div className="text-center">
          <BookOpen className="w-16 h-16 text-slate-300 dark:text-slate-600 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-slate-900 dark:text-white mb-2">
            Module Not Found
          </h3>
          <p className="text-slate-600 dark:text-slate-300 mb-4">
            This educational module could not be found.
          </p>
          <button
            onClick={() => router.push('/financial-hub/education')}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Back to Education Hub
          </button>
        </div>
      </div>
    );
  }

  const isCompleted = module.completion_status?.completed;

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      <div className="container mx-auto px-4 py-12 max-w-4xl">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => router.push('/financial-hub/education')}
            className="flex items-center gap-2 text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white mb-4 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Education Hub
          </button>

          {/* Module Info Card */}
          <div className="bg-white dark:bg-slate-800 rounded-xl shadow-md p-6 mb-6">
            <div className="flex items-start justify-between mb-4">
              <div className="flex-1">
                <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">
                  {module.title}
                </h1>
                <p className="text-slate-600 dark:text-slate-300">
                  {module.description}
                </p>
              </div>
              {isCompleted && (
                <div className="ml-4">
                  <CheckCircle className="w-8 h-8 text-green-500" />
                </div>
              )}
            </div>

            {/* Meta Info */}
            <div className="flex items-center gap-6 text-sm text-slate-500 dark:text-slate-400">
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4" />
                <span>{module.estimated_read_time_minutes} min read</span>
              </div>
              {module.is_required && (
                <span className="px-2 py-1 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 rounded text-xs font-medium">
                  Required for Accreditation
                </span>
              )}
              {isCompleted && (
                <div className="flex items-center gap-2 text-green-600 dark:text-green-400">
                  <CheckCircle className="w-4 h-4" />
                  <span>Completed</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="bg-white dark:bg-slate-800 rounded-xl shadow-md p-8 mb-6">
          <div
            className="prose prose-slate dark:prose-invert max-w-none
              prose-headings:text-slate-900 dark:prose-headings:text-white
              prose-p:text-slate-700 dark:prose-p:text-slate-300
              prose-strong:text-slate-900 dark:prose-strong:text-white
              prose-ul:text-slate-700 dark:prose-ul:text-slate-300
              prose-ol:text-slate-700 dark:prose-ol:text-slate-300
              prose-a:text-blue-600 dark:prose-a:text-blue-400"
            dangerouslySetInnerHTML={{ __html: sanitizeHtml(module.content) }}
          />
        </div>

        {/* Complete Button */}
        {!isCompleted && (
          <div className="bg-white dark:bg-slate-800 rounded-xl shadow-md p-6">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-3">
              Mark Module as Complete
            </h3>
            <p className="text-slate-600 dark:text-slate-300 mb-4">
              Once you have finished reading this module, mark it as complete to track your progress.
            </p>
            <button
              onClick={markAsComplete}
              disabled={completing}
              className="w-full px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-semibold rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {completing ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                  Completing...
                </>
              ) : (
                <>
                  <Award className="w-5 h-5" />
                  Mark as Complete
                </>
              )}
            </button>
          </div>
        )}

        {/* Completion Info */}
        {isCompleted && module.completion_status && (
          <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-xl p-6">
            <div className="flex items-start gap-3">
              <CheckCircle className="w-6 h-6 text-green-600 dark:text-green-400 mt-0.5" />
              <div>
                <h3 className="font-semibold text-green-900 dark:text-green-100 mb-1">
                  Module Completed!
                </h3>
                <p className="text-green-700 dark:text-green-300 text-sm">
                  You completed this module on {new Date(module.completion_status.completed_at!).toLocaleDateString()}.
                  Time spent: {Math.floor(module.completion_status.time_spent_seconds / 60)} minutes.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
