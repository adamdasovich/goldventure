'use client';

import React, { useState } from 'react';
import Image from 'next/image';
import { useAuth } from '@/contexts/AuthContext';
import { storeAPI } from '@/lib/api';
import { Button } from '@/components/ui/Button';
import type { StoreProductDetail, StoreProductList } from '@/types/api';

interface ShareToChatProps {
  product: StoreProductDetail | StoreProductList;
  onClose: () => void;
}

type ShareDestination = 'forum' | 'inquiry' | 'direct_message';

export function ShareToChat({ product, onClose }: ShareToChatProps) {
  const { accessToken, isAuthenticated } = useAuth();
  const [selectedDestination, setSelectedDestination] = useState<ShareDestination>('forum');
  const [destinationId, setDestinationId] = useState('');
  const [isSharing, setIsSharing] = useState(false);
  const [shareSuccess, setShareSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleShare = async () => {
    if (!isAuthenticated || !accessToken) {
      setError('Please log in to share products');
      return;
    }

    if (!destinationId) {
      setError('Please enter a destination');
      return;
    }

    setIsSharing(true);
    setError(null);

    try {
      await storeAPI.products.share(
        accessToken,
        product.id,
        selectedDestination,
        destinationId
      );
      setShareSuccess(true);
      setTimeout(() => onClose(), 2000);
    } catch (err: any) {
      setError(err.message || 'Failed to share product');
    } finally {
      setIsSharing(false);
    }
  };

  const imageUrl = 'primary_image' in product && product.primary_image
    ? product.primary_image.image_url
    : null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/70"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative glass rounded-xl max-w-md w-full p-6 animate-slide-in-up">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-slate-400 hover:text-slate-200 transition-colors"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        {shareSuccess ? (
          <div className="text-center py-8">
            <div className="w-16 h-16 rounded-full bg-green-500/20 flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h3 className="text-xl font-bold text-slate-100 mb-2">Shared Successfully!</h3>
            <p className="text-slate-400">Your product link has been shared.</p>
          </div>
        ) : (
          <>
            <h3 className="text-xl font-bold text-slate-100 mb-4">Share to Chat</h3>

            {/* Product Preview */}
            <div className="flex gap-3 p-3 bg-slate-800/50 rounded-lg mb-6">
              <div className="relative w-16 h-16 rounded bg-slate-700 overflow-hidden flex-shrink-0">
                {imageUrl ? (
                  <Image
                    src={imageUrl}
                    alt={product.name}
                    fill
                    className="object-cover"
                    sizes="64px"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-slate-500">
                    📦
                  </div>
                )}
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-medium text-slate-100 truncate">{product.name}</p>
                <p className="text-sm text-gold-400">${product.price_dollars.toFixed(2)}</p>
              </div>
            </div>

            {/* Destination Type */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Share to
              </label>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { id: 'forum', label: 'Forum', icon: '💬' },
                  { id: 'inquiry', label: 'Inquiry', icon: '📧' },
                  { id: 'direct_message', label: 'DM', icon: '✉️' },
                ].map((option) => (
                  <button
                    key={option.id}
                    onClick={() => setSelectedDestination(option.id as ShareDestination)}
                    className={`p-3 rounded-lg border text-center transition-all ${
                      selectedDestination === option.id
                        ? 'border-gold-500 bg-gold-500/20 text-gold-400'
                        : 'border-slate-600 text-slate-300 hover:border-slate-500'
                    }`}
                  >
                    <div className="text-xl mb-1">{option.icon}</div>
                    <div className="text-xs">{option.label}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Destination Input */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-slate-300 mb-2">
                {selectedDestination === 'forum' && 'Forum Thread ID or URL'}
                {selectedDestination === 'inquiry' && 'Inquiry Reference'}
                {selectedDestination === 'direct_message' && 'Username or User ID'}
              </label>
              <input
                type="text"
                value={destinationId}
                onChange={(e) => setDestinationId(e.target.value)}
                placeholder={
                  selectedDestination === 'forum' ? 'Enter thread ID or paste URL'
                  : selectedDestination === 'inquiry' ? 'Enter inquiry reference'
                  : 'Enter username'
                }
                className="w-full px-4 py-2 bg-slate-800 border border-slate-600 rounded-lg text-slate-200 placeholder-slate-500 focus:border-gold-500 focus:ring-1 focus:ring-gold-500"
              />
            </div>

            {error && (
              <div className="mb-4 p-3 bg-red-500/20 border border-red-500/30 rounded-lg text-sm text-red-400">
                {error}
              </div>
            )}

            {/* Actions */}
            <div className="flex gap-3">
              <Button
                variant="ghost"
                className="flex-1"
                onClick={onClose}
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                className="flex-1"
                onClick={handleShare}
                disabled={isSharing || !destinationId}
              >
                {isSharing ? 'Sharing...' : 'Share'}
              </Button>
            </div>

            {!isAuthenticated && (
              <p className="text-xs text-slate-500 text-center mt-4">
                Please log in to share products with the community.
              </p>
            )}
          </>
        )}
      </div>
    </div>
  );
}
