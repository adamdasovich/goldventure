"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { Card, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import SiteHeader from "@/components/SiteHeader";
import { LoginModal, RegisterModal } from "@/components/auth";
import { Modal } from "@/components/ui/Modal";
import { useAuth } from "@/contexts/AuthContext";
import { companyHref } from "@/lib/companyUrl";

interface OpenFinancing {
  id: number;
  company_id: number;
  company_slug?: string | null;
  company_name: string;
  company_ticker: string;
  company_exchange: string;
  financing_type: string;
  financing_type_display: string;
  status: string | null;
  amount_raised_usd: string | null;
  price_per_share: string | null;
  shares_issued: number | null;
  has_warrants: boolean | null;
  warrant_strike_price: string | null;
  warrant_expiry_date: string | null;
  announced_date: string | null;
  closing_date: string | null;
  lead_agent: string | null;
  use_of_proceeds: string | null;
  press_release_url: string | null;
  notes: string | null;
  is_locked: boolean;
}

export interface OpenFinancingsResponse {
  count: number;
  total_count: number;
  locked_count: number;
  user_tier: string;
  is_paid: boolean;
  preview_count: number;
  results: OpenFinancing[];
  financing_types: { value: string; label: string }[];
}

interface OpenFinancingsClientProps {
  initialData?: OpenFinancingsResponse | null;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

const STATUS_OPTIONS = [
  { value: "announced", label: "Announced" },
  { value: "closing", label: "Closing" },
  { value: "closed", label: "Closed" },
  { value: "cancelled", label: "Cancelled" },
];

type FinancingForm = {
  financing_type: string;
  status: string;
  amount_raised_usd: string;
  price_per_share: string;
  shares_issued: string;
  has_warrants: boolean;
  warrant_strike_price: string;
  warrant_expiry_date: string;
  announced_date: string;
  closing_date: string;
  lead_agent: string;
  use_of_proceeds: string;
  press_release_url: string;
  notes: string;
  is_closed: boolean;
};

const EMPTY_FORM: FinancingForm = {
  financing_type: "private_placement",
  status: "announced",
  amount_raised_usd: "",
  price_per_share: "",
  shares_issued: "",
  has_warrants: false,
  warrant_strike_price: "",
  warrant_expiry_date: "",
  announced_date: "",
  closing_date: "",
  lead_agent: "",
  use_of_proceeds: "",
  press_release_url: "",
  notes: "",
  is_closed: false,
};

/** Amount raised is displayed grouped ("4,000,000.00"), so every read of it
 *  has to strip the separators first — parseFloat("4,000,000") is 4, silently. */
function unformatAmount(value: string): string {
  return value.replace(/,/g, "");
}

/** Group the integer part in threes for display. Deliberately tolerant of a
 *  half-typed number — a trailing "." and an empty string both survive — so
 *  the field can reformat on every keystroke without fighting the typist. */
function formatAmount(value: string): string {
  const [whole, ...fraction] = value.replace(/[^0-9.]/g, "").split(".");
  const grouped = whole.replace(/(?=(?:[0-9]{3})+$)(?!^)/g, ",");
  // Only the first "." is a decimal point; later ones are typos, not a second.
  return fraction.length ? `${grouped}.${fraction.join("")}` : grouped;
}

/** How many characters of a value survive formatting. Commas the typist never
 *  pressed shift everything right, so the caret is restored by counting these
 *  rather than by raw offset — otherwise an edit mid-number jumps to the end. */
function significantCount(value: string): number {
  return (value.match(/[0-9.]/g) || []).length;
}

/** Index just past the `count`-th significant character of `formatted`. */
function caretAfter(formatted: string, count: number): number {
  if (count <= 0) return 0;
  let seen = 0;
  for (let i = 0; i < formatted.length; i++) {
    if (/[0-9.]/.test(formatted[i])) {
      seen += 1;
      if (seen === count) return i + 1;
    }
  }
  return formatted.length;
}

/** Share count implied by the size of the round at its announced price.
 *
 *  Upsizing a placement is what this form is mostly used for, and the share
 *  count moves with the amount — left behind, it publishes a figure that no
 *  longer matches the dollars beside it. Returns null when there is no usable
 *  price, so the existing count is left alone rather than blanked. */
function sharesFromAmount(amount: string, price: string): string | null {
  const raised = parseFloat(unformatAmount(amount));
  const perShare = parseFloat(price);
  if (!Number.isFinite(raised) || !Number.isFinite(perShare) || perShare <= 0) {
    return null;
  }
  return String(Math.round(raised / perShare));
}

export default function OpenFinancingsClient({
  initialData,
}: OpenFinancingsClientProps) {
  const [data, setData] = useState<OpenFinancingsResponse | null>(
    initialData ?? null,
  );
  const [loading, setLoading] = useState(!initialData);
  const [error, setError] = useState<string | null>(null);
  const [showLogin, setShowLogin] = useState(false);
  const [showRegister, setShowRegister] = useState(false);

  const [sortBy, setSortBy] = useState<string>("announced_date");
  const [sortOrder, setSortOrder] = useState<string>("desc");
  const [financingType, setFinancingType] = useState<string>("");
  const [searchQuery, setSearchQuery] = useState<string>("");

  const seeded = !!initialData;
  const didMountRef = useRef(false);

  /* Superuser editing. The rows on this page and the ones on
     /closed-financings are the same Financing records split by is_closed, so
     both edit through the same endpoint. */
  const { user } = useAuth();
  const canEdit = !!user?.is_superuser;
  const [editingFinancing, setEditingFinancing] =
    useState<OpenFinancing | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [formData, setFormData] = useState<FinancingForm>(EMPTY_FORM);

  const accessToken =
    typeof window !== "undefined" ? localStorage.getItem("accessToken") : null;

  const handleOpenEdit = (financing: OpenFinancing) => {
    setFormError(null);
    setEditingFinancing(financing);
    setFormData({
      financing_type: financing.financing_type,
      status: financing.status || "announced",
      amount_raised_usd: financing.amount_raised_usd
        ? formatAmount(String(financing.amount_raised_usd))
        : "",
      price_per_share: financing.price_per_share
        ? String(financing.price_per_share)
        : "",
      shares_issued: financing.shares_issued
        ? String(financing.shares_issued)
        : "",
      has_warrants: !!financing.has_warrants,
      warrant_strike_price: financing.warrant_strike_price
        ? String(financing.warrant_strike_price)
        : "",
      warrant_expiry_date: financing.warrant_expiry_date || "",
      announced_date: financing.announced_date || "",
      closing_date: financing.closing_date || "",
      lead_agent: financing.lead_agent || "",
      use_of_proceeds: financing.use_of_proceeds || "",
      press_release_url: financing.press_release_url || "",
      notes: financing.notes || "",
      is_closed: false,
    });
  };

  const handleCloseEdit = () => {
    setEditingFinancing(null);
    setFormData(EMPTY_FORM);
    setFormError(null);
  };

  const handleSubmitEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingFinancing) return;

