"use client";

import CompanyPicker, {
  type PickableCompany,
} from "@/components/ui/CompanyPicker";

interface CompanyMultiPickerProps {
  companies: PickableCompany[];
  /** Currently chosen companies, in display order. */
  selected: PickableCompany[];
  onChange: (next: PickableCompany[]) => void;
  label?: string;
  max?: number;
  disabled?: boolean;
}

/**
 * Build a set of companies without typing database IDs.
 *
 * Portfolio X-Ray and Peer Comparison both shipped a text box reading
 * "e.g. 1, 2, 3, 15, 42" — primary keys, which a user has no way to know and no
 * way to discover from the page. This is the replacement: pick by name, see
 * what you picked, remove individually.
 */
export default function CompanyMultiPicker({
  companies,
  selected,
  onChange,
  label = "Companies",
  max = 10,
  disabled = false,
}: CompanyMultiPickerProps) {
  const selectedIds = new Set(selected.map((c) => c.id));
  const remaining = companies.filter((c) => !selectedIds.has(c.id));
  const full = selected.length >= max;

  return (
    <div>
      <div className="flex items-baseline justify-between mb-1">
        <label className="block text-xs text-slate-400">{label}</label>
        <span className="text-xs text-slate-500">
          {selected.length} of {max}
        </span>
      </div>

      <CompanyPicker
        companies={remaining}
        value={null}
        onChange={(company) => {
          if (company && !full) onChange([...selected, company]);
        }}
        label=""
        placeholder={
          full
            ? `Maximum of ${max} selected`
            : "Add a company by name or ticker…"
        }
        disabled={disabled || full}
      />

      {selected.length > 0 && (
        <ul className="flex flex-wrap gap-2 mt-3">
          {selected.map((c) => (
            <li key={c.id}>
              <span className="inline-flex items-center gap-2 bg-slate-800/70 border border-slate-700 rounded-full pl-3 pr-2 py-1 text-xs text-slate-200">
                {c.name}
                {c.ticker && <span className="text-slate-500">{c.ticker}</span>}
                <button
                  type="button"
                  onClick={() =>
                    onChange(selected.filter((s) => s.id !== c.id))
                  }
                  aria-label={`Remove ${c.name}`}
                  className="text-slate-500 hover:text-red-400 focus:outline-none focus-visible:text-red-400"
                >
                  ✕
                </button>
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
