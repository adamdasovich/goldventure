"use client";

import { useEffect, useState } from "react";

interface FloatingForumButtonProps {
  /** ID of the forum section element to scroll to and observe. */
  targetId?: string;
}

/**
 * Persistent chat-style FAB that scrolls to the company's community forum.
 *
 * Auto-hides while the forum section is in view (no point showing a "jump to
 * the thing you're already looking at" button) and while the user is at the
 * top of the page where the header pill is already visible.
 */
export function FloatingForumButton({
  targetId = "community-forum",
}: FloatingForumButtonProps) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const target = document.getElementById(targetId);
    if (!target) return;

    let forumInView = false;
    let scrolledPastHero = false;

    const updateVisibility = () => {
      // Only show once the user has scrolled meaningfully past the header
      // (where the discovery pill lives) AND the forum itself is not on
      // screen yet. Otherwise we're just being noisy.
      setVisible(scrolledPastHero && !forumInView);
    };

    const observer = new IntersectionObserver(
      ([entry]) => {
        forumInView = entry.isIntersecting;
        updateVisibility();
      },
      { rootMargin: "-80px 0px -80px 0px" },
    );
    observer.observe(target);

    const onScroll = () => {
      scrolledPastHero = window.scrollY > 600;
      updateVisibility();
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });

    return () => {
      observer.disconnect();
      window.removeEventListener("scroll", onScroll);
    };
  }, [targetId]);

  const handleClick = () => {
    const target = document.getElementById(targetId);
    if (target) {
      target.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

  return (
    <button
      type="button"
      onClick={handleClick}
      aria-label="Open community forum"
      className={`fixed bottom-6 left-6 z-40 flex items-center gap-2 rounded-full bg-gradient-to-br from-slate-700 to-slate-800 border border-gold-500/40 px-5 py-3 text-sm font-semibold text-gold-300 shadow-lg shadow-slate-900/60 hover:border-gold-400 hover:text-gold-200 hover:scale-105 transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-gold-300 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900 ${
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
