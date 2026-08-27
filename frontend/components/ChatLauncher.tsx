"use client";

import { EXAMPLE_PROMPTS } from "./ChatInterface";

interface ChatLauncherProps {
  /** Called with a prompt when a suggestion is tapped, otherwise with nothing. */
  onOpen: (prompt?: string) => void;
  className?: string;
}

/**
 * The resting state of the assistant on the homepage: one ask-bar instead of a
 * 550px panel sitting open on a page nobody has asked anything on yet.
 *
 * It opens the assistant in a modal rather than expanding in place. The
 * assistant is the most valuable thing on the site and it was competing with
 * five other sections for attention; in a modal it gets the whole screen.
 */
export default function ChatLauncher({
  onOpen,
  className = "",
}: ChatLauncherProps) {
  return (
    <div className={`max-w-3xl mx-auto ${className}`}>
      <button
        type="button"
        onClick={() => onOpen()}
        className="group flex w-full items-center gap-3 rounded-lg border border-gold-500/40 bg-gold-500/5 px-4 py-4 text-left transition-colors hover:border-gold-500/70 hover:bg-gold-500/10"
      >
        <svg
          className="h-5 w-5 shrink-0 text-gold-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
          />
        </svg>
        <span className="flex-1 truncate text-slate-300 group-hover:text-slate-200">
          Ask about any company&hellip;
        </span>
        <span className="shrink-0 rounded-lg bg-gold-500 px-3 py-1.5 text-xs font-semibold uppercase tracking-wide text-slate-900">
          Ask
        </span>
      </button>

      <div className="mt-3 flex gap-2 overflow-x-auto scrollbar-none -mx-4 px-4 sm:mx-0 sm:px-0 sm:flex-wrap sm:justify-center">
        {EXAMPLE_PROMPTS.slice(0, 4).map((example) => (
          <button
            key={example.label}
            type="button"
            title={example.prompt}
            onClick={() => onOpen(example.prompt)}
            className="shrink-0 whitespace-nowrap rounded-lg border border-slate-700 px-4 py-2.5 min-h-11 inline-flex items-center text-sm text-slate-400 transition-colors hover:border-gold-500/40 hover:text-gold-400"
          >
            {example.label}
          </button>
        ))}
      </div>
    </div>
  );
}
