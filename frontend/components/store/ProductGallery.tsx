'use client';

import React, { useState } from 'react';
import type { StoreProductImage } from '@/types/api';

interface ProductGalleryProps {
  images: StoreProductImage[];
  productName: string;
}

export function ProductGallery({ images, productName }: ProductGalleryProps) {
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [isZoomed, setIsZoomed] = useState(false);

  // Sort images by display_order, primary first
  const sortedImages = [...images].sort((a, b) => {
    if (a.is_primary && !b.is_primary) return -1;
    if (!a.is_primary && b.is_primary) return 1;
    return a.display_order - b.display_order;
  });

  const currentImage = sortedImages[selectedIndex] || sortedImages[0];

  if (!sortedImages.length) {
    return (
      <div className="aspect-square bg-slate-800/50 rounded-xl flex items-center justify-center">
        <span className="text-slate-500">No image available</span>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Main Image */}
      <div
        className="relative aspect-square bg-slate-800/50 rounded-xl overflow-hidden cursor-zoom-in"
        onClick={() => setIsZoomed(true)}
      >
        <img
          src={currentImage.image_url}
          alt={currentImage.alt_text || productName}
          className="absolute inset-0 w-full h-full object-cover transition-transform duration-300 hover:scale-105"
        />
      </div>

      {/* Thumbnails */}
      {sortedImages.length > 1 && (
        <div className="flex gap-2 overflow-x-auto pb-2">
          {sortedImages.map((image, index) => (
            <button
              key={image.id}
              onClick={() => setSelectedIndex(index)}
              className={`relative flex-shrink-0 w-20 h-20 rounded-lg overflow-hidden border-2 transition-all ${
                index === selectedIndex
                  ? 'border-gold-500 ring-2 ring-gold-500/30'
                  : 'border-slate-700 hover:border-slate-500'
              }`}
            >
              <img
                src={image.image_url}
                alt={image.alt_text || `${productName} thumbnail ${index + 1}`}
                className="absolute inset-0 w-full h-full object-cover"
              />
            </button>
          ))}
        </div>
      )}

      {/* Zoom Modal */}
      {isZoomed && (
        <div
          className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center p-4"
          onClick={() => setIsZoomed(false)}
        >
          <button
            className="absolute top-4 right-4 text-white hover:text-gold-400 transition-colors"
            onClick={() => setIsZoomed(false)}
          >
            <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
          <div className="relative w-full h-full max-w-4xl max-h-[90vh] flex items-center justify-center">
            <img
              src={currentImage.image_url}
              alt={currentImage.alt_text || productName}
              className="max-w-full max-h-full object-contain"
            />
          </div>

          {/* Navigation arrows */}
          {sortedImages.length > 1 && (
            <>
              <button
                className="absolute left-4 top-1/2 -translate-y-1/2 p-2 bg-slate-800/80 rounded-full text-white hover:bg-slate-700 transition-colors"
                onClick={(e) => {
                  e.stopPropagation();
                  setSelectedIndex((prev) => (prev === 0 ? sortedImages.length - 1 : prev - 1));
                }}
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </button>
              <button
                className="absolute right-4 top-1/2 -translate-y-1/2 p-2 bg-slate-800/80 rounded-full text-white hover:bg-slate-700 transition-colors"
                onClick={(e) => {
                  e.stopPropagation();
                  setSelectedIndex((prev) => (prev === sortedImages.length - 1 ? 0 : prev + 1));
                }}
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </button>
            </>
          )}
        </div>
      )}
    </div>
  );
}
