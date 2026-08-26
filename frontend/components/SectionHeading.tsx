import type { ReactNode } from "react";

interface SectionHeadingProps {
  /** Small uppercase label above the title. Replaces the old gold Badge. */
  eyebrow?: string;
  title: string;
  /** One line. If it needs two, it is doing the section's job for it. */
  description?: string;
  /** Right-hand slot on desktop — a "view all" link, a count, a control. */
  action?: ReactNode;
  align?: "left" | "center";
  className?: string;
}

/**
 * One heading treatment for every homepage section.
 *
 * The sections each had a gold Badge, a 30-36px gradient h2 and a two-line
 * paragraph, in their own spacing — roughly 200px of furniture per section
 * before any content, five times over. This is the same information in about
 * 90px, and identical everywhere so the page reads as one design.
 */
export default function SectionHeading({
  eyebrow,
  title,
  description,
  action,
  align = "center",
  className = "",
}: SectionHeadingProps) {
  const centred = align === "center";

  return (
    <div
      className={`mb-6 sm:mb-8 ${
        centred
          ? "text-center"
          : "flex flex-wrap items-end justify-between gap-3"
      } ${className}`}
    >
      <div className={centred ? "" : "min-w-0"}>
        {eyebrow && (
          <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-500 mb-2">
            {eyebrow}
          </p>
        )}
        <h2 className="font-display text-xl sm:text-2xl lg:text-[1.75rem] font-bold tracking-tight text-slate-50 text-balance">
          {title}
        </h2>
        {description && (
          <p
            className={`mt-2 text-sm sm:text-base text-slate-400 ${
              centred ? "max-w-xl mx-auto" : "max-w-xl"
            }`}
          >
            {description}
          </p>
        )}
      </div>
      {action && <div className="shrink-0">{action}</div>}
    </div>
  );
}
