"use client";

import { useEffect, useId, useMemo, useRef, useState } from "react";

export interface PickableCompany {
  id: number;
  name: string;
  ticker?: string;
  exchange?: string;
}

interface CompanyPickerProps {
  /** Companies to choose from — usually a tool's `available_companies`. */
  companies: PickableCompany[];
  /** Currently selected company id, or null. */
  value: number | null;
  onChange: (company: PickableCompany | null) => void;
  label?: string;
  placeholder?: string;
  /** Shown under the field when `companies` is empty. */
  emptyHint?: string;
  disabled?: boolean;
  className?: string;
}

/**
 * Typeahead selector for a company.
 *
 * Replaces the free-text boxes the tools shipped with. Typing a name that the
 * backend resolves loosely (or not at all) was the single biggest source of
 * dead-end results: several tools already fetch an `available_companies` list
 * describing exactly what they can answer for, and then asked the user to guess
 * at it anyway. Selection is constrained to that list, so an empty result now
 * means "no data for this company" rather than "you typed it differently".
 *
 * Keyboard: ArrowUp/ArrowDown to move, Enter to pick, Escape to dismiss.
 */
export default function CompanyPicker({
  companies,
  value,
  onChange,
  label = "Company",
  placeholder = "Search by name or ticker…",
  emptyHint,
  disabled = false,
  className = "",
}: CompanyPickerProps) {
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const [highlight, setHighlight] = useState(0);
  const wrapRef = useRef<HTMLDivElement>(null);
  const listboxId = useId();

  const selected = useMemo(
    () => companies.find((c) => c.id === value) ?? null,
    [companies, value],
  );

  const matches = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return companies.slice(0, 50);
    return companies
      .filter(
        (c) =>
          c.name.toLowerCase().includes(q) ||
          (c.ticker || "").toLowerCase().includes(q),
      )
      .slice(0, 50);
  }, [companies, query]);

  // Close when focus leaves the component entirely.
  useEffect(() => {
    if (!open) return;
    const onPointerDown = (e: MouseEvent) => {
      if (!wrapRef.current?.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onPointerDown);
    return () => document.removeEventListener("mousedown", onPointerDown);
  }, [open]);

  // Keep the highlight in range as the match list shrinks while typing.
  useEffect(() => {
    setHighlight((h) => Math.min(h, Math.max(0, matches.length - 1)));
  }, [matches.length]);

  const choose = (company: PickableCompany) => {
    onChange(company);
    setQuery("");
    setOpen(false);
  };

  const onKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault();
      if (!open) {
        setOpen(true);
        return;
      }
      setHighlight((h) => {
        const next = e.key === "ArrowDown" ? h + 1 : h - 1;
        if (next < 0) return matches.length - 1;
        if (next >= matches.length) return 0;
        return next;
      });
      return;
    }
    if (e.key === "Enter" && open && matches[highlight]) {
      e.preventDefault();
      choose(matches[highlight]);
      return;
    }
    if (e.key === "Escape") {
      setOpen(false);
    }
  };

  return (
    <div ref={wrapRef} className={`relative ${className}`}>
      {label && (
        <label className="block text-xs text-slate-400 mb-1">{label}</label>
      )}

      {selected ? (
        <div className="flex items-center gap-2 bg-slate-800/60 border border-slate-700 rounded-lg px-3 py-2">
          <span className="text-sm text-slate-200 truncate">
            {selected.name}
          </span>
          {selected.ticker && (
            <span className="text-xs text-slate-500 shrink-0">
              {selected.ticker}
            </span>
          )}
          <button
            type="button"
            onClick={() => {
              onChange(null);
              setQuery("");
              setOpen(true);
            }}
            disabled={disabled}
            aria-label={`Clear ${selected.name}`}
            className="ml-auto text-slate-500 hover:text-gold-400 focus:outline-none focus-visible:text-gold-400 shrink-0"
          >
            ✕
          </button>
        </div>
      ) : (
        <input
          type="text"
          role="combobox"
          aria-expanded={open}
          aria-controls={listboxId}
          aria-autocomplete="list"
          value={query}
          disabled={disabled || companies.length === 0}
          placeholder={
            companies.length === 0 ? "No companies available" : placeholder
          }
          onChange={(e) => {
            setQuery(e.target.value);
            setOpen(true);
          }}
          onFocus={() => setOpen(true)}
          onKeyDown={onKeyDown}
          className="w-full bg-slate-800/60 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-gold-500/50 disabled:opacity-50"
        />
      )}

      {emptyHint && companies.length === 0 && (
        <p className="mt-1 text-xs text-slate-500">{emptyHint}</p>
      )}

      {open && !selected && matches.length > 0 && (
        <ul
          id={listboxId}
          role="listbox"
          className="absolute z-30 mt-1 w-full max-h-64 overflow-y-auto rounded-lg border border-slate-700 bg-slate-900 shadow-xl"
        >
          {matches.map((c, i) => (
            <li key={c.id} role="option" aria-selected={i === highlight}>
              <button
                type="button"
                onMouseEnter={() => setHighlight(i)}
                onClick={() => choose(c)}
                className={`w-full text-left px-3 py-2 text-sm flex items-baseline gap-2 ${
                  i === highlight
                    ? "bg-slate-800 text-gold-400"
                    : "text-slate-300"
                }`}
              >
                <span className="truncate">{c.name}</span>
                {c.ticker && (
                  <span className="ml-auto text-xs text-slate-500 shrink-0">
                    {c.ticker}
                    {c.exchange ? ` · ${c.exchange.toUpperCase()}` : ""}
                  </span>
                )}
              </button>
            </li>
          ))}
        </ul>
      )}

      {open && !selected && query.trim() && matches.length === 0 && (
        <div className="absolute z-30 mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-500">
          No match for “{query.trim()}”
        </div>
      )}
    </div>
  );
}
