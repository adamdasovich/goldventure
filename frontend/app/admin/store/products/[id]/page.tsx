'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import {
  storeAdminAPI,
  type StoreProductAdmin,
  type StoreCategoryAdmin,
  type StoreProductImage,
  type StoreProductVariant,
  type StoreDigitalAsset,
} from '@/lib/api';
import { Button } from '@/components/ui/Button';

const BADGE_OPTIONS = [
  { value: 'rare', label: 'Rare' },
  { value: 'limited_edition', label: 'Limited Edition' },
  { value: 'community_favorite', label: 'Community Favorite' },
  { value: 'new_arrival', label: 'New Arrival' },
  { value: 'instant_download', label: 'Instant Download' },
];

export default function ProductEditPage() {
  const params = useParams();
  const router = useRouter();
  const { accessToken } = useAuth();
  const isNew = params.id === 'new';
  const productId = isNew ? null : Number(params.id);

  const [isLoading, setIsLoading] = useState(!isNew);
  const [isSaving, setIsSaving] = useState(false);
  const [categories, setCategories] = useState<StoreCategoryAdmin[]>([]);

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    slug: '',
    description: '',
    short_description: '',
    category: '' as number | '',
    price_cents: 0,
    compare_at_price_cents: null as number | null,
    product_type: 'physical' as 'physical' | 'digital',
    sku: '',
    inventory_count: 0,
    weight_grams: 0,
    is_active: false,
    is_featured: false,
    badges: [] as string[],
    provenance_info: '',
    authentication_docs: [] as string[],
    min_price_for_inquiry: 500000,
  });

  const [images, setImages] = useState<StoreProductImage[]>([]);
  const [variants, setVariants] = useState<StoreProductVariant[]>([]);
  const [digitalAssets, setDigitalAssets] = useState<StoreDigitalAsset[]>([]);

  // New image/variant forms
  const [newImageUrl, setNewImageUrl] = useState('');
  const [newVariantName, setNewVariantName] = useState('');
  const [newVariantPrice, setNewVariantPrice] = useState('');

  // Fetch categories
  useEffect(() => {
    if (!accessToken) return;

    storeAdminAPI.categories.getAll(accessToken)
      .then(setCategories)
      .catch(console.error);
  }, [accessToken]);

  // Fetch product if editing
  useEffect(() => {
    if (!accessToken || isNew || !productId) return;

    const fetchProduct = async () => {
      try {
        const product = await storeAdminAPI.products.getById(accessToken, productId);
        setFormData({
          name: product.name,
          slug: product.slug,
          description: product.description,
          short_description: product.short_description,
          category: product.category || '',
          price_cents: product.price_cents,
          compare_at_price_cents: product.compare_at_price_cents,
          product_type: product.product_type,
          sku: product.sku || '',
          inventory_count: product.inventory_count,
          weight_grams: product.weight_grams,
          is_active: product.is_active,
          is_featured: product.is_featured,
          badges: product.badges,
          provenance_info: product.provenance_info,
          authentication_docs: product.authentication_docs,
          min_price_for_inquiry: product.min_price_for_inquiry,
        });
        setImages(product.images || []);
        setVariants(product.variants || []);
        setDigitalAssets(product.digital_assets || []);
      } catch (err) {
        console.error('Failed to fetch product:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchProduct();
  }, [accessToken, isNew, productId]);

  // Auto-generate slug from name
  const generateSlug = (name: string) => {
    return name
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-|-$/g, '');
  };

  const handleNameChange = (name: string) => {
    setFormData(prev => ({
      ...prev,
      name,
      slug: isNew ? generateSlug(name) : prev.slug,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!accessToken) return;

    setIsSaving(true);
    try {
      const data = {
        ...formData,
        category: formData.category || null,
        sku: formData.sku || null,
      };

      if (isNew) {
        const product = await storeAdminAPI.products.create(accessToken, data);
        router.push(`/admin/store/products/${product.id}`);
      } else if (productId) {
        await storeAdminAPI.products.update(accessToken, productId, data);
      }
    } catch (err) {
      console.error('Failed to save product:', err);
      alert('Failed to save product');
    } finally {
      setIsSaving(false);
    }
  };

  const handleAddImage = async () => {
    if (!accessToken || !productId || !newImageUrl) return;

    try {
      const image = await storeAdminAPI.products.addImage(accessToken, productId, {
        image_url: newImageUrl,
        is_primary: images.length === 0,
      });
      setImages([...images, image]);
      setNewImageUrl('');
    } catch (err) {
      console.error('Failed to add image:', err);
      alert('Failed to add image');
    }
  };

  const handleDeleteImage = async (imageId: number) => {
    if (!accessToken) return;

    try {
      await storeAdminAPI.images.delete(accessToken, imageId);
      setImages(images.filter(i => i.id !== imageId));
    } catch (err) {
      console.error('Failed to delete image:', err);
      alert('Failed to delete image');
    }
  };

  const handleSetPrimaryImage = async (imageId: number) => {
    if (!accessToken) return;

    try {
      await storeAdminAPI.images.update(accessToken, imageId, { is_primary: true });
      setImages(images.map(i => ({ ...i, is_primary: i.id === imageId })));
    } catch (err) {
      console.error('Failed to set primary image:', err);
    }
  };

  const handleAddVariant = async () => {
    if (!accessToken || !productId || !newVariantName) return;

    try {
      const variant = await storeAdminAPI.products.addVariant(accessToken, productId, {
        name: newVariantName,
        price_cents_override: newVariantPrice ? Number(newVariantPrice) * 100 : undefined,
      });
      setVariants([...variants, variant]);
      setNewVariantName('');
      setNewVariantPrice('');
    } catch (err) {
      console.error('Failed to add variant:', err);
      alert('Failed to add variant');
    }
  };

  const handleDeleteVariant = async (variantId: number) => {
    if (!accessToken) return;

    try {
      await storeAdminAPI.variants.delete(accessToken, variantId);
      setVariants(variants.filter(v => v.id !== variantId));
    } catch (err) {
      console.error('Failed to delete variant:', err);
      alert('Failed to delete variant');
    }
  };

  const handleBadgeToggle = (badge: string) => {
    setFormData(prev => ({
      ...prev,
      badges: prev.badges.includes(badge)
        ? prev.badges.filter(b => b !== badge)
        : [...prev.badges, badge],
    }));
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="animate-spin w-8 h-8 border-2 border-gold-500 border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link
            href="/admin/store/products"
            className="p-2 text-slate-400 hover:text-slate-200 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-slate-100">
              {isNew ? 'Add Product' : 'Edit Product'}
            </h1>
            {!isNew && (
              <p className="text-slate-400 text-sm">ID: {productId}</p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Link href="/admin/store/products">
            <Button variant="secondary">Cancel</Button>
          </Link>
          <Button
            variant="primary"
            onClick={handleSubmit}
            disabled={isSaving}
          >
            {isSaving ? 'Saving...' : 'Save Product'}
          </Button>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Basic Info */}
        <div className="glass rounded-xl p-6 space-y-4">
          <h2 className="text-lg font-semibold text-slate-100">Basic Information</h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">
                Product Name *
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
              Short Description
            </label>
            <input
              type="text"
              maxLength={500}
              value={formData.short_description}
              onChange={(e) => setFormData({ ...formData, short_description: e.target.value })}
              className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:border-gold-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">
              Full Description (Markdown supported)
            </label>
            <textarea
              rows={6}
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:border-gold-500 font-mono text-sm"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">
                Category
              </label>
              <select
                value={formData.category}
                onChange={(e) => setFormData({ ...formData, category: e.target.value ? Number(e.target.value) : '' })}
                className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:border-gold-500"
              >
                <option value="">Select category</option>
                {categories.map((cat) => (
                  <option key={cat.id} value={cat.id}>{cat.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">
                Product Type
              </label>
              <select
                value={formData.product_type}
                onChange={(e) => setFormData({ ...formData, product_type: e.target.value as 'physical' | 'digital' })}
                className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:border-gold-500"
              >
                <option value="physical">Physical</option>
                <option value="digital">Digital</option>
              </select>
            </div>
          </div>
        </div>

        {/* Pricing & Inventory */}
        <div className="glass rounded-xl p-6 space-y-4">
          <h2 className="text-lg font-semibold text-slate-100">Pricing & Inventory</h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">
                Price ($) *
              </label>
              <input
                type="number"
                required
                min="0"
                step="0.01"
                value={formData.price_cents / 100}
                onChange={(e) => setFormData({ ...formData, price_cents: Math.round(Number(e.target.value) * 100) })}
                className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:border-gold-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">
                Compare At Price ($)
              </label>
              <input
                type="number"
                min="0"
                step="0.01"
                value={formData.compare_at_price_cents ? formData.compare_at_price_cents / 100 : ''}
                onChange={(e) => setFormData({ ...formData, compare_at_price_cents: e.target.value ? Math.round(Number(e.target.value) * 100) : null })}
                className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:border-gold-500"
                placeholder="Original price for sales"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">
                SKU
              </label>
              <input
                type="text"
                value={formData.sku}
                onChange={(e) => setFormData({ ...formData, sku: e.target.value })}
                className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:border-gold-500"
              />
            </div>
          </div>

          {formData.product_type === 'physical' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">
                  Inventory Count
                </label>
                <input
                  type="number"
                  min="0"
                  value={formData.inventory_count}
                  onChange={(e) => setFormData({ ...formData, inventory_count: Number(e.target.value) })}
                  className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:border-gold-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">
                  Weight (grams)
                </label>
                <input
                  type="number"
                  min="0"
                  value={formData.weight_grams}
                  onChange={(e) => setFormData({ ...formData, weight_grams: Number(e.target.value) })}
                  className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:border-gold-500"
                />
              </div>
            </div>
          )}
        </div>

        {/* Status & Badges */}
        <div className="glass rounded-xl p-6 space-y-4">
          <h2 className="text-lg font-semibold text-slate-100">Status & Badges</h2>

          <div className="flex flex-wrap gap-4">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={formData.is_active}
                onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                className="w-4 h-4 rounded border-slate-600 bg-slate-800 text-gold-500 focus:ring-gold-500"
              />
              <span className="text-slate-300">Active (visible in store)</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={formData.is_featured}
                onChange={(e) => setFormData({ ...formData, is_featured: e.target.checked })}
                className="w-4 h-4 rounded border-slate-600 bg-slate-800 text-gold-500 focus:ring-gold-500"
              />
              <span className="text-slate-300">Featured</span>
            </label>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">Badges</label>
            <div className="flex flex-wrap gap-2">
              {BADGE_OPTIONS.map((badge) => (
                <button
                  key={badge.value}
                  type="button"
                  onClick={() => handleBadgeToggle(badge.value)}
                  className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
                    formData.badges.includes(badge.value)
                      ? 'bg-gold-500/20 text-gold-400 border border-gold-500/40'
                      : 'bg-slate-700 text-slate-400 hover:bg-slate-600'
                  }`}
                >
                  {badge.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Images (only for existing products) */}
        {!isNew && (
          <div className="glass rounded-xl p-6 space-y-4">
            <h2 className="text-lg font-semibold text-slate-100">Images</h2>

            {/* Existing Images */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              {images.map((image) => (
                <div key={image.id} className="relative group">
                  <div className="aspect-square bg-slate-800 rounded-lg overflow-hidden">
                    <img
                      src={image.image_url}
                      alt={image.alt_text || ''}
                      className="w-full h-full object-cover"
                    />
                  </div>
                  {image.is_primary && (
                    <span className="absolute top-2 left-2 px-2 py-0.5 bg-gold-500 text-slate-900 text-xs font-medium rounded">
                      Primary
                    </span>
                  )}
                  <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
                    {!image.is_primary && (
                      <button
                        type="button"
                        onClick={() => handleSetPrimaryImage(image.id)}
                        className="p-2 bg-slate-800 rounded-lg text-slate-200 hover:text-gold-400"
                        title="Set as primary"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                      </button>
                    )}
                    <button
                      type="button"
                      onClick={() => handleDeleteImage(image.id)}
                      className="p-2 bg-slate-800 rounded-lg text-slate-200 hover:text-red-400"
                      title="Delete"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </div>
                </div>
              ))}
            </div>

            {/* Add Image */}
            <div className="flex gap-2">
              <input
                type="url"
                value={newImageUrl}
                onChange={(e) => setNewImageUrl(e.target.value)}
                placeholder="Enter image URL"
                className="flex-1 px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:border-gold-500"
              />
              <Button
                type="button"
                variant="secondary"
                onClick={handleAddImage}
                disabled={!newImageUrl}
              >
                Add Image
              </Button>
            </div>
          </div>
        )}

        {/* Variants (only for existing products) */}
        {!isNew && (
          <div className="glass rounded-xl p-6 space-y-4">
            <h2 className="text-lg font-semibold text-slate-100">Variants</h2>

            {/* Existing Variants */}
            {variants.length > 0 && (
              <div className="space-y-2">
                {variants.map((variant) => (
                  <div key={variant.id} className="flex items-center justify-between bg-slate-800/50 rounded-lg px-4 py-3">
                    <div>
                      <span className="text-slate-100 font-medium">{variant.name}</span>
                      {variant.price_cents_override && (
                        <span className="text-gold-400 ml-2">
                          ${(variant.price_cents_override / 100).toFixed(2)}
                        </span>
                      )}
                    </div>
                    <button
                      type="button"
                      onClick={() => handleDeleteVariant(variant.id)}
                      className="p-2 text-slate-400 hover:text-red-400 transition-colors"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                ))}
              </div>
            )}

            {/* Add Variant */}
            <div className="flex gap-2">
              <input
                type="text"
                value={newVariantName}
                onChange={(e) => setNewVariantName(e.target.value)}
                placeholder="Variant name (e.g., Large, Digital)"
                className="flex-1 px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:border-gold-500"
              />
              <input
                type="number"
                value={newVariantPrice}
                onChange={(e) => setNewVariantPrice(e.target.value)}
                placeholder="Price override ($)"
                className="w-32 px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:border-gold-500"
              />
              <Button
                type="button"
                variant="secondary"
                onClick={handleAddVariant}
                disabled={!newVariantName}
              >
                Add Variant
              </Button>
            </div>
          </div>
        )}

        {/* Provenance (for vault items) */}
        <div className="glass rounded-xl p-6 space-y-4">
          <h2 className="text-lg font-semibold text-slate-100">Provenance & Authentication</h2>
          <p className="text-sm text-slate-400">For premium/vault items</p>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">
              Provenance Information
            </label>
            <textarea
              rows={4}
              value={formData.provenance_info}
              onChange={(e) => setFormData({ ...formData, provenance_info: e.target.value })}
              placeholder="History, origin, and authenticity details..."
              className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:border-gold-500"
            />
          </div>
        </div>

        {/* Save hint for new products */}
        {isNew && (
          <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4 text-blue-300 text-sm">
            Save the product first to add images and variants.
          </div>
        )}
      </form>
    </div>
  );
}
