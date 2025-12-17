'use client';

import React, { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import { storeAdminAPI, type StoreProductAdmin, type StoreCategoryAdmin } from '@/lib/api';
import { Button } from '@/components/ui/Button';

export default function ProductsListPage() {
  const { accessToken } = useAuth();
  const [products, setProducts] = useState<StoreProductAdmin[]>([]);
  const [categories, setCategories] = useState<StoreCategoryAdmin[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [search, setSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<number | ''>('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [typeFilter, setTypeFilter] = useState<string>('');

  const fetchProducts = useCallback(async () => {
    if (!accessToken) return;

    setIsLoading(true);
    try {
      const params: {
        search?: string;
        category?: number;
        is_active?: boolean;
        type?: string;
      } = {};

      if (search) params.search = search;
      if (categoryFilter) params.category = categoryFilter;
      if (statusFilter === 'active') params.is_active = true;
      if (statusFilter === 'inactive') params.is_active = false;
      if (typeFilter) params.type = typeFilter;

      const data = await storeAdminAPI.products.getAll(accessToken, params);
      setProducts(data);
    } catch (err) {
      console.error('Failed to fetch products:', err);
      setError('Failed to load products');
    } finally {
      setIsLoading(false);
    }
  }, [accessToken, search, categoryFilter, statusFilter, typeFilter]);

  useEffect(() => {
    fetchProducts();
  }, [fetchProducts]);

  useEffect(() => {
    if (!accessToken) return;

    const fetchCategories = async () => {
      try {
        const data = await storeAdminAPI.categories.getAll(accessToken);
        setCategories(data);
      } catch (err) {
        console.error('Failed to fetch categories:', err);
      }
    };

    fetchCategories();
  }, [accessToken]);

  const handleDelete = async (product: StoreProductAdmin) => {
    if (!confirm(`Are you sure you want to delete "${product.name}"?`)) return;
    if (!accessToken) return;

    try {
      await storeAdminAPI.products.delete(accessToken, product.id);
      setProducts(products.filter(p => p.id !== product.id));
    } catch (err) {
      console.error('Failed to delete product:', err);
      alert('Failed to delete product');
    }
  };

  const handleDuplicate = async (product: StoreProductAdmin) => {
    if (!accessToken) return;

    try {
      const newProduct = await storeAdminAPI.products.duplicate(accessToken, product.id);
      setProducts([newProduct, ...products]);
    } catch (err) {
      console.error('Failed to duplicate product:', err);
      alert('Failed to duplicate product');
    }
  };

  const handleToggleActive = async (product: StoreProductAdmin) => {
    if (!accessToken) return;

    try {
      const updated = await storeAdminAPI.products.patch(accessToken, product.id, {
        is_active: !product.is_active,
      });
      setProducts(products.map(p => p.id === product.id ? updated : p));
    } catch (err) {
      console.error('Failed to update product:', err);
      alert('Failed to update product');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Products</h1>
          <p className="text-slate-400 mt-1">Manage your store products</p>
        </div>
        <Link href="/admin/store/products/new">
          <Button variant="primary">
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Add Product
          </Button>
        </Link>
      </div>

      {/* Filters */}
      <div className="glass rounded-xl p-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Search */}
          <div className="relative">
            <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              type="text"
              placeholder="Search products..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-gold-500"
            />
          </div>

          {/* Category Filter */}
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value ? Number(e.target.value) : '')}
            className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:border-gold-500"
          >
            <option value="">All Categories</option>
            {categories.map((cat) => (
              <option key={cat.id} value={cat.id}>{cat.name}</option>
            ))}
          </select>

          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:border-gold-500"
          >
            <option value="">All Status</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </select>

          {/* Type Filter */}
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:border-gold-500"
          >
            <option value="">All Types</option>
            <option value="physical">Physical</option>
            <option value="digital">Digital</option>
          </select>
        </div>
      </div>

      {/* Products Table */}
      <div className="glass rounded-xl overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center">
            <div className="animate-spin w-8 h-8 border-2 border-gold-500 border-t-transparent rounded-full mx-auto" />
          </div>
        ) : error ? (
          <div className="p-8 text-center text-red-400">{error}</div>
        ) : products.length === 0 ? (
          <div className="p-8 text-center">
            <div className="mb-4">
              <svg className="w-16 h-16 text-slate-500 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-slate-100 mb-2">No products found</h3>
            <p className="text-slate-400 mb-4">Get started by adding your first product.</p>
            <Link href="/admin/store/products/new">
              <Button variant="primary">Add Product</Button>
            </Link>
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-slate-800/50">
              <tr>
                <th className="text-left px-4 py-3 text-sm font-medium text-slate-400">Product</th>
                <th className="text-left px-4 py-3 text-sm font-medium text-slate-400">Category</th>
                <th className="text-left px-4 py-3 text-sm font-medium text-slate-400">Price</th>
                <th className="text-left px-4 py-3 text-sm font-medium text-slate-400">Inventory</th>
                <th className="text-left px-4 py-3 text-sm font-medium text-slate-400">Status</th>
                <th className="text-right px-4 py-3 text-sm font-medium text-slate-400">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700">
              {products.map((product) => (
                <tr key={product.id} className="hover:bg-slate-800/30 transition-colors">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-3">
                      {/* Product Image */}
                      <div className="w-12 h-12 bg-slate-800 rounded-lg overflow-hidden flex-shrink-0">
                        {product.primary_image ? (
                          <img
                            src={product.primary_image}
                            alt={product.name}
                            className="w-full h-full object-cover"
                          />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center">
                            <svg className="w-6 h-6 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                            </svg>
                          </div>
                        )}
                      </div>
                      {/* Product Info */}
                      <div>
                        <p className="font-medium text-slate-100">{product.name}</p>
                        <p className="text-sm text-slate-400">
                          {product.product_type === 'digital' ? 'Digital' : 'Physical'}
                          {product.sku && ` • ${product.sku}`}
                        </p>
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-slate-300">
                    {product.category_name || '-'}
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-slate-100 font-medium">
                      ${(product.price_cents / 100).toFixed(2)}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    {product.product_type === 'digital' ? (
                      <span className="text-slate-400">Unlimited</span>
                    ) : (
                      <span className={product.inventory_count > 0 ? 'text-green-400' : 'text-red-400'}>
                        {product.inventory_count}
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => handleToggleActive(product)}
                      className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium transition-colors ${
                        product.is_active
                          ? 'bg-green-500/20 text-green-400 hover:bg-green-500/30'
                          : 'bg-slate-700 text-slate-400 hover:bg-slate-600'
                      }`}
                    >
                      {product.is_active ? 'Active' : 'Inactive'}
                    </button>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-end gap-2">
                      <Link
                        href={`/admin/store/products/${product.id}`}
                        className="p-2 text-slate-400 hover:text-gold-400 transition-colors"
                        title="Edit"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                        </svg>
                      </Link>
                      <button
                        onClick={() => handleDuplicate(product)}
                        className="p-2 text-slate-400 hover:text-blue-400 transition-colors"
                        title="Duplicate"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                        </svg>
                      </button>
                      <button
                        onClick={() => handleDelete(product)}
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
