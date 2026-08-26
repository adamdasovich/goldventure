"use client";

import { useAssistant } from "@/contexts/AssistantContext";

interface AskAssistantButtonProps {
  /** "chip" for the static nav strip, "nav" for the app header. */
  variant?: "nav" | "chip";
  className?: string;
}

/**
 * Opens the site-wide assistant. Small enough to drop into any header,
 * including the server-rendered SiteNav on the report and guide routes —
 * this is the only client boundary those pages take on.
 */
export default function AskAssistantButton({
  variant = "nav",
  className = "",
}: AskAssistantButtonProps) {
  const { open } = useAssistant();

  const base =
    "inline-flex items-center gap-1.5 whitespace-nowrap font-medium transition-colors";

  const styles =
    variant === "chip"
      ? "px-4 py-2.5 min-h-11 rounded-full border border-gold-500/50 bg-gold-500/10 text-gold-300 text-sm hover:bg-gold-500/20"
      : "px-3 py-1.5 min-h-11 lg:min-h-0 rounded-lg border border-gold-500/50 bg-gold-500/10 text-gold-300 text-sm hover:bg-gold-500/20";

  return (
    <button
      type="button"
      onClick={() => open()}
      className={`${base} ${styles} ${className}`}
    >
      <svg
        className="h-4 w-4 shrink-0"
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
      Ask AI
    </button>
  );
}
