"use client";

import React, { useCallback, useEffect, useRef } from "react";

const SIZE_CLASSES = {
  sm: "max-w-sm",
  md: "max-w-md",
  lg: "max-w-lg",
  xl: "max-w-2xl",
  "2xl": "max-w-4xl",
} as const;

const FOCUSABLE = [
  "a[href]",
  "button:not([disabled])",
  'input:not([disabled]):not([type="hidden"])',
  "select:not([disabled])",
  "textarea:not([disabled])",
  '[tabindex]:not([tabindex="-1"])',
].join(",");

/* Nested overlays (the upgrade modal opened from the cart sidebar) must not
   release the lock when only the inner one closes, so the lock is counted
   rather than toggled. */
let lockCount = 0;
let previousOverflow = "";

function lockBodyScroll() {
  if (lockCount === 0) {
    previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
  }
  lockCount += 1;
}

function unlockBodyScroll() {
  lockCount = Math.max(0, lockCount - 1);
  if (lockCount === 0) {
    document.body.style.overflow = previousOverflow;
  }
}

export interface ModalProps {
  onClose: () => void;
  children: React.ReactNode;
  /** id of the heading inside the panel, for the accessible name. */
  labelledBy?: string;
  size?: keyof typeof SIZE_CLASSES;
  /** false for flows that must not be dismissed by backdrop click or Esc. */
  dismissible?: boolean;
  className?: string;
}

/**
 * Overlay primitive for every dialog in the app.
 *
 * The height cap is the point of it: an overlay that only centres its child
 * pushes the overflow of a tall panel *above* the scroll origin, where it
 * cannot be reached by any means. Capping the panel to the viewport and
 * scrolling inside it keeps the whole dialog reachable on short screens and
 * with the software keyboard open. `dvh` (not `vh`) so the cap tracks the
 * iOS URL bar as it collapses.
 */
export function Modal({
  onClose,
  children,
  labelledBy,
  size = "md",
  dismissible = true,
  className = "",
}: ModalProps) {
  const panelRef = useRef<HTMLDivElement>(null);
  const restoreFocusRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    restoreFocusRef.current = document.activeElement as HTMLElement | null;
    lockBodyScroll();

    return () => {
      unlockBodyScroll();
      restoreFocusRef.current?.focus?.();
    };
  }, []);

  // Move focus into the panel so the dialog reads correctly and Esc lands here.
  useEffect(() => {
    const panel = panelRef.current;
    if (!panel) return;
    const first = panel.querySelector<HTMLElement>(FOCUSABLE);
    (first ?? panel).focus();
  }, []);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Escape" && dismissible) {
        e.stopPropagation();
        onClose();
        return;
      }
      if (e.key !== "Tab") return;

      const panel = panelRef.current;
      if (!panel) return;

      const items = Array.from(
        panel.querySelectorAll<HTMLElement>(FOCUSABLE),
      ).filter((el) => el.offsetParent !== null);
      if (items.length === 0) return;

      const first = items[0];
      const last = items[items.length - 1];

      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    },
    [dismissible, onClose],
  );

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
      /* mousedown, not click: otherwise selecting text inside the panel and
         releasing over the backdrop closes the dialog. */
      onMouseDown={(e) => {
        if (dismissible && e.target === e.currentTarget) onClose();
      }}
      onKeyDown={handleKeyDown}
    >
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={labelledBy}
        tabIndex={-1}
        className={`w-full ${SIZE_CLASSES[size]} max-h-[calc(100dvh-2rem)] overflow-y-auto overscroll-contain outline-none ${className}`}
      >
        {children}
      </div>
    </div>
  );
}

Modal.displayName = "Modal";
