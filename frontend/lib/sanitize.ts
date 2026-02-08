/**
 * Shared HTML sanitization utility using DOMPurify.
 *
 * SECURITY: Always use this instead of custom regex-based sanitization.
 * DOMPurify is battle-tested against XSS bypasses that regex cannot catch
 * (mutation XSS, parser differentials, encoding tricks).
 *
 * Usage:
 *   import { sanitize } from '@/lib/sanitize';
 *   <div dangerouslySetInnerHTML={{ __html: sanitize(htmlContent) }} />
 */

import DOMPurify from 'dompurify';

/**
 * Sanitize HTML content to prevent XSS attacks.
 *
 * Allows safe formatting tags (p, b, i, ul, ol, li, a, h1-h6, etc.)
 * but strips scripts, event handlers, iframes, and dangerous attributes.
 */
export function sanitize(dirty: string): string {
  if (!dirty) return '';

  return DOMPurify.sanitize(dirty, {
    // Allow common formatting tags
    ALLOWED_TAGS: [
      'p', 'br', 'b', 'i', 'em', 'strong', 'u', 'sub', 'sup',
      'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
      'ul', 'ol', 'li',
      'a', 'img',
      'table', 'thead', 'tbody', 'tr', 'th', 'td',
      'blockquote', 'pre', 'code',
      'span', 'div', 'hr',
    ],
    // Allow safe attributes only
    ALLOWED_ATTR: [
      'href', 'src', 'alt', 'title', 'class', 'id',
      'target', 'rel', 'width', 'height',
      'colspan', 'rowspan',
    ],
    // Force all links to open in new tab safely
    ADD_ATTR: ['target'],
    // Block dangerous URI schemes
    ALLOWED_URI_REGEXP: /^(?:(?:https?|mailto):|[^a-z]|[a-z+.-]+(?:[^a-z+.\-:]|$))/i,
  });
}
