'use client';

import { usePathname } from 'next/navigation';
import { useEffect } from 'react';

/**
 * Client-side canonical URL handler
 * Ensures canonical URLs are lowercase and without trailing slashes
 */
export default function CanonicalUrl() {
  const pathname = usePathname();

  useEffect(() => {
    // Normalize the pathname: lowercase and remove trailing slash
    const normalizedPath = pathname.toLowerCase().replace(/\/$/, '') || '/';
    const canonicalUrl = `https://juniorminingintelligence.com${normalizedPath}`;

    // Check if canonical link already exists
    let canonicalLink = document.querySelector('link[rel="canonical"]');

    if (!canonicalLink) {
      // Create canonical link if it doesn't exist
      canonicalLink = document.createElement('link');
      canonicalLink.setAttribute('rel', 'canonical');
      document.head.appendChild(canonicalLink);
    }

    // Update the canonical URL
    canonicalLink.setAttribute('href', canonicalUrl);
  }, [pathname]);

  return null;
}
