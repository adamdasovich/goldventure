'use client';

import { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

interface CompanyResourceUploadModalProps {
  companyId: number;
  accessToken: string | null;
  onClose: () => void;
  onUploadComplete: () => void;
}

const RESOURCE_CATEGORIES = [
  { value: 'investor_presentation', label: 'Investor Presentation', icon: '📊' },
  { value: 'technical_report', label: 'Technical Report (NI 43-101)', icon: '📋' },
  { value: 'financial_report', label: 'Financial Report', icon: '💰' },
  { value: 'annual_report', label: 'Annual Report', icon: '📈' },
  { value: 'factsheet', label: 'Fact Sheet', icon: '📄' },
  { value: 'hero', label: 'Hero Image', icon: '🖼️' },
  { value: 'gallery', label: 'Photo / Gallery Image', icon: '📷' },
  { value: 'logo', label: 'Company Logo', icon: '🏷️' },
  { value: 'map_geological', label: 'Geological Map', icon: '🗺️' },
  { value: 'map_location', label: 'Location Map', icon: '📍' },
  { value: 'map_claims', label: 'Claims Map', icon: '🧭' },
  { value: 'drilling_results', label: 'Drilling Results', icon: '🔬' },
  { value: 'assay_certificate', label: 'Assay Certificate', icon: '🧪' },
  { value: 'news_release', label: 'News Release', icon: '📰' },
  { value: 'permit', label: 'Permit/License', icon: '📜' },
  { value: 'corporate', label: 'Corporate Document', icon: '🏢' },
  { value: 'other', label: 'Other Document', icon: '📁' },
];

const ALLOWED_FILE_TYPES = {
  document: ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/vnd.ms-powerpoint', 'application/vnd.openxmlformats-officedocument.presentationml.presentation'],
  image: ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],
  map: ['image/jpeg', 'image/png', 'application/pdf'],
};

