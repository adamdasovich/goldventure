'use client';

import { useState } from 'react';
import { Card, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';

interface GlossarySubmissionFormProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmitSuccess: () => void;
}

export default function GlossarySubmissionForm({ isOpen, onClose, onSubmitSuccess }: GlossarySubmissionFormProps) {
  const [formData, setFormData] = useState({
    term: '',
    definition: '',
    category: 'general' as 'reporting' | 'geology' | 'finance' | 'regulatory' | 'operations' | 'general',
    keywords: '',
    relatedLinks: ''
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const categories = [
    { value: 'reporting', label: 'Reporting & Standards' },
    { value: 'geology', label: 'Geology & Resources' },
    { value: 'finance', label: 'Finance & Investment' },
    { value: 'regulatory', label: 'Regulatory & Legal' },
    { value: 'operations', label: 'Mining Operations' },
    { value: 'general', label: 'General Terms' }
  ];

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.term.trim()) {
      newErrors.term = 'Term is required';
    } else if (formData.term.length < 2) {
      newErrors.term = 'Term must be at least 2 characters';
    } else if (formData.term.length > 200) {
      newErrors.term = 'Term must be less than 200 characters';
    }

    if (!formData.definition.trim()) {
      newErrors.definition = 'Definition is required';
    } else if (formData.definition.length < 20) {
      newErrors.definition = 'Definition must be at least 20 characters';
    } else if (formData.definition.length > 2000) {
      newErrors.definition = 'Definition must be less than 2000 characters';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitError(null);

    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);

    try {
      // Parse related links if provided
      let relatedLinksArray = [];
      if (formData.relatedLinks.trim()) {
        try {
          relatedLinksArray = JSON.parse(formData.relatedLinks);
        } catch {
          // If not valid JSON, ignore related links
          relatedLinksArray = [];
        }
      }

      const token = localStorage.getItem('accessToken');
      if (!token) {
        setSubmitError('You must be logged in to submit terms');
        setIsSubmitting(false);
        return;
      }

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/glossary/submissions/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          term: formData.term.trim(),
          definition: formData.definition.trim(),
          category: formData.category,
          keywords: formData.keywords.trim(),
          related_links: relatedLinksArray
        })
      });

      if (response.ok) {
        // Success - reset form and close modal
        setFormData({
          term: '',
          definition: '',
          category: 'general',
          keywords: '',
          relatedLinks: ''
        });
        setErrors({});
        onSubmitSuccess();
        onClose();
      } else {
        const errorData = await response.json();
        if (errorData.term) {
          setSubmitError(Array.isArray(errorData.term) ? errorData.term[0] : errorData.term);
        } else {
          setSubmitError('Failed to submit term. Please try again.');
        }
      }
    } catch (error) {
      console.error('Error submitting term:', error);
      setSubmitError('An error occurred while submitting. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <Card variant="glass-card" className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <CardHeader>
          <div className="flex items-start justify-between mb-4">
            <div>
              <CardTitle className="text-2xl">Submit New Glossary Term</CardTitle>
              <CardDescription className="mt-2">
                Suggest a new mining term for our glossary. Submissions will be reviewed by our team before being published.
              </CardDescription>
            </div>
            <button
              onClick={onClose}
              className="text-slate-400 hover:text-slate-300 text-2xl font-bold"
            >
              ×
            </button>
          </div>

          {submitError && (
            <div className="mb-4 p-3 bg-red-500/20 border border-red-500/50 rounded-lg text-red-300 text-sm">
              {submitError}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Term */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Term <span className="text-red-400">*</span>
              </label>
              <input
                type="text"
                value={formData.term}
                onChange={(e) => setFormData({ ...formData, term: e.target.value })}
                className={`w-full px-4 py-2.5 glass-light rounded-lg border ${
                  errors.term ? 'border-red-500' : 'border-slate-600'
                } text-slate-100 placeholder-slate-500 focus:outline-none focus:border-gold-500`}
                placeholder="e.g., Mineral Reserve"
                maxLength={200}
              />
              {errors.term && (
                <p className="mt-1 text-sm text-red-400">{errors.term}</p>
              )}
              <p className="mt-1 text-xs text-slate-500">
                {formData.term.length}/200 characters
              </p>
            </div>

            {/* Definition */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Definition <span className="text-red-400">*</span>
              </label>
              <textarea
                value={formData.definition}
                onChange={(e) => setFormData({ ...formData, definition: e.target.value })}
                rows={6}
                className={`w-full px-4 py-2.5 glass-light rounded-lg border ${
                  errors.definition ? 'border-red-500' : 'border-slate-600'
                } text-slate-100 placeholder-slate-500 focus:outline-none focus:border-gold-500 resize-none`}
                placeholder="Provide a clear, comprehensive definition of the term..."
                maxLength={2000}
              />
              {errors.definition && (
                <p className="mt-1 text-sm text-red-400">{errors.definition}</p>
              )}
              <p className="mt-1 text-xs text-slate-500">
                {formData.definition.length}/2000 characters (minimum 20 required)
              </p>
            </div>

            {/* Category */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Category <span className="text-red-400">*</span>
              </label>
              <select
                value={formData.category}
                onChange={(e) => setFormData({ ...formData, category: e.target.value as any })}
                className="w-full px-4 py-2.5 glass-light rounded-lg border border-slate-600 text-slate-100 focus:outline-none focus:border-gold-500"
              >
                {categories.map(cat => (
                  <option key={cat.value} value={cat.value} className="bg-slate-800">
                    {cat.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Keywords (Optional) */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Keywords (Optional)
              </label>
              <input
                type="text"
                value={formData.keywords}
                onChange={(e) => setFormData({ ...formData, keywords: e.target.value })}
                className="w-full px-4 py-2.5 glass-light rounded-lg border border-slate-600 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-gold-500"
                placeholder="e.g., reserves, measured, proven"
                maxLength={500}
              />
              <p className="mt-1 text-xs text-slate-500">
                Comma-separated keywords for better searchability
              </p>
            </div>

            {/* Related Links (Optional - Advanced) */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Related Links (Optional - JSON format)
              </label>
              <textarea
                value={formData.relatedLinks}
                onChange={(e) => setFormData({ ...formData, relatedLinks: e.target.value })}
                rows={3}
                className="w-full px-4 py-2.5 glass-light rounded-lg border border-slate-600 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-gold-500 resize-none font-mono text-sm"
                placeholder='[{"text": "Link text", "url": "/path"}]'
              />
              <p className="mt-1 text-xs text-slate-500">
                Optional: Add related links in JSON array format
              </p>
            </div>

            {/* Submit Buttons */}
            <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-700">
              <Button
                type="button"
                variant="ghost"
                onClick={onClose}
                disabled={isSubmitting}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="primary"
                disabled={isSubmitting}
              >
                {isSubmitting ? 'Submitting...' : 'Submit for Review'}
              </Button>
            </div>

            <p className="text-xs text-slate-500 text-center">
              Your submission will be reviewed by our team before being added to the glossary.
            </p>
          </form>
        </CardHeader>
      </Card>
    </div>
  );
}
