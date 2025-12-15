'use client';

import { useEffect, useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import LogoMono from '@/components/LogoMono';
import { LoginModal } from '@/components/auth/LoginModal';
import { companyResourceAPI } from '@/lib/api';
import type { CompanyResource } from '@/types/api';
import {
  FileText,
  Image,
  Video,
  File,
  Upload,
  Trash2,
  Edit2,
  Eye,
  EyeOff,
  ArrowLeft,
  Plus,
  X,
  Download,
  ExternalLink,
  Star,
  Building2
} from 'lucide-react';

const RESOURCE_TYPES = [
  { value: 'image', label: 'Image', icon: Image },
  { value: 'video', label: 'Video', icon: Video },
  { value: 'document', label: 'Document', icon: FileText },
  { value: 'presentation', label: 'Presentation', icon: FileText },
  { value: 'spreadsheet', label: 'Spreadsheet', icon: File },
  { value: 'other', label: 'Other', icon: File },
];

const RESOURCE_CATEGORIES = [
  { value: 'hero', label: 'Hero Image' },
  { value: 'gallery', label: 'Gallery' },
  { value: 'investor_presentation', label: 'Investor Presentation' },
  { value: 'technical_report', label: 'Technical Report' },
  { value: 'map', label: 'Map' },
  { value: 'logo', label: 'Logo' },
  { value: 'news_image', label: 'News Image' },
  { value: 'other', label: 'Other' },
];

export default function ResourcesPage() {
  const { user, accessToken, isAuthenticated } = useAuth();
  const [resources, setResources] = useState<CompanyResource[]>([]);
  const [loading, setLoading] = useState(true);
  const [showLogin, setShowLogin] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [editingResource, setEditingResource] = useState<CompanyResource | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [uploading, setUploading] = useState(false);

  // Company access state
  const [hasCompany, setHasCompany] = useState<boolean | null>(null);
  const [companyId, setCompanyId] = useState<number | null>(null);
  const [companyName, setCompanyName] = useState<string>('');

  // Form state
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    resource_type: 'document',
    category: 'other',
    is_public: true,
    is_featured: false,
    external_url: '',
  });
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  useEffect(() => {
    if (accessToken && user) {
      // Check if user has a company from auth context
      if (user.company_id) {
        setHasCompany(true);
        setCompanyId(user.company_id);
        setCompanyName(user.company_name || '');
        fetchResources();
      } else {
        setHasCompany(false);
        setLoading(false);
      }
    } else {
      setLoading(false);
    }
  }, [accessToken, user]);

  const fetchResources = async () => {
    if (!accessToken) return;

    try {
      setLoading(true);
      const data = await companyResourceAPI.getMyResources(accessToken);
      setResources(data.results || []);
    } catch (error) {
      console.error('Error fetching resources:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!accessToken) return;

    // Get company ID from editing resource or from state
    const resourceCompanyId = editingResource?.company || companyId;
    if (!resourceCompanyId && !editingResource) {
      alert('Unable to determine company. Please go back to Company Portal and try again.');
      return;
    }

    try {
      setUploading(true);
      const formPayload = new FormData();
      formPayload.append('title', formData.title);
      formPayload.append('description', formData.description);
      formPayload.append('resource_type', formData.resource_type);
      formPayload.append('category', formData.category);
      formPayload.append('is_public', String(formData.is_public));
      formPayload.append('is_featured', String(formData.is_featured));

      // Include company ID for new resources
      if (!editingResource && resourceCompanyId) {
        formPayload.append('company', String(resourceCompanyId));
      }

      if (formData.external_url) {
        formPayload.append('external_url', formData.external_url);
      }

      if (selectedFile) {
        formPayload.append('file', selectedFile);
      }

      if (editingResource) {
        await companyResourceAPI.update(accessToken, editingResource.id, formPayload);
      } else {
        await companyResourceAPI.create(accessToken, formPayload);
      }

      await fetchResources();
      resetForm();
      setShowUploadModal(false);
    } catch (error) {
      console.error('Error saving resource:', error);
      alert('Failed to save resource. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!accessToken) return;
    if (!confirm('Are you sure you want to delete this resource?')) return;

    try {
      await companyResourceAPI.delete(accessToken, id);
      await fetchResources();
    } catch (error) {
      console.error('Error deleting resource:', error);
      alert('Failed to delete resource. Please try again.');
    }
  };

  const handleEdit = (resource: CompanyResource) => {
    setEditingResource(resource);
    setFormData({
      title: resource.title,
      description: resource.description || '',
      resource_type: resource.resource_type,
      category: resource.category,
      is_public: resource.is_public,
      is_featured: resource.is_featured,
      external_url: resource.external_url || '',
    });
    setShowUploadModal(true);
  };

  const resetForm = () => {
    setFormData({
      title: '',
      description: '',
      resource_type: 'document',
      category: 'other',
      is_public: true,
      is_featured: false,
      external_url: '',
    });
    setSelectedFile(null);
    setEditingResource(null);
  };

  const getResourceIcon = (type: string) => {
    const found = RESOURCE_TYPES.find((t) => t.value === type);
    const Icon = found?.icon || File;
    return <Icon className="w-5 h-5 text-gold-400" />;
  };

  const filteredResources = selectedCategory === 'all'
    ? resources
    : resources.filter((r) => r.category === selectedCategory);

  // Not logged in
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <Card variant="glass-card" className="max-w-md w-full mx-4">
          <CardContent className="py-8 text-center">
            <FileText className="w-16 h-16 text-gold-400 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-white mb-2">Sign In Required</h2>
            <p className="text-slate-400 mb-6">Please sign in to manage your resources.</p>
            <Button variant="primary" onClick={() => setShowLogin(true)}>Sign In</Button>
          </CardContent>
        </Card>
        {showLogin && <LoginModal onClose={() => setShowLogin(false)} onSwitchToRegister={() => setShowLogin(false)} />}
      </div>
    );
  }

  // Loading
  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-gold-400"></div>
      </div>
    );
  }

  // No company access - redirect to Company Portal
  if (hasCompany === false) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <Card variant="glass-card" className="max-w-md w-full mx-4">
          <CardContent className="py-8 text-center">
            <Building2 className="w-16 h-16 text-gold-400 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-white mb-2">Company Access Required</h2>
            <p className="text-slate-400 mb-6">
              You need to be associated with a company to manage resources.
              Please request access from the Company Portal.
            </p>
            <Button variant="primary" onClick={() => window.location.href = '/company-portal'}>
              Go to Company Portal
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Navigation */}
      <nav className="glass-nav sticky top-0 z-50 border-b border-gold-500/10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <a href="/" className="flex items-center space-x-3">
              <LogoMono className="h-8 w-8 text-gold-400" />
              <span className="text-xl font-bold text-gradient-gold">GoldVenture</span>
            </a>
            <Button variant="ghost" onClick={() => window.location.href = '/company-portal'}>
              <ArrowLeft className="w-4 h-4 mr-2" /> Back to Portal
            </Button>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white">Resources</h1>
            <p className="text-slate-400">Upload and manage presentations, documents, and media</p>
          </div>
          <Button variant="primary" onClick={() => { resetForm(); setShowUploadModal(true); }}>
            <Plus className="w-4 h-4 mr-2" /> Upload Resource
          </Button>
        </div>

        {/* Category Filter */}
        <div className="flex flex-wrap gap-2 mb-8">
          <Button
            variant={selectedCategory === 'all' ? 'primary' : 'secondary'}
            size="sm"
            onClick={() => setSelectedCategory('all')}
          >
            All ({resources.length})
          </Button>
          {RESOURCE_CATEGORIES.map((cat) => {
            const count = resources.filter((r) => r.category === cat.value).length;
            if (count === 0) return null;
            return (
              <Button
                key={cat.value}
                variant={selectedCategory === cat.value ? 'primary' : 'secondary'}
                size="sm"
                onClick={() => setSelectedCategory(cat.value)}
              >
                {cat.label} ({count})
              </Button>
            );
          })}
        </div>

        {/* Resources Grid */}
        {filteredResources.length === 0 ? (
          <Card variant="glass" className="py-16 text-center">
            <Upload className="w-16 h-16 text-slate-600 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-white mb-2">No resources yet</h3>
            <p className="text-slate-400 mb-6">Upload your first resource to get started</p>
            <Button variant="primary" onClick={() => { resetForm(); setShowUploadModal(true); }}>
              <Plus className="w-4 h-4 mr-2" /> Upload Resource
            </Button>
          </Card>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredResources.map((resource) => (
              <Card key={resource.id} variant="glass" className="overflow-hidden">
                {/* Preview/Thumbnail */}
                {resource.resource_type === 'image' && resource.file_url ? (
                  <div className="aspect-video bg-slate-800 overflow-hidden">
                    <img
                      src={resource.file_url}
                      alt={resource.title}
                      className="w-full h-full object-cover"
                    />
                  </div>
                ) : (
                  <div className="aspect-video bg-slate-800 flex items-center justify-center">
                    {getResourceIcon(resource.resource_type)}
                  </div>
                )}

                <CardContent className="p-4">
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <h3 className="text-white font-semibold line-clamp-1">{resource.title}</h3>
                    {resource.is_featured && (
                      <Star className="w-4 h-4 text-gold-400 flex-shrink-0" />
                    )}
                  </div>

                  <div className="flex items-center gap-2 mb-3">
                    <Badge variant="slate">
                      {RESOURCE_CATEGORIES.find((c) => c.value === resource.category)?.label || resource.category}
                    </Badge>
                    <Badge variant={resource.is_public ? 'gold' : 'slate'}>
                      {resource.is_public ? <Eye className="w-3 h-3 mr-1" /> : <EyeOff className="w-3 h-3 mr-1" />}
                      {resource.is_public ? 'Public' : 'Private'}
                    </Badge>
                  </div>

                  {resource.description && (
                    <p className="text-slate-400 text-sm line-clamp-2 mb-3">{resource.description}</p>
                  )}

                  <div className="flex items-center justify-between pt-3 border-t border-slate-700">
                    <div className="flex items-center gap-2">
                      {resource.file_url && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => window.open(resource.file_url, '_blank')}
                        >
                          <Download className="w-4 h-4" />
                        </Button>
                      )}
                      {resource.external_url && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => window.open(resource.external_url, '_blank')}
                        >
                          <ExternalLink className="w-4 h-4" />
                        </Button>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      <Button variant="ghost" size="sm" onClick={() => handleEdit(resource)}>
                        <Edit2 className="w-4 h-4" />
                      </Button>
                      <Button variant="ghost" size="sm" onClick={() => handleDelete(resource.id)}>
                        <Trash2 className="w-4 h-4 text-red-400" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Upload/Edit Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
          <Card variant="glass-card" className="max-w-lg w-full max-h-[90vh] overflow-y-auto">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-white">
                {editingResource ? 'Edit Resource' : 'Upload Resource'}
              </CardTitle>
              <Button variant="ghost" size="sm" onClick={() => { setShowUploadModal(false); resetForm(); }}>
                <X className="w-5 h-5" />
              </Button>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1">Title *</label>
                  <input
                    type="text"
                    value={formData.title}
                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                    required
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white focus:border-gold-500 focus:outline-none"
                    placeholder="Enter resource title"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1">Description</label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    rows={3}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white focus:border-gold-500 focus:outline-none"
                    placeholder="Enter description"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-1">Type *</label>
                    <select
                      value={formData.resource_type}
                      onChange={(e) => setFormData({ ...formData, resource_type: e.target.value })}
                      className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white focus:border-gold-500 focus:outline-none"
                    >
                      {RESOURCE_TYPES.map((type) => (
                        <option key={type.value} value={type.value}>{type.label}</option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-1">Category *</label>
                    <select
                      value={formData.category}
                      onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                      className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white focus:border-gold-500 focus:outline-none"
                    >
                      {RESOURCE_CATEGORIES.map((cat) => (
                        <option key={cat.value} value={cat.value}>{cat.label}</option>
                      ))}
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1">
                    File {!editingResource && '*'}
                  </label>
                  <input
                    type="file"
                    onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white focus:border-gold-500 focus:outline-none file:mr-4 file:py-1 file:px-3 file:rounded file:border-0 file:bg-gold-500/20 file:text-gold-400"
                  />
                  {editingResource && editingResource.file_url && (
                    <p className="text-slate-400 text-sm mt-1">
                      Current file will be kept if no new file is selected
                    </p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1">External URL (optional)</label>
                  <input
                    type="url"
                    value={formData.external_url}
                    onChange={(e) => setFormData({ ...formData, external_url: e.target.value })}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white focus:border-gold-500 focus:outline-none"
                    placeholder="https://example.com/resource"
                  />
                </div>

                <div className="flex items-center gap-6">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.is_public}
                      onChange={(e) => setFormData({ ...formData, is_public: e.target.checked })}
                      className="rounded border-slate-600 bg-slate-800 text-gold-500 focus:ring-gold-500"
                    />
                    <span className="text-slate-300">Public</span>
                  </label>

                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.is_featured}
                      onChange={(e) => setFormData({ ...formData, is_featured: e.target.checked })}
                      className="rounded border-slate-600 bg-slate-800 text-gold-500 focus:ring-gold-500"
                    />
                    <span className="text-slate-300">Featured</span>
                  </label>
                </div>

                <div className="flex justify-end gap-3 pt-4">
                  <Button type="button" variant="ghost" onClick={() => { setShowUploadModal(false); resetForm(); }}>
                    Cancel
                  </Button>
                  <Button type="submit" variant="primary" disabled={uploading}>
                    {uploading ? 'Saving...' : editingResource ? 'Update' : 'Upload'}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