export function CompanyResourceUploadModal({ companyId, accessToken, onClose, onUploadComplete }: CompanyResourceUploadModalProps) {
  const [category, setCategory] = useState('');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [isPublic, setIsPublic] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);

  const getResourceType = (cat: string): string => {
    if (cat.startsWith('map_')) return 'map';
    if (['hero', 'gallery', 'logo'].includes(cat)) return 'image';
    if (cat.includes('video')) return 'video';
    if (cat === 'investor_presentation') return 'presentation';
    if (cat === 'spreadsheet') return 'spreadsheet';
    return 'document';
  };

  const handleFileSelect = (selectedFile: File) => {
    if (!category) {
      setError('Please select a resource type first');
      return;
    }

    const resourceType = getResourceType(category);
    let allowedTypes: string[] = [];

    if (resourceType === 'map') {
      allowedTypes = ALLOWED_FILE_TYPES.map;
    } else if (resourceType === 'image') {
      allowedTypes = ALLOWED_FILE_TYPES.image;
    } else {
      allowedTypes = [...ALLOWED_FILE_TYPES.document, ...ALLOWED_FILE_TYPES.image];
    }

    if (!allowedTypes.includes(selectedFile.type)) {
      setError(`Invalid file type. Allowed: PDF, Word, Excel, PowerPoint, JPG, PNG`);
      return;
    }

    if (selectedFile.size > 50 * 1024 * 1024) {
      setError('File size must be less than 50MB');
      return;
    }

    setFile(selectedFile);
    setError(null);

    if (!title) {
      const fileName = selectedFile.name.replace(/\.[^/.]+$/, '');
      setTitle(fileName);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file || !category || !title.trim()) {
      setError('Please fill in all required fields');
      return;
    }

    setUploading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('company', companyId.toString());
      formData.append('category', category);
      formData.append('title', title.trim());
      formData.append('description', description.trim());
      formData.append('resource_type', getResourceType(category));
      formData.append('is_public', isPublic.toString());

      const response = await fetch(`${API_URL}/company-portal/resources/upload/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
        },
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to upload file');
      }

      onUploadComplete();
      onClose();
    } catch (err) {
      console.error('Upload failed:', err);
      setError(err instanceof Error ? err.message : 'Failed to upload file');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-screen items-center justify-center p-4">
        <div className="fixed inset-0 bg-black/70" onClick={onClose} />

        <Card className="relative z-10 w-full max-w-2xl p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-white">Add Company Resource</h2>
            <button onClick={onClose} className="text-slate-400 hover:text-white">
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-900/30 border border-red-700 rounded-lg text-red-400 text-sm">
              {error}
            </div>
          )}

          {/* Resource Type Selection */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Resource Type <span className="text-red-400">*</span>
            </label>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-2 max-h-64 overflow-y-auto">
              {RESOURCE_CATEGORIES.map((cat) => (
                <button
                  key={cat.value}
                  type="button"
                  onClick={() => {
                    setCategory(cat.value);
                    setFile(null);
                  }}
                  className={`p-3 rounded-lg border text-left transition-all text-sm ${
                    category === cat.value
                      ? 'border-gold-500 bg-gold-500/10 text-white'
                      : 'border-slate-700 hover:border-slate-600 text-slate-300'
                  }`}
                >
                  <span className="mr-2">{cat.icon}</span>
                  {cat.label}
                </button>
              ))}
            </div>
          </div>

          {/* File Upload Area */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-slate-300 mb-2">
              File <span className="text-red-400">*</span>
            </label>
            <div
              onDragEnter={(e) => { e.preventDefault(); setDragActive(true); }}
              onDragLeave={(e) => { e.preventDefault(); setDragActive(false); }}
              onDragOver={(e) => e.preventDefault()}
              onDrop={handleDrop}
              className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
                dragActive ? 'border-gold-500 bg-gold-500/10' : 'border-slate-700 hover:border-slate-600'
              }`}
            >
              {file ? (
                <div className="flex items-center justify-center gap-3">
                  <svg className="w-8 h-8 text-gold-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <div className="text-left">
                    <p className="text-white font-medium">{file.name}</p>
                    <p className="text-sm text-slate-400">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                  </div>
                  <button
                    type="button"
                    onClick={() => setFile(null)}
                    className="ml-2 text-slate-400 hover:text-red-400"
                  >
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              ) : (
                <>
                  <svg className="mx-auto w-12 h-12 text-slate-500 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                  <p className="text-slate-300 mb-1">Drag and drop your file here, or</p>
                  <label className="cursor-pointer">
                    <span className="text-gold-500 hover:text-gold-400">browse to upload</span>
                    <input
                      type="file"
                      className="hidden"
                      onChange={(e) => e.target.files?.[0] && handleFileSelect(e.target.files[0])}
                      disabled={!category}
                    />
                  </label>
                  <p className="text-xs text-slate-500 mt-2">
                    {!category ? 'Select a resource type first' : 'Max file size: 50MB'}
                  </p>
                </>
              )}
            </div>
          </div>

          {/* Title */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Title <span className="text-red-400">*</span>
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g., Q3 2024 Investor Presentation"
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white placeholder-slate-500 focus:ring-2 focus:ring-gold-500 focus:border-transparent"
            />
          </div>

          {/* Description */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Description <span className="text-slate-500">(optional)</span>
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={2}
              placeholder="Brief description of this resource..."
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white placeholder-slate-500 focus:ring-2 focus:ring-gold-500 focus:border-transparent resize-none"
            />
          </div>

          {/* Visibility Toggle */}
          <div className="mb-6">
            <label className="flex items-center gap-3 cursor-pointer">
              <div className="relative">
                <input
                  type="checkbox"
                  checked={isPublic}
                  onChange={(e) => setIsPublic(e.target.checked)}
                  className="sr-only"
                />
                <div className={`w-10 h-6 rounded-full transition-colors ${isPublic ? 'bg-gold-500' : 'bg-slate-700'}`}>
                  <div className={`w-4 h-4 bg-white rounded-full absolute top-1 transition-transform ${isPublic ? 'translate-x-5' : 'translate-x-1'}`} />
                </div>
              </div>
              <div>
                <span className="text-sm font-medium text-white">
                  {isPublic ? 'Public' : 'Private'}
                </span>
                <p className="text-xs text-slate-400">
                  {isPublic ? 'Visible to all investors' : 'Only visible to company representatives'}
                </p>
              </div>
            </label>
          </div>

          {/* Actions */}
          <div className="flex gap-3">
            <Button
              variant="ghost"
              className="flex-1"
              onClick={onClose}
              disabled={uploading}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              className="flex-1"
              onClick={handleUpload}
              disabled={uploading || !file || !category || !title.trim()}
            >
              {uploading ? 'Uploading...' : 'Upload Resource'}
            </Button>
          </div>
        </Card>
      </div>
    </div>
  );
}
