"use client";

import { useState } from "react";
import Link from "next/link";
import { Badge } from "@/components/ui/Badge";
import UpgradeModal from "@/components/UpgradeModal";
import { useAuth } from "@/contexts/AuthContext";
import {
  AVAILABLE_COUNT,
  FREE_TOOL_SLUGS,
  TOOLS,
  TOOL_GROUPS,
  type Tool,
} from "./tools";

/**
 * The interactive half of /investor-tools.
 *
 * Split out of page.tsx so the page itself can stay a server component: the
 * headings, prose and JSON-LD now render into the HTML for every visitor,
 * including crawlers, while the tier checks that genuinely need `useAuth`
 * stay client-side. Previously the whole page was "use client" and carried no
 * headings at all.
 */
export default function ToolsGrid() {
  const { subscription } = useAuth();
  const [showUpgrade, setShowUpgrade] = useState(false);
  const tier = subscription?.effective_tier || "explorer";
  // 'miner' still appears on legacy rows; the backend resolves it to
  // prospector, and it means the same thing here.
  const hasFullAccess = tier === "prospector" || tier === "miner";

  const isToolFree = (slug: string) => FREE_TOOL_SLUGS.includes(slug);

  /** True when this tool needs a plan the user doesn't have. Since Miner was
   *  retired there is only one paid tier, so this is a boolean, not a ladder. */
  const isToolLocked = (slug: string) => !isToolFree(slug) && !hasFullAccess;

  const handleToolClick = (e: React.MouseEvent, tool: Tool) => {
    if (!tool.available) return;
    if (isToolLocked(tool.slug)) {
      e.preventDefault();
      setShowUpgrade(true);
    }
  };

  const renderCard = (tool: Tool) => {
    const isLocked = tool.available && isToolLocked(tool.slug);

    return (
      <Link
        key={tool.slug}
        href={tool.available ? tool.href : "#"}
        onClick={(e) => handleToolClick(e, tool)}
        className={`group block ${!tool.available ? "pointer-events-none opacity-60" : ""}`}
      >
        <div
          className={`glass-card rounded-xl p-5 h-full flex flex-col transition-all hover:border-gold-400/30 ${isLocked ? "relative" : ""}`}
        >
          {isLocked && (
            <div className="absolute top-3 right-3">
              <svg
                className="w-4 h-4 text-slate-500"
                fill="currentColor"
                viewBox="0 0 20 20"
                aria-label="Requires an upgrade"
                role="img"
              >
                <path
                  fillRule="evenodd"
                  d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
          )}

          <div className="flex items-start justify-between mb-3">
            <div className="w-10 h-10 rounded-lg flex items-center justify-center bg-gold-500/15 border border-gold-500/30 group-hover:scale-110 transition-transform">
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
                  d={tool.icon}
                />
              </svg>
            </div>
            <Badge
              variant={tool.available ? "gold" : "slate"}
              className="text-[10px]"
            >
              {tool.badge}
            </Badge>
          </div>

          {/* h4: the group heading above this grid is the h3, and the page
              section heading is the h2. Cards must not outrank their section. */}
          <h4 className="text-lg font-semibold text-slate-200 group-hover:text-gold-400 transition-colors mb-2">
            {tool.title}
          </h4>
          <p className="text-sm text-slate-400 leading-relaxed flex-1">
            {tool.description}
          </p>

          {tool.available && (
            <div className="mt-4 pt-3 border-t border-slate-700/50">
              <span className="text-sm text-gold-400 font-medium group-hover:underline">
                {isLocked ? "Upgrade to Access →" : "Launch Tool →"}
              </span>
            </div>
          )}
        </div>
      </Link>
    );
  };

  const comingSoon = TOOLS.filter((t) => !t.available);

  return (
    <>
      {showUpgrade && (
        <UpgradeModal
          onClose={() => setShowUpgrade(false)}
          feature={`All ${AVAILABLE_COUNT} Investor Tools`}
        />
      )}

      <div className="flex flex-col gap-14">
        {TOOL_GROUPS.map((group) => {
          const groupTools = TOOLS.filter(
            (t) => t.group === group.id && t.available,
          );
          if (groupTools.length === 0) return null;

          return (
            <section key={group.id} id={group.id} className="scroll-mt-20">
              <h3 className="text-2xl font-bold text-gold-400 mb-3">
                {group.heading}
              </h3>
              <p className="text-slate-300 leading-relaxed max-w-3xl mb-6">
                {group.blurb}
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
                {groupTools.map(renderCard)}
              </div>
            </section>
          );
        })}

        {comingSoon.length > 0 && (
          <section id="coming-soon" className="scroll-mt-20">
            <h3 className="text-2xl font-bold text-slate-400 mb-3">
              In development
            </h3>
            <p className="text-slate-400 leading-relaxed max-w-3xl mb-6">
              Listed here so you know what is coming rather than what already
              works. These are not available yet.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
              {comingSoon.map(renderCard)}
            </div>
          </section>
        )}
      </div>
    </>
  );
}