    const amountRaised = parseFloat(unformatAmount(formData.amount_raised_usd));
    if (!Number.isFinite(amountRaised)) {
      setFormError("Amount is required.");
      return;
    }
    if (!formData.announced_date) {
      setFormError("Announced date is required.");
      return;
    }

    setFormError(null);
    setSubmitting(true);
    try {
      const token = accessToken || localStorage.getItem("accessToken");
      const response = await fetch(
        `${API_URL}/closed-financings/${editingFinancing.id}/update/`,
        {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            financing_type: formData.financing_type,
            status: formData.status,
            amount_raised_usd: amountRaised,
            price_per_share: formData.price_per_share
              ? parseFloat(formData.price_per_share)
              : null,
            shares_issued: formData.shares_issued
              ? parseInt(formData.shares_issued, 10)
              : null,
            has_warrants: formData.has_warrants,
            warrant_strike_price: formData.warrant_strike_price
              ? parseFloat(formData.warrant_strike_price)
              : null,
            warrant_expiry_date: formData.warrant_expiry_date || null,
            announced_date: formData.announced_date,
            closing_date: formData.closing_date || null,
            lead_agent: formData.lead_agent,
            use_of_proceeds: formData.use_of_proceeds,
            press_release_url: formData.press_release_url,
            notes: formData.notes,
            is_closed: formData.is_closed,
          }),
        },
      );

      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body.error || "Failed to save the financing.");
      }

      handleCloseEdit();
      // A row marked closed leaves this list, so refetch rather than patching
      // the local copy.
      fetchOpenFinancings({ silent: true });
    } catch (err) {
      setFormError(
        err instanceof Error ? err.message : "Failed to save the financing.",
      );
    } finally {
      setSubmitting(false);
    }
  };

  useEffect(() => {
    // The server already seeded default-sorted anonymous preview data. Skip the
    // redundant first fetch unless (a) the visitor is logged in and needs their
    // unlocked rows, or (b) they change a filter.
    const isFilterChange = didMountRef.current;
    didMountRef.current = true;
    if (!seeded || isFilterChange || accessToken) {
      fetchOpenFinancings({ silent: seeded && !isFilterChange });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sortBy, sortOrder, financingType]);

  const fetchOpenFinancings = async ({
    silent = false,
  }: { silent?: boolean } = {}) => {
    try {
      if (!silent) setLoading(true);

      const params = new URLSearchParams();
      params.append("sort_by", sortBy);
      params.append("sort_order", sortOrder);
      if (financingType) {
        params.append("financing_type", financingType);
      }

      const headers: Record<string, string> = {};
      if (accessToken) {
        headers["Authorization"] = `Bearer ${accessToken}`;
      }

      const response = await fetch(
        `${API_URL}/open-financings/?${params.toString()}`,
        {
          headers,
        },
      );

      if (!response.ok) {
        throw new Error("Failed to fetch open financings");
      }

      const json: OpenFinancingsResponse = await response.json();
      setData(json);
      setError(null);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load open financings",
      );
    } finally {
      if (!silent) setLoading(false);
    }
  };

  const formatCurrency = (amount: string | number) => {
    return new Intl.NumberFormat("en-CA", {
      style: "currency",
      currency: "CAD",
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(typeof amount === "string" ? parseFloat(amount) : amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  const filteredFinancings = (data?.results || []).filter((f) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      f.company_name.toLowerCase().includes(query) ||
      f.company_ticker.toLowerCase().includes(query) ||
      f.financing_type_display.toLowerCase().includes(query)
    );
  });

  const isPaid = data?.is_paid ?? false;
  const lockedCount = data?.locked_count ?? 0;

  // Find the index of the first locked row in the filtered list — used to
  // insert the upgrade banner once, immediately above the locked section.
  const firstLockedIndex = filteredFinancings.findIndex((f) => f.is_locked);

  const financingTypes = [
    { value: "", label: "All Types" },
    ...(data?.financing_types || []),
  ];

  return (
    <div className="min-h-screen bg-slate-900">
      <SiteHeader
        onLoginClick={() => setShowLogin(true)}
        onRegisterClick={() => setShowRegister(true)}
      />

      {showLogin && (
        <LoginModal
          onClose={() => setShowLogin(false)}
          onSwitchToRegister={() => {
            setShowLogin(false);
            setShowRegister(true);
          }}
        />
      )}
      {showRegister && (
        <RegisterModal
          onClose={() => setShowRegister(false)}
          onSwitchToLogin={() => {
            setShowRegister(false);
            setShowLogin(true);
          }}
        />
      )}

      {editingFinancing && (
        <Modal
          onClose={handleCloseEdit}
          size="2xl"
          labelledBy="edit-financing-title"
        >
          <form onSubmit={handleSubmitEdit} className="p-6">
            <h2
              id="edit-financing-title"
              className="font-display text-xl font-semibold text-gold-400"
            >
              Edit financing
            </h2>
            <p className="mt-1 mb-6 text-sm text-slate-400">
              {editingFinancing.company_name} (
              {editingFinancing.company_exchange}:
              {editingFinancing.company_ticker})
            </p>

            {formError && (
              <p className="mb-4 rounded-lg border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-300">
                {formError}
              </p>
            )}

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Field label="Type">
                <select
                  value={formData.financing_type}
                  onChange={(e) =>
                    setFormData({ ...formData, financing_type: e.target.value })
                  }
                  className={INPUT_CLASS}
                >
                  {(data?.financing_types || []).map((t) => (
                    <option key={t.value} value={t.value}>
                      {t.label}
                    </option>
                  ))}
                </select>
              </Field>

              <Field label="Status">
                <select
                  value={formData.status}
                  onChange={(e) =>
                    setFormData({ ...formData, status: e.target.value })
                  }
                  className={INPUT_CLASS}
                >
                  {STATUS_OPTIONS.map((o) => (
                    <option key={o.value} value={o.value}>
                      {o.label}
                    </option>
                  ))}
                </select>
              </Field>

              <Field label="Amount (CAD)" required>
                <input
                  type="text"
                  inputMode="decimal"
                  required
                  value={formData.amount_raised_usd}
                  onChange={(e) => {
                    const input = e.target;
                    const caret = input.selectionStart ?? input.value.length;
                    const typed = significantCount(input.value.slice(0, caret));
                    const amount = formatAmount(input.value);
                    const shares = sharesFromAmount(
                      amount,
                      formData.price_per_share,
                    );
                    setFormData({
                      ...formData,
                      amount_raised_usd: amount,
                      ...(shares === null ? {} : { shares_issued: shares }),
                    });
                    // Put the caret back behind the same digit it was behind.
                    // React rewrites value on the next paint, and a controlled
                    // reformat otherwise drops it at the end of the field.
                    requestAnimationFrame(() => {
                      const pos = caretAfter(amount, typed);
                      input.setSelectionRange(pos, pos);
                    });
                  }}
                  className={INPUT_CLASS}
                />
              </Field>

              <Field label="Price per share">
                <input
                  type="number"
                  step="0.0001"
                  value={formData.price_per_share}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      price_per_share: e.target.value,
                    })
                  }
                  className={INPUT_CLASS}
                />
              </Field>

              <Field label="Shares issued">
                <input
                  type="number"
                  value={formData.shares_issued}
                  onChange={(e) =>
                    setFormData({ ...formData, shares_issued: e.target.value })
                  }
                  className={INPUT_CLASS}
                />
                <p className="mt-1 text-xs text-slate-500">
                  Recalculated as amount &divide; price per share whenever you
                  change the amount. Type here to override it.
                </p>
              </Field>

              <Field label="Lead agent">
                <input
                  type="text"
                  value={formData.lead_agent}
                  onChange={(e) =>
                    setFormData({ ...formData, lead_agent: e.target.value })
                  }
                  className={INPUT_CLASS}
                />
              </Field>

              <Field label="Announced date" required>
                <input
                  type="date"
                  required
                  value={formData.announced_date}
                  onChange={(e) =>
                    setFormData({ ...formData, announced_date: e.target.value })
                  }
                  className={INPUT_CLASS}
                />
              </Field>

              <Field label="Closing date">
                <input
                  type="date"
                  value={formData.closing_date}
                  onChange={(e) =>
                    setFormData({ ...formData, closing_date: e.target.value })
                  }
                  className={INPUT_CLASS}
                />
              </Field>
            </div>

            <label className="mt-4 flex items-center gap-3 py-2 text-sm text-slate-300">
              <input
                type="checkbox"
                checked={formData.has_warrants}
                onChange={(e) =>
                  setFormData({ ...formData, has_warrants: e.target.checked })
                }
                className="h-5 w-5 rounded border-slate-600 bg-slate-800 text-gold-500"
              />
              Includes warrants
            </label>

            {formData.has_warrants && (
              <div className="mt-2 grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Field label="Warrant strike price">
                  <input
                    type="number"
                    step="0.0001"
                    value={formData.warrant_strike_price}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        warrant_strike_price: e.target.value,
                      })
                    }
                    className={INPUT_CLASS}
                  />
                </Field>
                <Field label="Warrant expiry">
                  <input
                    type="date"
                    value={formData.warrant_expiry_date}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        warrant_expiry_date: e.target.value,
                      })
                    }
                    className={INPUT_CLASS}
                  />
                </Field>
              </div>
            )}

            <div className="mt-4 space-y-4">
              <Field label="Use of proceeds">
                <textarea
                  rows={3}
                  value={formData.use_of_proceeds}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      use_of_proceeds: e.target.value,
                    })
                  }
                  className={INPUT_CLASS}
                />
              </Field>

              <Field label="Press release URL">
                <input
                  type="url"
                  value={formData.press_release_url}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      press_release_url: e.target.value,
                    })
                  }
                  className={INPUT_CLASS}
                />
              </Field>

              <Field label="Notes">
                <textarea
                  rows={2}
                  value={formData.notes}
                  onChange={(e) =>
                    setFormData({ ...formData, notes: e.target.value })
                  }
                  className={INPUT_CLASS}
                />
              </Field>
            </div>

            {/* The flag the two public pages split on. Ticking it moves this
                round off /open-financings and onto /closed-financings, and
                stamps who closed it. */}
            <label className="mt-6 flex items-start gap-3 rounded-lg border border-slate-700 bg-slate-800/40 p-4 text-sm text-slate-300">
              <input
                type="checkbox"
                checked={formData.is_closed}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    is_closed: e.target.checked,
                    status: e.target.checked ? "closed" : formData.status,
                  })
                }
                className="mt-0.5 h-5 w-5 shrink-0 rounded border-slate-600 bg-slate-800 text-gold-500"
              />
              <span>
                <span className="block font-medium text-slate-100">
                  Mark this round closed
                </span>
                <span className="mt-0.5 block text-slate-400">
                  Moves it off this page and onto Closed Financings.
                </span>
              </span>
            </label>

            <div className="mt-6 flex flex-col-reverse sm:flex-row sm:justify-end gap-3">
              <Button
                type="button"
                variant="secondary"
                onClick={handleCloseEdit}
                disabled={submitting}
              >
                Cancel
              </Button>
              <Button type="submit" variant="primary" disabled={submitting}>
                {submitting ? "Saving…" : "Save changes"}
              </Button>
            </div>
          </form>
        </Modal>
      )}

      {/* Hero */}
      <section className="relative py-12 px-4 sm:px-6 lg:px-8">
        <div className="absolute inset-0 bg-gradient-to-b from-slate-900 via-slate-900 to-slate-800 opacity-50"></div>
        <div
          className="absolute inset-0"
          style={{
            backgroundImage:
              "radial-gradient(circle at 50% 50%, rgba(212, 161, 42, 0.1) 0%, transparent 50%)",
          }}
        ></div>
        <div className="relative max-w-7xl mx-auto text-center">
          <Badge variant="gold" className="mb-4">
            Currently Raising
          </Badge>
          <h1 className="font-display text-2xl sm:text-3xl md:text-4xl font-semibold mb-4 text-gold-400 leading-tight tracking-tight italic">
            Open Financings
          </h1>
          <p className="text-lg text-slate-300 max-w-2xl mx-auto mb-2">
            Junior mining companies currently raising capital — private
            placements, bought deals, flow-through offerings, and more.
          </p>
          <p className="text-sm text-slate-400 max-w-2xl mx-auto mt-3 mb-2">
            New to mining financings?{" "}
            <Link
              href="/guides/how-junior-mining-companies-raise-money"
              className="text-gold-400 hover:underline"
            >
              Read our complete guide
            </Link>{" "}
            — covers placement structures, flow-through, warrants, and the
            dilution math you should run before participating.
          </p>
          {data && (
            <p className="text-sm text-slate-500">
              {data.total_count} open financing
              {data.total_count !== 1 ? "s" : ""}
              {!isPaid && lockedCount > 0 && (
                <>
                  {" "}
                  · Showing {data.preview_count} preview · {lockedCount} locked
                </>
              )}
            </p>
          )}
        </div>
      </section>

      {/* Filters — paid users only */}
      {isPaid && (
        <section className="py-6 px-4 sm:px-6 lg:px-8 border-b border-slate-800">
          <div className="max-w-7xl mx-auto">
            <div className="flex flex-col md:flex-row gap-4 items-start md:items-center justify-between">
              <div className="flex-1 max-w-md">
                <input
                  type="text"
                  placeholder="Search by company name or ticker..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-gold-400"
                />
              </div>
              <div className="flex flex-wrap gap-3">
                <select
                  value={financingType}
                  onChange={(e) => setFinancingType(e.target.value)}
                  className="px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-gold-400"
                >
                  {financingTypes.map((type) => (
                    <option key={type.value} value={type.value}>
                      {type.label}
                    </option>
                  ))}
                </select>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-gold-400"
                >
                  <option value="announced_date">Date Announced</option>
                  <option value="closing_date">Closing Date</option>
                  <option value="amount">Amount</option>
                  <option value="company">Company Name</option>
                </select>
                <button
                  onClick={() =>
                    setSortOrder(sortOrder === "asc" ? "desc" : "asc")
                  }
                  className="px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white hover:bg-slate-700 focus:outline-none focus:border-gold-400 flex items-center gap-2"
                >
                  {sortOrder === "desc" ? "Newest First" : "Oldest First"}
                </button>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* Main Content */}
      <section className="py-8 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gold-400"></div>
            </div>
          ) : error ? (
            <Card variant="glass-card" className="max-w-md mx-auto">
              <CardContent className="p-6 text-center">
                <p className="text-red-400 mb-4">{error}</p>
              </CardContent>
            </Card>
          ) : filteredFinancings.length === 0 ? (
            <Card variant="glass-card" className="max-w-md mx-auto">
              <CardContent className="p-12 text-center">
                <h2 className="text-xl font-semibold text-white mb-2">
                  No Open Financings
                </h2>
                <p className="text-slate-400">
                  No financings are currently open. Check back soon — new rounds
                  appear here as companies announce them.
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {filteredFinancings.map((financing, idx) => (
                <div key={financing.id}>
                  {/* Upgrade banner — inserted once, right before the first locked row */}
                  {!isPaid &&
                    idx === firstLockedIndex &&
                    firstLockedIndex >= 0 && (
                      <UpgradeBanner lockedCount={lockedCount} />
                    )}

                  {financing.is_locked ? (
                    <LockedFinancingCard financing={financing} />
                  ) : (
                    <OpenFinancingCard
                      financing={financing}
                      formatCurrency={formatCurrency}
                      formatDate={formatDate}
                      onEdit={canEdit ? handleOpenEdit : undefined}
                    />
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </section>

      <footer className="py-8 px-4 border-t border-slate-800 mt-12">
        <div className="max-w-7xl mx-auto text-center text-slate-400 text-sm">
          <p>
            &copy; {new Date().getFullYear()} GoldVenture. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}

function OpenFinancingCard({
  financing,
  formatCurrency,
  formatDate,
  onEdit,
}: {
  financing: OpenFinancing;
  formatCurrency: (amount: string | number) => string;
  formatDate: (dateString: string) => string;
  /** Passed only for superusers; undefined hides the button entirely. */
  onEdit?: (financing: OpenFinancing) => void;
}) {
  return (
    <Card
      variant="glass-card"
      className="hover:border-gold-500/30 transition-all"
    >
      <CardContent className="p-6">
        <div className="flex flex-col lg:flex-row gap-6">
          <div className="flex items-start gap-4 flex-1">
            <div className="w-14 h-14 rounded-lg bg-gradient-to-br from-gold-500/20 to-copper-500/20 flex items-center justify-center">
              <span className="text-xl font-bold text-gold-400">
                {financing.company_name.charAt(0)}
              </span>
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <Link
                  href={companyHref({
                    id: financing.company_id,
                    slug: financing.company_slug,
                  })}
                  className="text-lg font-semibold text-white hover:text-gold-400 transition-colors"
                >
                  {financing.company_name}
                </Link>
                <Badge variant="copper" className="text-xs">
                  {financing.company_exchange}:{financing.company_ticker}
                </Badge>
              </div>
              <div className="flex items-center gap-2 mb-2">
                <Badge variant="gold">{financing.financing_type_display}</Badge>
                {financing.has_warrants && (
                  <Badge variant="slate">With Warrants</Badge>
                )}
              </div>
              {financing.use_of_proceeds && (
                <p className="text-sm text-slate-400 line-clamp-2">
                  {financing.use_of_proceeds}
                </p>
              )}
            </div>
          </div>

          <div className="flex flex-col sm:flex-row lg:flex-col gap-4 lg:min-w-[200px] lg:text-right">
            {financing.amount_raised_usd && (
              <div>
                <p className="text-2xl font-bold text-gold-400">
                  {formatCurrency(financing.amount_raised_usd)}
                </p>
                <p className="text-xs text-slate-500">Amount</p>
              </div>
            )}
            <div className="flex flex-col sm:flex-row lg:flex-col gap-2 text-sm">
              {financing.price_per_share && (
                <div>
                  <span className="text-slate-500">Price: </span>
                  <span className="text-white">
                    ${Number(financing.price_per_share).toFixed(3)}
                  </span>
                </div>
              )}
              {financing.closing_date && (
                <div>
                  <span className="text-slate-500">Closes: </span>
                  <span className="text-white">
                    {formatDate(financing.closing_date)}
                  </span>
                </div>
              )}
              {financing.announced_date && (
                <div>
                  <span className="text-slate-500">Announced: </span>
                  <span className="text-white">
                    {formatDate(financing.announced_date)}
                  </span>
                </div>
              )}
            </div>
          </div>

          <div className="flex flex-row lg:flex-col gap-2 lg:justify-start">
            {/*
              The round itself — terms, how far it has filled, and the
              Participate in Financing flow. The card previously offered only
              the company profile and the press release, so the list of open
              deals had no route to acting on one. Same destination and wording
              as the "View Financing Details" button on a company's financings
              tab.
            */}
            <Link href={`/companies/${financing.company_id}/financing`}>
              <Button variant="primary" size="sm" className="w-full">
                View Financing Details
              </Button>
            </Link>
            <Link
              href={companyHref({
                id: financing.company_id,
                slug: financing.company_slug,
              })}
            >
              <Button variant="secondary" size="sm" className="w-full">
                View Company
              </Button>
            </Link>
            {financing.press_release_url && (
              <a
                href={financing.press_release_url}
                target="_blank"
                rel="noopener noreferrer"
              >
                <Button
                  variant="ghost"
                  size="sm"
                  className="w-full text-gold-400"
                >
                  Press Release
                </Button>
              </a>
            )}
            {onEdit && (
              <Button
                variant="ghost"
                size="sm"
                className="w-full text-slate-400 hover:text-gold-400"
                onClick={() => onEdit(financing)}
              >
                Edit
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function LockedFinancingCard({ financing }: { financing: OpenFinancing }) {
  return (
    <Card
      variant="glass-card"
      className="relative overflow-hidden border-slate-800/50 opacity-90"
    >
      <CardContent className="p-6">
        <div className="flex flex-col lg:flex-row gap-6">
          <div className="flex items-start gap-4 flex-1">
            <div className="w-14 h-14 rounded-lg bg-slate-800/60 flex items-center justify-center">
              <svg
                className="w-6 h-6 text-slate-500"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 11c0-1.657-1.343-3-3-3m6 3c0-1.657 1.343-3 3-3M12 11v6m-6-6a6 6 0 1112 0v0"
                />
              </svg>
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-lg font-semibold text-slate-300">
                  {financing.company_name}
                </span>
                <Badge variant="copper" className="text-xs">
                  {financing.company_exchange}:{financing.company_ticker}
                </Badge>
              </div>
              <div className="flex items-center gap-2 mb-2">
                <Badge variant="slate">
                  {financing.financing_type_display}
                </Badge>
              </div>
              <p
                className="text-sm text-slate-500 select-none"
                style={{ filter: "blur(4px)" }}
              >
                Use of proceeds available to subscribers — terms, pricing, and
                closing date hidden.
              </p>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row lg:flex-col gap-4 lg:min-w-[200px] lg:text-right">
            <div>
              <p
                className="text-2xl font-bold text-gold-400/60 select-none"
                style={{ filter: "blur(6px)" }}
              >
                $••••••••
              </p>
              <p className="text-xs text-slate-500">Amount</p>
            </div>
            <div className="flex flex-col sm:flex-row lg:flex-col gap-2 text-sm">
              <div>
                <span className="text-slate-500">Closes: </span>
                <span
                  className="text-slate-400 select-none"
                  style={{ filter: "blur(4px)" }}
                >
                  ••• ••, ••••
                </span>
              </div>
            </div>
          </div>

          <div className="flex flex-row lg:flex-col gap-2 lg:justify-start">
            <Link href="/pricing">
              <Button variant="primary" size="sm" className="w-full">
                Unlock
              </Button>
            </Link>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function UpgradeBanner({ lockedCount }: { lockedCount: number }) {
  return (
    <div className="my-6">
      <Card
        variant="glass-card"
        className="border-gold-500/40 bg-gradient-to-r from-gold-500/10 via-copper-500/10 to-gold-500/10"
      >
        <CardContent className="p-6 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 rounded-lg bg-gold-500/20 flex items-center justify-center flex-shrink-0">
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
                  d="M13 10V3L4 14h7v7l9-11h-7z"
                />
              </svg>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-white mb-1">
                {lockedCount} more open financing{lockedCount !== 1 ? "s" : ""}{" "}
                — <span className="text-gold-400">unlock with Prospector</span>
              </h3>
              <p className="text-sm text-slate-400">
                See every open round&apos;s amount, pricing, closing date, and
                use of proceeds. Includes email alerts for new financings.
              </p>
            </div>
          </div>
          <Link href="/pricing">
            <Button variant="primary" size="lg" className="whitespace-nowrap">
              Upgrade →
            </Button>
          </Link>
        </CardContent>
      </Card>
    </div>
  );
}

/* Shared control styling for the edit form. 16px on mobile so iOS does not
   zoom the viewport when a field takes focus. */
const INPUT_CLASS =
  "w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2.5 min-h-11 text-base sm:text-sm text-slate-100 placeholder-slate-500 focus:border-gold-500/60 focus:outline-none";

function Field({
  label,
  required,
  children,
}: {
  label: string;
  required?: boolean;
  children: React.ReactNode;
}) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-sm text-slate-400">
        {label}
        {required && <span className="ml-1 text-gold-400">*</span>}
      </span>
      {children}
    </label>
  );
}
