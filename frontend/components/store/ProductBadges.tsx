'use client';

import React from 'react';
import type { ProductBadge } from '@/types/api';

interface ProductBadgesProps {
  badges: ProductBadge[];
  className?: string;
}

// SVG Icon Components
const DiamondIcon = () => (
  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
  </svg>
);

const StarIcon = () => (
  <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
  </svg>
);

const HeartIcon = () => (
  <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
    <path fillRule="evenodd" d="M3.172 5.172a4 4 0 015.656 0L10 6.343l1.172-1.171a4 4 0 115.656 5.656L10 17.657l-6.828-6.829a4 4 0 010-5.656z" clipRule="evenodd" />
  </svg>
);

const SparkleIcon = () => (
  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
  </svg>
);

const DownloadIcon = () => (
  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
  </svg>
);

const badgeConfig: Record<ProductBadge, { label: string; className: string; icon: React.ReactNode }> = {
  rare: {
    label: 'Rare',
    className: 'bg-gold-500/20 text-gold-300 border-gold-500/40',
    icon: <DiamondIcon />,
  },
  limited_edition: {
    label: 'Limited Edition',
    className: 'bg-gold-500/20 text-gold-300 border-gold-500/40',
    icon: <StarIcon />,
  },
  community_favorite: {
    label: 'Community Favorite',
    className: 'bg-gold-500/20 text-gold-300 border-gold-500/40',
    icon: <HeartIcon />,
  },
  new_arrival: {
    label: 'New',
    className: 'bg-gold-500/20 text-gold-300 border-gold-500/40',
    icon: <SparkleIcon />,
  },
  instant_download: {
    label: 'Instant Download',
    className: 'bg-gold-500/20 text-gold-300 border-gold-500/40',
    icon: <DownloadIcon />,
  },
};

export function ProductBadges({ badges, className = '' }: ProductBadgesProps) {
  if (!badges || badges.length === 0) return null;

  return (
    <div className={`flex flex-wrap gap-1.5 ${className}`}>
      {badges.map((badge) => {
        const config = badgeConfig[badge];
        if (!config) return null;

        return (
          <span
            key={badge}
            className={`inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium rounded border ${config.className}`}
          >
            {config.icon}
            <span>{config.label}</span>
          </span>
        );
      })}
    </div>
  );
}
