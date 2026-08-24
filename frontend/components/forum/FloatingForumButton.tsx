"use client";

import { useEffect, useState } from "react";

interface FloatingForumButtonProps {
  /** Called when the user clicks the FAB. Parent decides what jumping means
   *  (tab switch, scrollIntoView, etc). */
  onClick: () => void;
  /** Hard-hide the FAB regardless of scroll position. Use this when the user
   *  is already viewing the forum, so we don't show "jump to the thing you're
   *  already looking at." */
  hidden?: boolean;
  /** Scroll threshold (px) before the FAB fades in. Defaults to 600 so it
   *  only appears once the user is past the company hero, leaving the header
   *  pill as the primary entry point above the fold. */
  scrollThreshold?: number;
}

/**
 * Persistent chat-style FAB that surfaces the company forum from anywhere on
 * the company page. Fades in once the user has scrolled past the hero and
 * stays out of the way otherwise.
 */
export function FloatingForumButton({
  onClick,
  hidden = false,
  scrollThreshold = 600,
}: FloatingForumButtonProps) {
  const [scrolledPast, setScrolledPast] = useState(false);

  useEffect(() => {
    const onScroll = () => {
      setScrolledPast(window.scrollY > scrollThreshold);
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, [scrollThreshold]);

  const visible = scrolledPast && !hidden;

  return (
    <button
      type="button"
      onClick={onClick}
      aria-label="Open community forum"
      className={`fixed left-4 bottom-[calc(6rem+env(safe-area-inset-bottom))] sm:left-6 sm:bottom-[calc(1.5rem+env(safe-area-inset-bottom))] z-40 flex items-center gap-2 rounded-full bg-gradient-to-br from-slate-700 to-slate-800 border border-gold-500/40 px-5 py-3 text-sm font-semibold text-gold-300 shadow-lg shadow-slate-900/60 hover:border-gold-400 hover:text-gold-200 hover:scale-105 transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-gold-300 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900 ${
        visible
          ? "opacity-100 translate-y-0 pointer-events-auto"
          : "opacity-0 translate-y-4 pointer-events-none"
      } duration-300 motion-reduce:transition-none`}
    >
      <span
        className="w-2 h-2 rounded-full bg-green-300 motion-safe:animate-pulse"
        aria-hidden="true"
      />
      <svg
        className="w-5 h-5"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2.5}
          d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
        />
      </svg>
      <span className="hidden sm:inline">Discussion</span>
    </button>
  );
}
