'use client';

import { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface ResourceUploadModalProps {
  listingId: number;
  accessToken: string | null;
  onClose: () => void;
  onUploadComplete: () => void;
}

const RESOURCE_CATEGORIES = [
  { value: 'geological_map', label: 'Geological Map', icon: '🗺️' },
  { value: 'claim_map', label: 'Claim Map', icon: '📍' },
  { value: 'location_map', label: 'Location Map', icon: '🧭' },
  { value: 'assay', label: 'Assay Certificate', icon: '🔬' },
  { value: 'report', label: 'Technical Report', icon: '📊' },
  { value: 'permit', label: 'Permit/License', icon: '📜' },
  { value: 'gallery', label: 'Photo', icon: '📷' },
  { value: 'other', label: 'Other Document', icon: '📄' },
];

const ALLOWED_FILE_TYPES = {
  image: ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],
  document: ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/vnd.ms-powerpoint', 'application/vnd.openxmlformats-officedocument.presentationml.presentation'],
  map: ['image/jpeg', 'image/png', 'application/pdf'],
};

export function ResourceUploadModal({ listingId, accessToken, onClose, onUploadComplete }: ResourceUploadModalProps) {
  const [category, setCategory] = useState('');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);

  const getMediaType = (cat: string): string => {
    if (['geological_map', 'claim_map', 'location_map'].includes(cat)) return 'map';
    if (cat === 'gallery') return 'image';
    return 'document';
  };

  const handleFileSelect = (selectedFile: File) => {
    if (!category) {
      setError('Please select a resource type first');
      return;
    }

    const mediaType = getMediaType(category);
    const allowedTypes = ALLOWED_FILE_TYPES[mediaType as keyof typeof ALLOWED_FILE_TYPES] || [];

    if (!allowedTypes.includes(selectedFile.type)) {
      setError(`Invalid file type. Allowed: ${mediaType === 'image' ? 'JPG, PNG, GIF, WebP' : mediaType === 'map' ? 'JPG, PNG, PDF' : 'PDF, Word, Excel, PowerPoint'}`);
      return;
    }

    if (selectedFile.size > 50 * 1024 * 1024) { // 50MB limit
      setError('File size must be less than 50MB');
      return;
    }

    setFile(selectedFile);
    setError(null);

    // Auto-fill title from filename if empty
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
      // First, upload file to get URL (for now, we'll use a direct URL approach)
      // In production, you'd upload to S3/CloudStorage and get a URL back

      // Create FormData for file upload
      const formData = new FormData();
      formData.append('file', file);
      formData.append('listing', listingId.toString());
      formData.append('category', category);
      formData.append('title', title.trim());
      formData.append('description', description.trim());
      formData.append('media_type', getMediaType(category));

      // Upload to backend
      const response = await fetch(`${API_URL}/properties/media/upload/`, {
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
        {/* Backdrop */}
        <div className="fixed inset-0 bg-black/70" onClick={onClose} />

        {/* Modal */}
        <Card className="relative z-10 w-full max-w-lg p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-white">Add Resource</h2>
            <button
              onClick={onClose}
              className="text-slate-400 hover:text-white"
            >
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
            <div className="grid grid-cols-2 gap-2">
              {RESOURCE_CATEGORIES.map((cat) => (
                <button
                  key={cat.value}
                  type="button"
                  onClick={() => {
                    setCategory(cat.value);
                    setFile(null); // Reset file when category changes
                  }}
                  className={`p-3 rounded-lg border text-left transition-all ${
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
              placeholder="e.g., Regional Geology Map"
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white placeholder-slate-500 focus:ring-2 focus:ring-gold-500 focus:border-transparent"
            />
          </div>

          {/* Description */}
          <div className="mb-6">
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
