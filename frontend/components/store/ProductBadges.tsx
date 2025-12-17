'use client';

import React from 'react';
import type { ProductBadge } from '@/types/api';

interface ProductBadgesProps {
  badges: ProductBadge[];
  className?: string;
}

const badgeConfig: Record<ProductBadge, { label: string; className: string; icon: string }> = {
  rare: {
    label: 'Rare',
    className: 'bg-purple-500/20 text-purple-300 border-purple-500/40',
    icon: '💎',
  },
  limited_edition: {
    label: 'Limited Edition',
    className: 'bg-gold-500/20 text-gold-300 border-gold-500/40',
    icon: '⭐',
  },
  community_favorite: {
    label: 'Community Favorite',
    className: 'bg-copper-500/20 text-copper-300 border-copper-500/40',
    icon: '❤️',
  },
  new_arrival: {
    label: 'New',
    className: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40',
    icon: '✨',
  },
  instant_download: {
    label: 'Instant Download',
    className: 'bg-blue-500/20 text-blue-300 border-blue-500/40',
    icon: '⬇️',
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
            <span>{config.icon}</span>
            <span>{config.label}</span>
          </span>
        );
      })}
    </div>
  );
}
