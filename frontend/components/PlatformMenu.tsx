"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";

export interface PlatformLink {
  title: string;
  href: string;
  group: string;
  badge?: string;
}

/**
 * One dropdown instead of a wall of options.
 *
 * These were eleven pill-shaped links wrapping to three ragged rows. The
 * commodity filter on /companies collapses far more choices than this into a
 * single labelled control, and that is the pattern this follows — same square
 * button, same grouped panel.
 */
export default function PlatformMenu({ links }: { links: PlatformLink[] }) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const onDown = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node))
        setOpen(false);
    };
    document.addEventListener("mousedown", onDown);
    return () => document.removeEventListener("mousedown", onDown);
  }, []);

  const groups = links.reduce<Record<string, PlatformLink[]>>((acc, l) => {
    (acc[l.group] ||= []).push(l);
    return acc;
  }, {});

  return (
    <div className="relative inline-block text-left" ref={ref}>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        aria-haspopup="true"
        className="flex items-center gap-2 px-4 py-3 min-h-11 bg-slate-800/50 border border-slate-700 rounded-lg text-white transition-colors hover:border-gold-500/40"
      >
        <svg
          className="w-5 h-5 text-gold-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M4 6h16M4 12h16M4 18h16"
          />
        </svg>
        <span>Explore the platform</span>
        <svg
          className={`w-4 h-4 transition-transform ${open ? "rotate-180" : ""}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>

      {open && (
        <div className="absolute top-full left-1/2 -translate-x-1/2 mt-2 w-80 max-h-96 overflow-y-auto overscroll-contain bg-slate-800 border border-slate-700 rounded-lg shadow-2xl z-30 text-left">
          {Object.entries(groups).map(([group, items]) => (
            <div key={group} className="p-2">
              <div className="text-xs font-semibold text-gold-400 uppercase tracking-wide px-2 py-1">
                {group}
              </div>
              {items.map((item) => (
                <Link
                  key={item.href + item.title}
                  href={item.href}
                  onClick={() => setOpen(false)}
                  className="flex items-center justify-between gap-2 px-2 py-2 min-h-11 rounded text-sm text-slate-300 transition-colors hover:bg-slate-700/60 hover:text-gold-400"
                >
                  {item.title}
                  {item.badge && (
                    <span className="shrink-0 text-[10px] font-semibold uppercase tracking-wide text-gold-400">
                      {item.badge}
                    </span>
                  )}
                </Link>
              ))}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
