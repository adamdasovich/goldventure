"use client";

const TESTIMONIALS = [
  {
    quote:
      "Claude helped me spot an undervalued lithium play before anyone else picked up on the drill results. Complete game-changer for my portfolio.",
    name: "Michael T.",
    role: "Retail Investor",
    verified: true,
  },
  {
    quote:
      "I used to spend hours digging through SEDAR filings. Now I just ask the AI assistant and get sourced answers in seconds. Saves me 10+ hours a week.",
    name: "Sarah K.",
    role: "Mining Analyst",
    verified: true,
  },
  {
    quote:
      "The financing tracker caught a private placement I would have completely missed. Subscribed to the round and it's already up 40%.",
    name: "David R.",
    role: "Accredited Investor",
    verified: true,
  },
];

export default function Testimonials() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {TESTIMONIALS.map((t, i) => (
        <div
          key={i}
          className="glass-card rounded-xl p-5 flex flex-col justify-between"
        >
          {/* Quote */}
          <div>
            <svg
              className="w-6 h-6 text-gold-500/40 mb-2"
              fill="currentColor"
              viewBox="0 0 24 24"
            >
              <path d="M14.017 21v-7.391c0-5.704 3.731-9.57 8.983-10.609l.995 2.151c-2.432.917-3.995 3.638-3.995 5.849h4v10H14.017zm-14.017 0v-7.391c0-5.704 3.748-9.57 9-10.609l.996 2.151c-2.433.917-3.996 3.638-3.996 5.849h3.983v10H0z" />
            </svg>
            <p className="text-sm text-slate-300 leading-relaxed italic">
              &ldquo;{t.quote}&rdquo;
            </p>
          </div>

          {/* Attribution */}
          <div className="flex items-center gap-3 mt-4 pt-3 border-t border-slate-700/50">
            {/* Avatar placeholder */}
            <div className="w-8 h-8 rounded-full bg-gold-500/15 border border-gold-500/30 flex items-center justify-center flex-shrink-0">
              <span className="text-xs font-bold text-gold-400">
                {t.name.charAt(0)}
              </span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-slate-200">{t.name}</p>
              <p className="text-xs text-slate-500">{t.role}</p>
            </div>
            {t.verified && (
              <span className="flex items-center gap-1 text-[10px] text-emerald-400/80 flex-shrink-0">
                <svg
                  className="w-3 h-3"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                    clipRule="evenodd"
                  />
                </svg>
                Verified
              </span>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
