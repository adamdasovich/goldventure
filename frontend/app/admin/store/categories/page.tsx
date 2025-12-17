'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { storeAdminAPI, type StoreCategoryAdmin } from '@/lib/api';
import { Button } from '@/components/ui/Button';

export default function CategoriesPage() {
  const { accessToken } = useAuth();
  const [categories, setCategories] = useState<StoreCategoryAdmin[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [showNewForm, setShowNewForm] = useState(false);

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    slug: '',
    description: '',
    display_order: 0,
    icon: '',
    is_active: true,
  });

  const fetchCategories = useCallback(async () => {
    if (!accessToken) return;

    setIsLoading(true);
    try {
      const data = await storeAdminAPI.categories.getAll(accessToken);
      setCategories(data);
    } catch (err) {
      console.error('Failed to fetch categories:', err);
    } finally {
      setIsLoading(false);
    }
  }, [accessToken]);

  useEffect(() => {
    fetchCategories();
  }, [fetchCategories]);

  const generateSlug = (name: string) => {
    return name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
  };

  const handleNameChange = (name: string) => {
    setFormData(prev => ({
      ...prev,
      name,
      slug: editingId ? prev.slug : generateSlug(name),
    }));
  };

  const resetForm = () => {
    setFormData({
      name: '',
      slug: '',
      description: '',
      display_order: 0,
      icon: '',
      is_active: true,
    });
    setEditingId(null);
    setShowNewForm(false);
  };

  const startEdit = (category: StoreCategoryAdmin) => {
    setFormData({
      name: category.name,
      slug: category.slug,
      description: category.description,
      display_order: category.display_order,
      icon: category.icon,
      is_active: category.is_active,
    });
    setEditingId(category.id);
    setShowNewForm(false);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!accessToken) return;

    try {
      if (editingId) {
        const updated = await storeAdminAPI.categories.update(accessToken, editingId, formData);
        setCategories(categories.map(c => c.id === editingId ? updated : c));
      } else {
        const created = await storeAdminAPI.categories.create(accessToken, formData);
        setCategories([...categories, created]);
      }
      resetForm();
    } catch (err) {
      console.error('Failed to save category:', err);
      alert('Failed to save category');
    }
  };

  const handleDelete = async (category: StoreCategoryAdmin) => {
    if (!confirm(`Are you sure you want to delete "${category.name}"? This will affect ${category.product_count} products.`)) return;
    if (!accessToken) return;

    try {
      await storeAdminAPI.categories.delete(accessToken, category.id);
      setCategories(categories.filter(c => c.id !== category.id));
    } catch (err) {
      console.error('Failed to delete category:', err);
      alert('Failed to delete category');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Categories</h1>
          <p className="text-slate-400 mt-1">Manage store product categories</p>
        </div>
        {!showNewForm && !editingId && (
          <Button variant="primary" onClick={() => setShowNewForm(true)}>
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Add Category
          </Button>
        )}
      </div>

      {/* New/Edit Form */}
      {(showNewForm || editingId) && (
        <div className="glass rounded-xl p-6">
          <h2 className="text-lg font-semibold text-slate-100 mb-4">
            {editingId ? 'Edit Category' : 'New Category'}
          </h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">
                  Name *
                </label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => handleNameChange(e.target.value)}
                  className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:border-gold-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">
                  Slug *
                </label>
                <input
                  type="text"
                  required
                  value={formData.slug}
                  onChange={(e) => setFormData({ ...formData, slug: e.target.value })}
                  className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:border-gold-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">
                Description
              </label>
              <textarea
                rows={3}
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:border-gold-500"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">
                  Display Order
                </label>
                <input
                  type="number"
                  value={formData.display_order}
                  onChange={(e) => setFormData({ ...formData, display_order: Number(e.target.value) })}
                  className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:border-gold-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">
                  Icon (class name)
                </label>
                <input
                  type="text"
                  value={formData.icon}
                  onChange={(e) => setFormData({ ...formData, icon: e.target.value })}
                  placeholder="e.g., vault, gear, book"
                  className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:border-gold-500"
                />
              </div>
              <div className="flex items-end">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.is_active}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                    className="w-4 h-4 rounded border-slate-600 bg-slate-800 text-gold-500 focus:ring-gold-500"
                  />
                  <span className="text-slate-300">Active</span>
                </label>
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-4">
              <Button type="button" variant="secondary" onClick={resetForm}>
                Cancel
              </Button>
              <Button type="submit" variant="primary">
                {editingId ? 'Update' : 'Create'} Category
              </Button>
            </div>
          </form>
        </div>
      )}

      {/* Categories List */}
      <div className="glass rounded-xl overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center">
            <div className="animate-spin w-8 h-8 border-2 border-gold-500 border-t-transparent rounded-full mx-auto" />
          </div>
        ) : categories.length === 0 ? (
          <div className="p-8 text-center">
            <svg className="w-16 h-16 text-slate-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
            </svg>
            <h3 className="text-lg font-medium text-slate-100 mb-2">No categories yet</h3>
            <p className="text-slate-400 mb-4">Create your first category to organize products.</p>
            <Button variant="primary" onClick={() => setShowNewForm(true)}>
              Add Category
            </Button>
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-slate-800/50">
              <tr>
                <th className="text-left px-4 py-3 text-sm font-medium text-slate-400">Order</th>
                <th className="text-left px-4 py-3 text-sm font-medium text-slate-400">Name</th>
                <th className="text-left px-4 py-3 text-sm font-medium text-slate-400">Slug</th>
                <th className="text-left px-4 py-3 text-sm font-medium text-slate-400">Products</th>
                <th className="text-left px-4 py-3 text-sm font-medium text-slate-400">Status</th>
                <th className="text-right px-4 py-3 text-sm font-medium text-slate-400">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700">
              {categories.map((category) => (
                <tr key={category.id} className="hover:bg-slate-800/30 transition-colors">
                  <td className="px-4 py-3 text-slate-400">{category.display_order}</td>
                  <td className="px-4 py-3">
                    <span className="font-medium text-slate-100">{category.name}</span>
                    {category.description && (
                      <p className="text-sm text-slate-400 truncate max-w-xs">{category.description}</p>
                    )}
                  </td>
                  <td className="px-4 py-3 text-slate-400 font-mono text-sm">{category.slug}</td>
                  <td className="px-4 py-3">
                    <span className="text-slate-100">{category.product_count}</span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex px-2.5 py-1 rounded-full text-xs font-medium ${
                      category.is_active
                        ? 'bg-green-500/20 text-green-400'
                        : 'bg-slate-700 text-slate-400'
                    }`}>
                      {category.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => startEdit(category)}
                        className="p-2 text-slate-400 hover:text-gold-400 transition-colors"
                        title="Edit"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                        </svg>
                      </button>
                      <button
                        onClick={() => handleDelete(category)}
                        className="p-2 text-slate-400 hover:text-red-400 transition-colors"
                        title="Delete"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
