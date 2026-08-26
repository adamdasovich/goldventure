"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import {
  companyAPI,
  projectAPI,
  newsAPI,
  accessRequestAPI,
  companyResourceAPI,
  financingAPI,
  type Company,
  type Project,
  type NewsReleasesResponse,
} from "@/lib/api";
import SiteHeader from "@/components/SiteHeader";
import {
  CompanySchema,
  BreadcrumbListSchema,
} from "@/components/StructuredData";
import CompanyChatbot from "@/components/CompanyChatbot";
import { CompanyForum, FloatingForumButton } from "@/components/forum";
import { EventBanner } from "@/components/events";
import { LoginModal, RegisterModal } from "@/components/auth";
import WatchButton from "@/components/WatchButton";
import {
  CompanyRepRegistrationModal,
  CompanyResourceUploadModal,
  CreateFinancingModal,
} from "@/components/company";
import { useAuth } from "@/contexts/AuthContext";
import type { CompanyResource, CompanyAccessRequest } from "@/types/api";

interface StockQuote {
  ticker: string;
  exchange: string;
  price: number;
  change: number;
  change_percent: number;
  volume: number;
  date: string;
  source: string;
  cached: boolean;
}

interface CompanyDetailClientProps {
  initialCompany?: Company;
  initialProjects?: Project[];
}

const TAB_IDS = [
  "overview",
  "events",
  "news",
  "financings",
  "resources",
  "forum",
] as const;
type TabId = (typeof TAB_IDS)[number];

function readTabFromUrl(): TabId {
  if (typeof window === "undefined") return "overview";
  const tab = new URLSearchParams(window.location.search).get("tab");
  return tab && (TAB_IDS as readonly string[]).includes(tab)
    ? (tab as TabId)
    : "overview";
}

export default function CompanyDetailClient({
  initialCompany,
  initialProjects,
}: CompanyDetailClientProps) {
  const params = useParams();
  const router = useRouter();
  // params.id may be `{numericId}-{slug}` — strip everything after the leading
  // integer for API lookups. The internal API only knows numeric ids.
  const rawIdSegment = params.id as string;
  const companyId = (rawIdSegment || "").split("-")[0];
  const { user, accessToken } = useAuth();

  // Tab state — mirrored into the URL (?tab=forum) so the discovery pill, FAB,
  // and external links can deep-link straight into a tab and the choice
  // survives refresh / back-forward navigation.
  //
  // Deliberately NOT `useSearchParams()`. This route is statically prerendered
  // (generateStaticParams + revalidate), and reading that hook opts the whole
  // subtree out of prerendering — every company page shipped loading.tsx's
  // skeleton to Googlebot instead of the profile (7 words, no <h1>). Seeding
  // from "overview" and syncing after mount keeps the server render intact,
  // and "overview" is the tab holding the indexable content anyway.
  const [activeTab, setActiveTabState] = useState<TabId>("overview");

  useEffect(() => {
    const syncFromUrl = () => setActiveTabState(readTabFromUrl());
    // Deep links (?tab=forum) land on "overview" for one paint, then correct.
    syncFromUrl();
    // Back/forward across tabs came free with useSearchParams; restore it.
    window.addEventListener("popstate", syncFromUrl);
    return () => window.removeEventListener("popstate", syncFromUrl);
  }, []);

  const setActiveTab = useCallback(
    (tab: TabId, opts?: { scrollIntoView?: string }) => {
      setActiveTabState(tab);
      const next = new URLSearchParams(window.location.search);
      if (tab === "overview") {
        next.delete("tab");
      } else {
        next.set("tab", tab);
      }
      const qs = next.toString();
      // Keep the `{id}-{slug}` segment. Rewriting to the bare numeric id sent
      // every tab click through middleware's 308 back to the canonical URL.
      router.replace(`/companies/${rawIdSegment}${qs ? `?${qs}` : ""}`, {
        scroll: false,
      });
      if (opts?.scrollIntoView) {
        // Wait one frame so the newly-mounted target exists in the DOM.
        requestAnimationFrame(() => {
          const el = document.getElementById(opts.scrollIntoView!);
          if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
        });
      }
    },
    [rawIdSegment, router],
  );

  const jumpToForum = useCallback(() => {
    setActiveTab("forum", { scrollIntoView: "community-forum" });
  }, [setActiveTab]);

  const [company, setCompany] = useState<Company | null>(
    initialCompany || null,
  );
  const [projects, setProjects] = useState<Project[]>(initialProjects || []);
  const [loading, setLoading] = useState(!initialCompany);
  const [error, setError] = useState<string | null>(null);
  const [newsData, setNewsData] = useState<NewsReleasesResponse | null>(null);
  const [newsLoading, setNewsLoading] = useState(false);
  const [scrapingNews, setScrapingNews] = useState(false);
  const [scrapeError, setScrapeError] = useState<string | null>(null);
  const [showLogin, setShowLogin] = useState(false);
  const [showRegister, setShowRegister] = useState(false);
  const [financings, setFinancings] = useState<any[]>([]);
  const [interestAggregates, setInterestAggregates] = useState<
    Record<
      number,
      {
        total_interest_count: number;
        total_shares_requested: number;
        total_amount_interested: string;
        percentage_filled: string;
      }
    >
  >({});
  const [stockQuote, setStockQuote] = useState<StockQuote | null>(null);
  const [stockLoading, setStockLoading] = useState(false);

  // Company representative states
  const [isCompanyRep, setIsCompanyRep] = useState(false);
  const [pendingRequest, setPendingRequest] =
    useState<CompanyAccessRequest | null>(null);
  const [showRepRegistration, setShowRepRegistration] = useState(false);
  const [showResourceUpload, setShowResourceUpload] = useState(false);
  const [companyResources, setCompanyResources] = useState<CompanyResource[]>(
    [],
  );
  const [resourcesLoading, setResourcesLoading] = useState(false);
  const [deletingResourceId, setDeletingResourceId] = useState<number | null>(
    null,
  );
  const [showCreateFinancing, setShowCreateFinancing] = useState(false);
  const [deletingFinancingId, setDeletingFinancingId] = useState<number | null>(
    null,
  );

  // Editable description states
  const [canEditCompany, setCanEditCompany] = useState(false);
  const [isEditingDescription, setIsEditingDescription] = useState(false);
  const [editedDescription, setEditedDescription] = useState("");
  const [savingDescription, setSavingDescription] = useState(false);
  const [descriptionError, setDescriptionError] = useState<string | null>(null);

  // Project management states (superuser only)
  const [showAddProject, setShowAddProject] = useState(false);
  const [deletingProjectId, setDeletingProjectId] = useState<number | null>(
    null,
  );
  const [newProject, setNewProject] = useState({
    name: "",
    project_stage: "early_exploration",
    primary_commodity: "gold",
    country: "",
    province_state: "",
    description: "",
  });
  const [savingProject, setSavingProject] = useState(false);
  const [projectError, setProjectError] = useState<string | null>(null);

  // Edit project states
  const [editingProject, setEditingProject] = useState<Project | null>(null);
  const [editProjectForm, setEditProjectForm] = useState({
    name: "",
    project_stage: "",
    primary_commodity: "",
    country: "",
    province_state: "",
    description: "",
    is_flagship: false,
  });
  const [savingEditProject, setSavingEditProject] = useState(false);
  const [editProjectError, setEditProjectError] = useState<string | null>(null);

  const API_URL =
    process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

  useEffect(() => {
    // Create AbortController for cleanup
    const abortController = new AbortController();

    if (companyId) {
      // Skip company/projects fetch if we have SSR data
      if (!initialCompany) {
        fetchCompanyDetails(abortController.signal);
      }
      fetchNewsReleases(abortController.signal);
      fetchFinancings(abortController.signal);
      fetchStockQuote(abortController.signal);
      fetchCompanyResources(abortController.signal);
    }

    // Cleanup: abort requests on dependency change or unmount
    return () => {
      abortController.abort();
    };
  }, [companyId]);

  // Check user's representative status for this company
  useEffect(() => {
    if (accessToken && companyId && user) {
      checkRepresentativeStatus();
    }
  }, [accessToken, companyId, user]);

  const checkRepresentativeStatus = async () => {
    if (!accessToken) {
      setIsCompanyRep(false);
      setPendingRequest(null);
      setCanEditCompany(false);
      return;
    }

    try {
      // Reset state first
      setIsCompanyRep(false);
      setPendingRequest(null);
      setCanEditCompany(false);

      // Superusers and staff have access to all companies
      if (user?.is_superuser || user?.is_staff) {
        setIsCompanyRep(true);
        setCanEditCompany(true);
        return;
      }

      // Check if user is a representative for this specific company
      const companyIdNum = parseInt(companyId);

      if (user?.company_id === companyIdNum) {
        setIsCompanyRep(true);
        setCanEditCompany(true);
        return;
      }

      // Check for pending request for this company
      const response = await accessRequestAPI
        .getMyRequest(accessToken)
        .catch(() => null);
      if (response && "id" in response) {
        // User has a pending request - check if it's for this company
        const request = response as CompanyAccessRequest;
        if (request.company === companyIdNum && request.status === "pending") {
          setPendingRequest(request);
        }
      }
    } catch (err) {
      console.error("Failed to check representative status:", err);
    }
  };

  const fetchCompanyResources = async (signal?: AbortSignal) => {
    try {
      setResourcesLoading(true);
      const res = await fetch(
        `${API_URL}/company-portal/resources/?company=${companyId}`,
        { signal },
      );
      if (signal?.aborted) return;
      if (res.ok) {
        const data = await res.json();
        setCompanyResources(data.results || data || []);
      }
    } catch (err) {
      if (err instanceof Error && err.name === "AbortError") return;
      console.error("Failed to fetch company resources:", err);
    } finally {
      if (!signal?.aborted) {
        setResourcesLoading(false);
      }
    }
  };

  const fetchStockQuote = async (signal?: AbortSignal) => {
    try {
      setStockLoading(true);
      const res = await fetch(
        `${API_URL}/companies/${companyId}/stock-quote/`,
        { signal },
      );
      if (signal?.aborted) return;
      if (res.ok) {
        const data = await res.json();
        setStockQuote(data);
      }
    } catch (err) {
      if (err instanceof Error && err.name === "AbortError") return;
      console.error("Failed to fetch stock quote:", err);
    } finally {
      if (!signal?.aborted) {
        setStockLoading(false);
      }
    }
  };

  const fetchCompanyDetails = async (signal?: AbortSignal) => {
    try {
      setLoading(true);
      const [companyData, projectsData] = await Promise.all([
        companyAPI.getById(parseInt(companyId)),
        companyAPI.getProjects(parseInt(companyId)),
      ]);
      if (signal?.aborted) return;
      setCompany(companyData);
      setProjects(projectsData);
      setError(null);
    } catch (err) {
      if (err instanceof Error && err.name === "AbortError") return;
      if (!signal?.aborted) {
        setError(
          err instanceof Error
            ? err.message
            : "Failed to fetch company details",
        );
      }
    } finally {
      if (!signal?.aborted) {
        setLoading(false);
      }
    }
  };

  const fetchNewsReleases = async (signal?: AbortSignal) => {
    try {
      setNewsLoading(true);
      const data = await newsAPI.getNewsReleases(parseInt(companyId));
      if (signal?.aborted) return;
      setNewsData(data);
    } catch (err) {
      if (err instanceof Error && err.name === "AbortError") return;
      console.error("Failed to fetch news releases:", err);
    } finally {
      if (!signal?.aborted) {
        setNewsLoading(false);
      }
    }
  };

  const fetchFinancings = async (signal?: AbortSignal) => {
    try {
      const res = await fetch(`${API_URL}/financings/?company=${companyId}`, {
        signal,
      });
      if (signal?.aborted) return;
      if (res.ok) {
        const data = await res.json();
        const financingsList = data.results || data;
        setFinancings(financingsList);
        // Fetch interest aggregates for open financings
        const openFinancings = financingsList.filter(
          (f: any) =>
            f.status === "announced" ||
            f.status === "closing" ||
            f.status === "open",
        );
        for (const financing of openFinancings) {
          fetchInterestAggregate(financing.id, signal);
        }
      }
    } catch (err) {
      if (err instanceof Error && err.name === "AbortError") return;
      console.error("Failed to fetch financings:", err);
    }
  };

  const fetchInterestAggregate = async (
    financingId: number,
    signal?: AbortSignal,
  ) => {
    try {
      const res = await fetch(
        `${API_URL}/investment-interest/aggregate/${financingId}/`,
        { signal },
      );
      if (signal?.aborted) return;
      if (res.ok) {
        const data = await res.json();
        setInterestAggregates((prev) => ({
          ...prev,
          [financingId]: data,
        }));
      }
    } catch (err) {
      if (err instanceof Error && err.name === "AbortError") return;
      console.error("Failed to fetch interest aggregate:", err);
    }
  };

  const handleScrapeNews = async () => {
    try {
      setScrapingNews(true);
      setScrapeError(null);
      const result = await newsAPI.scrapeNews(parseInt(companyId));

      if (result.status === "success" || result.status === "cached") {
        // Refresh news releases after scraping
        await fetchNewsReleases();
        setScrapeError(null);
      } else if (result.status === "error") {
        // Handle error response gracefully
        setScrapeError(result.message || "Failed to scrape news releases");
        // Still try to refresh in case some data was saved
        await fetchNewsReleases();
      }
    } catch (err) {
      console.error("Failed to scrape news:", err);
      setScrapeError(
        err instanceof Error
          ? err.message
          : "An unexpected error occurred while scraping news",
      );
    } finally {
      setScrapingNews(false);
    }
  };

  const handleDeleteResource = async (resourceId: number) => {
    if (!accessToken) return;

    if (
      !confirm(
        "Are you sure you want to delete this resource? This action cannot be undone.",
      )
    ) {
      return;
    }

    try {
      setDeletingResourceId(resourceId);
      await companyResourceAPI.delete(accessToken, resourceId);
      // Remove from local state
      setCompanyResources((prev) => prev.filter((r) => r.id !== resourceId));
    } catch (err) {
      console.error("Failed to delete resource:", err);
      alert("Failed to delete resource. Please try again.");
    } finally {
      setDeletingResourceId(null);
    }
  };

  const handleDeleteFinancing = async (financingId: number) => {
    if (!accessToken) return;

    if (
      !confirm(
        "Are you sure you want to delete this financing? This action cannot be undone.",
      )
    ) {
      return;
    }

    try {
      setDeletingFinancingId(financingId);
      await financingAPI.delete(accessToken, financingId);
      // Remove from local state
      setFinancings((prev) => prev.filter((f) => f.id !== financingId));
    } catch (err) {
      console.error("Failed to delete financing:", err);
      alert("Failed to delete financing. Please try again.");
    } finally {
      setDeletingFinancingId(null);
    }
  };

  const getExchangeBadgeVariant = (exchange: string) => {
    const variants: Record<string, "gold" | "copper" | "slate"> = {
      TSX: "gold",
      TSXV: "copper",
      NYSE: "gold",
      NASDAQ: "gold",
    };
    return variants[exchange.toUpperCase()] || "slate";
  };

  const formatNumber = (num: number | null | undefined) => {
    if (!num) return "---";
    return num.toLocaleString("en-US");
  };

  // Description editing handlers
  const handleEditDescription = () => {
    setEditedDescription(company?.description || "");
    setIsEditingDescription(true);
    setDescriptionError(null);
  };

  const handleCancelEditDescription = () => {
    setIsEditingDescription(false);
    setEditedDescription("");
    setDescriptionError(null);
  };

  const handleSaveDescription = async () => {
    if (!accessToken || !company) return;

    setSavingDescription(true);
    setDescriptionError(null);

    try {
      const result = await companyAPI.updateDescription(
        parseInt(companyId),
        editedDescription,
        accessToken,
      );

      if (result.success) {
        // Update local company state with new description
        setCompany({ ...company, description: result.description });
        setIsEditingDescription(false);
        setEditedDescription("");
      }
    } catch (err) {
      console.error("Failed to save description:", err);
      setDescriptionError(
        err instanceof Error ? err.message : "Failed to save description",
      );
    } finally {
      setSavingDescription(false);
    }
  };

  // Project management handlers (admins only)
  const handleAddProject = async () => {
    if (!accessToken || !canEditCompany) return;

    setSavingProject(true);
    setProjectError(null);

    try {
      const projectData = {
        company: parseInt(companyId),
        name: newProject.name,
        project_stage: newProject.project_stage,
        primary_commodity: newProject.primary_commodity,
        country: newProject.country,
        province_state: newProject.province_state || undefined,
        description: newProject.description || undefined,
      };

      const createdProject = await projectAPI.create(projectData, accessToken);
      setProjects([...projects, createdProject]);
      setShowAddProject(false);
      setNewProject({
        name: "",
        project_stage: "early_exploration",
        primary_commodity: "gold",
        country: "",
        province_state: "",
        description: "",
      });
    } catch (err) {
      console.error("Failed to create project:", err);
      setProjectError(
        err instanceof Error ? err.message : "Failed to create project",
      );
    } finally {
      setSavingProject(false);
    }
  };

  const handleDeleteProject = async (projectId: number) => {
    if (!accessToken || !canEditCompany) return;

    if (
      !confirm(
        "Are you sure you want to delete this project? This action cannot be undone.",
      )
    ) {
      return;
    }

    setDeletingProjectId(projectId);

    try {
      await projectAPI.delete(projectId, accessToken);
      setProjects(projects.filter((p) => p.id !== projectId));
    } catch (err) {
      console.error("Failed to delete project:", err);
      alert(err instanceof Error ? err.message : "Failed to delete project");
    } finally {
      setDeletingProjectId(null);
    }
  };

  // Edit project handlers
  const handleEditProject = (project: Project) => {
    setEditingProject(project);
    setEditProjectForm({
      name: project.name || "",
      project_stage: project.project_stage || "early_exploration",
      primary_commodity: project.primary_commodity || "gold",
      country: project.country || "",
      province_state: project.province_state || "",
      description: project.description || "",
      is_flagship: project.is_flagship || false,
    });
    setEditProjectError(null);
  };

  const handleCancelEditProject = () => {
    setEditingProject(null);
    setEditProjectForm({
      name: "",
      project_stage: "",
      primary_commodity: "",
      country: "",
      province_state: "",
      description: "",
      is_flagship: false,
    });
    setEditProjectError(null);
  };

  const handleSaveEditProject = async () => {
    if (!accessToken || !canEditCompany || !editingProject) return;

    setSavingEditProject(true);
    setEditProjectError(null);

    try {
      const updatedProject = await projectAPI.update(
        editingProject.id,
        {
          name: editProjectForm.name,
          project_stage: editProjectForm.project_stage,
          primary_commodity: editProjectForm.primary_commodity,
          country: editProjectForm.country,
          province_state: editProjectForm.province_state || undefined,
          description: editProjectForm.description || undefined,
          is_flagship: editProjectForm.is_flagship,
        },
        accessToken,
      );

      // Update the project in the local state
      setProjects(
        projects.map((p) => (p.id === editingProject.id ? updatedProject : p)),
      );
      setEditingProject(null);
      setEditProjectForm({
        name: "",
        project_stage: "",
        primary_commodity: "",
        country: "",
        province_state: "",
        description: "",
        is_flagship: false,
      });
    } catch (err) {
      console.error("Failed to update project:", err);
      setEditProjectError(
        err instanceof Error ? err.message : "Failed to update project",
      );
    } finally {
      setSavingEditProject(false);
    }
  };

  return (
    <div className="min-h-screen">
      {/* Structured Data */}
      {company && (
        <>
          <CompanySchema
            name={company.name}
            tickerSymbol={company.ticker_symbol}
            exchange={company.exchange}
            website={company.website}
            headquarters={company.headquarters}
            description={company.description}
          />
          <BreadcrumbListSchema
            items={[
              { name: "Home", url: "https://juniorminingintelligence.com/" },
              {
                name: "Companies",
                url: "https://juniorminingintelligence.com/companies",
              },
              {
                name: company.name,
                url: `https://juniorminingintelligence.com/companies/${company.id}`,
              },
            ]}
          />
        </>
      )}

      {/* Navigation */}
      <SiteHeader
        active="/companies"
        onLoginClick={() => setShowLogin(true)}
        onRegisterClick={() => setShowRegister(true)}
      />

      {/* Auth Modals */}
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

      {/* Company Representative Registration Modal */}
      {showRepRegistration && company && (
        <CompanyRepRegistrationModal
          companyId={parseInt(companyId)}
          companyName={company.name}
          accessToken={accessToken}
          onClose={() => setShowRepRegistration(false)}
          onSubmitSuccess={(request) => {
            setPendingRequest(request);
            setShowRepRegistration(false);
          }}
        />
      )}

      {/* Company Resource Upload Modal */}
      {showResourceUpload && company && (
        <CompanyResourceUploadModal
          companyId={parseInt(companyId)}
          accessToken={accessToken}
          onClose={() => setShowResourceUpload(false)}
          onUploadComplete={() => {
            fetchCompanyResources();
          }}
        />
      )}

      {/* Create Financing Modal */}
      {showCreateFinancing && company && (
        <CreateFinancingModal
          companyId={parseInt(companyId)}
          companyName={company.name}
          accessToken={accessToken}
          onClose={() => setShowCreateFinancing(false)}
          onCreateComplete={() => {
            fetchFinancings();
          }}
        />
      )}

      {/* Edit Project Modal */}
      {editingProject && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-xl w-full max-w-2xl max-h-[90dvh] overflow-y-auto">
            <div className="p-6 border-b border-slate-700">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-bold text-gold-400">
                  Edit Project
                </h2>
                <button
                  type="button"
                  onClick={handleCancelEditProject}
                  className="p-2 text-slate-400 hover:text-white transition-colors"
                  title="Close"
                >
                  <svg
                    className="w-5 h-5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                </button>
              </div>
            </div>
            <div className="p-6 space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-slate-400 mb-1">
                    Project Name *
                  </label>
                  <input
                    type="text"
                    value={editProjectForm.name}
                    onChange={(e) =>
                      setEditProjectForm({
                        ...editProjectForm,
                        name: e.target.value,
                      })
                    }
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-gold-400"
                    placeholder="e.g., Gold Mountain Project"
                  />
                </div>
                <div>
                  <label className="block text-sm text-slate-400 mb-1">
                    Country *
                  </label>
                  <input
                    type="text"
                    value={editProjectForm.country}
                    onChange={(e) =>
                      setEditProjectForm({
                        ...editProjectForm,
                        country: e.target.value,
                      })
                    }
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-gold-400"
                    placeholder="e.g., Canada"
                  />
                </div>
                <div>
                  <label className="block text-sm text-slate-400 mb-1">
                    Province/State
                  </label>
                  <input
                    type="text"
                    value={editProjectForm.province_state}
                    onChange={(e) =>
                      setEditProjectForm({
                        ...editProjectForm,
                        province_state: e.target.value,
                      })
                    }
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-gold-400"
                    placeholder="e.g., Ontario"
                  />
                </div>
                <div>
                  <label
                    htmlFor="edit_primary_commodity"
                    className="block text-sm text-slate-400 mb-1"
                  >
                    Primary Commodity *
                  </label>
                  <select
                    id="edit_primary_commodity"
                    value={editProjectForm.primary_commodity}
                    onChange={(e) =>
                      setEditProjectForm({
                        ...editProjectForm,
                        primary_commodity: e.target.value,
                      })
                    }
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-gold-400"
                  >
                    <option value="gold">Gold</option>
                    <option value="silver">Silver</option>
                    <option value="copper">Copper</option>
                    <option value="lithium">Lithium</option>
                    <option value="nickel">Nickel</option>
                    <option value="cobalt">Cobalt</option>
                    <option value="rare_earths">Rare Earth Elements</option>
                    <option value="zinc">Zinc</option>
                    <option value="uranium">Uranium</option>
                    <option value="multi_metal">Multi-Metal</option>
                    <option value="other">Other</option>
                  </select>
                </div>
                <div>
                  <label
                    htmlFor="edit_project_stage"
                    className="block text-sm text-slate-400 mb-1"
                  >
                    Project Stage *
                  </label>
                  <select
                    id="edit_project_stage"
                    value={editProjectForm.project_stage}
                    onChange={(e) =>
                      setEditProjectForm({
                        ...editProjectForm,
                        project_stage: e.target.value,
                      })
                    }
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-gold-400"
                  >
                    <option value="grassroots">Grassroots Exploration</option>
                    <option value="early_exploration">
                      Early Stage Exploration
                    </option>
                    <option value="advanced_exploration">
                      Advanced Exploration
                    </option>
                    <option value="resource">Resource Stage</option>
                    <option value="pea">PEA Completed</option>
                    <option value="pfs">PFS Completed</option>
                    <option value="fs">Feasibility Study</option>
                    <option value="permitting">Permitting</option>
                    <option value="development">Development</option>
                    <option value="production">Production</option>
                  </select>
                </div>
                <div className="flex items-center gap-3">
                  <label
                    htmlFor="edit_is_flagship"
                    className="block text-sm text-slate-400"
                  >
                    Flagship Project
                  </label>
                  <input
                    id="edit_is_flagship"
                    type="checkbox"
                    checked={editProjectForm.is_flagship}
                    onChange={(e) =>
                      setEditProjectForm({
                        ...editProjectForm,
                        is_flagship: e.target.checked,
                      })
                    }
                    className="w-5 h-5 rounded border-slate-700 bg-slate-800 text-gold-500 focus:ring-gold-500 focus:ring-offset-slate-900"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm text-slate-400 mb-1">
                  Description
                </label>
                <textarea
                  value={editProjectForm.description}
                  onChange={(e) =>
                    setEditProjectForm({
                      ...editProjectForm,
                      description: e.target.value,
                    })
                  }
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-gold-400 h-24"
                  placeholder="Brief description of the project..."
                />
              </div>
              {editProjectError && (
                <div className="text-red-400 text-sm">{editProjectError}</div>
              )}
              <div className="flex gap-2 pt-2">
                <Button
                  variant="primary"
                  size="sm"
                  onClick={handleSaveEditProject}
                  disabled={
                    savingEditProject ||
                    !editProjectForm.name ||
                    !editProjectForm.country
                  }
                >
                  {savingEditProject ? "Saving..." : "Save Changes"}
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={handleCancelEditProject}
                >
                  Cancel
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {error && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Card variant="glass-card">
            <CardContent className="py-12 text-center">
              <div className="text-red-400 mb-4">{error}</div>
              <Button
                variant="secondary"
                onClick={() => (window.location.href = "/companies")}
              >
                Back to Companies
              </Button>
            </CardContent>
          </Card>
        </div>
      )}

      {loading ? (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Card variant="glass-card">
            <CardContent className="py-12 text-center">
              <div className="text-slate-400">Loading company details...</div>
            </CardContent>
          </Card>
        </div>
      ) : company ? (
        <>
          {/* JSON-LD Schema Markup for Company */}
          <script
            type="application/ld+json"
            dangerouslySetInnerHTML={{
              __html: JSON.stringify({
                "@context": "https://schema.org",
                "@type": "Corporation",
                name: company.name,
                description:
                  company.description ||
                  `${company.name} is a mining company listed on ${company.exchange.toUpperCase()}.`,
                url: `https://juniorminingintelligence.com/companies/${companyId}`,
                tickerSymbol: `${company.exchange.toUpperCase()}:${company.ticker_symbol}`,
                ...(company.website && { sameAs: [company.website] }),
                ...(stockQuote && {
                  quote: {
                    "@type": "MonetaryAmount",
                    currency: "CAD",
                    value: stockQuote.price,
                  },
                }),
              }),
            }}
          />

          {/* Company Header */}
          <section className="relative py-12 px-4 sm:px-6 lg:px-8 bg-gradient-slate">
            <div className="max-w-7xl mx-auto">
              <div className="flex items-start justify-between mb-6">
                <div className="flex-1">
                  <div className="flex items-center gap-4 mb-3">
                    {/* Company Logo */}
                    {company.logo_url ? (
                      <img
                        src={company.logo_url}
                        alt={company.name}
                        className="w-16 h-16 rounded-lg object-contain bg-white p-2"
                      />
                    ) : (
                      <div className="w-16 h-16 rounded-lg bg-gradient-to-br from-gold-500/20 to-copper-500/20 flex items-center justify-center">
                        <span className="text-2xl font-bold text-gold-400">
                          {company.name.charAt(0)}
                        </span>
                      </div>
                    )}
                    <h1 className="font-display text-3xl sm:text-4xl font-bold text-slate-50 break-words tracking-tight">
                      {company.name}
                    </h1>
                    {/* Ticker & Exchange Info */}
                    <span className="text-xl font-mono text-gold-400 font-semibold">
                      {company.exchange.toUpperCase()}:{company.ticker_symbol}
                    </span>
                    <WatchButton
                      companyId={company.id}
                      onRequireLogin={() => setShowLogin(true)}
                    />
                    {/* Forum discovery pill — surfaces the Community Forum
                        above the fold so users don't have to scroll the page
                        to discover it exists. */}
                    <button
                      type="button"
                      onClick={jumpToForum}
                      aria-label="Jump to community forum"
                      className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-gold-500/10 hover:bg-gold-500/20 border border-gold-500/40 text-sm font-medium text-gold-300 hover:text-gold-200 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-gold-400 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900"
                    >
                      <span
                        className="w-2 h-2 rounded-full bg-green-400 motion-safe:animate-pulse"
                        aria-hidden="true"
                      />
                      <svg
                        className="w-4 h-4"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                        aria-hidden="true"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                        />
                      </svg>
                      <span>Join the discussion</span>
                    </button>
                  </div>
                  {/* Editable Description */}
                  {isEditingDescription ? (
                    <div className="max-w-3xl">
                      <textarea
                        value={editedDescription}
                        onChange={(e) => setEditedDescription(e.target.value)}
                        className="w-full h-32 px-4 py-3 bg-slate-800/50 border border-slate-600 rounded-lg text-slate-200 text-lg resize-none focus:outline-none focus:border-gold-400 focus:ring-1 focus:ring-gold-400"
                        placeholder="Enter company description..."
                        disabled={savingDescription}
                      />
                      {descriptionError && (
                        <p className="text-red-400 text-sm mt-2">
                          {descriptionError}
                        </p>
                      )}
                      <div className="flex gap-2 mt-3">
                        <Button
                          variant="primary"
                          size="sm"
                          onClick={handleSaveDescription}
                          disabled={savingDescription}
                        >
                          {savingDescription ? "Saving..." : "Save"}
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={handleCancelEditDescription}
                          disabled={savingDescription}
                        >
                          Cancel
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <div className="flex items-start gap-2 max-w-3xl">
                      {company.description ? (
                        <p className="text-slate-300 text-lg flex-1">
                          {company.description}
                        </p>
                      ) : canEditCompany ? (
                        <p className="text-slate-500 text-lg italic flex-1">
                          No description yet. Click the edit button to add one.
                        </p>
                      ) : null}
                      {canEditCompany && (
                        <button
                          type="button"
                          onClick={handleEditDescription}
                          className="p-2 text-slate-400 hover:text-gold-400 hover:bg-slate-700/50 rounded-lg transition-colors"
                          title="Edit description"
                        >
                          <svg
                            className="w-5 h-5"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                            />
                          </svg>
                        </button>
                      )}
                    </div>
                  )}
                </div>
                <div className="flex items-center gap-3">
                  {company.presentation_url && (
                    <Button
                      variant="secondary"
                      onClick={() =>
                        window.open(company.presentation_url!, "_blank")
                      }
                    >
                      <svg
                        className="w-4 h-4 mr-2"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"
                        />
                      </svg>
                      Presentation
                    </Button>
                  )}
                  {company.fact_sheet_url && (
                    <Button
                      variant="secondary"
                      onClick={() =>
                        window.open(company.fact_sheet_url!, "_blank")
                      }
                    >
                      <svg
                        className="w-4 h-4 mr-2"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                        />
                      </svg>
                      Fact Sheet
                    </Button>
                  )}
                  {company.technical_report_url && (
                    <Button
                      variant="secondary"
                      onClick={() =>
                        window.open(company.technical_report_url!, "_blank")
                      }
                    >
                      <svg
                        className="w-4 h-4 mr-2"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                        />
                      </svg>
                      Technical Report
                    </Button>
                  )}
                  {company.website && (
                    <Button
                      variant="primary"
                      onClick={() => window.open(company.website, "_blank")}
                    >
                      <svg
                        className="w-4 h-4 mr-2"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                        />
                      </svg>
                      Visit Website
                    </Button>
                  )}
                </div>
              </div>

              {/* Quick Stats - Now showing Stock Data */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-8">
                <Card variant="glass-card">
                  <CardContent className="py-4">
                    <div className="text-sm text-slate-400 mb-1">
                      Stock Price
                    </div>
                    {stockLoading ? (
                      <div className="text-2xl font-bold text-slate-500 animate-pulse">
                        ---
                      </div>
                    ) : stockQuote ? (
                      <div className="text-2xl font-bold text-gold-400">
                        ${stockQuote.price.toFixed(3)}
                      </div>
                    ) : (
                      <div className="text-2xl font-bold text-slate-500">
                        N/A
                      </div>
                    )}
                  </CardContent>
                </Card>
                <Card variant="glass-card">
                  <CardContent className="py-4">
                    <div className="text-sm text-slate-400 mb-1">Change</div>
                    {stockLoading ? (
                      <div className="text-2xl font-bold text-slate-500 animate-pulse">
                        ---
                      </div>
                    ) : stockQuote ? (
                      <div
                        className={`text-2xl font-bold ${stockQuote.change >= 0 ? "text-green-400" : "text-red-400"}`}
                      >
                        {stockQuote.change >= 0 ? "+" : ""}
                        {stockQuote.change_percent.toFixed(2)}%
                      </div>
                    ) : (
                      <div className="text-2xl font-bold text-slate-500">
                        N/A
                      </div>
                    )}
                  </CardContent>
                </Card>
                <Card variant="glass-card">
                  <CardContent className="py-4">
                    <div className="text-sm text-slate-400 mb-1">Volume</div>
                    {stockLoading ? (
                      <div className="text-2xl font-bold text-slate-500 animate-pulse">
                        ---
                      </div>
                    ) : stockQuote ? (
                      <div className="text-2xl font-bold text-white">
                        {stockQuote.volume.toLocaleString()}
                      </div>
                    ) : (
                      <div className="text-2xl font-bold text-slate-500">
                        N/A
                      </div>
                    )}
                  </CardContent>
                </Card>
                <Card variant="glass-card">
                  <CardContent className="py-4">
                    <div className="text-sm text-slate-400 mb-1">Status</div>
                    <div className="text-2xl font-bold text-green-400">
                      Active
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          </section>

          {/* Company Details Tabs */}
          <section className="py-12 px-4 sm:px-6 lg:px-8">
            <div className="max-w-7xl mx-auto">
              {/* Tab navigation — sticky below the global nav so users can
                  switch sections without scrolling back. Horizontally
                  scrollable on narrow screens. */}
              <div
                role="tablist"
                aria-label="Company sections"
                className="sticky top-16 z-30 -mx-4 sm:mx-0 mb-8 flex gap-1 overflow-x-auto bg-slate-900/85 backdrop-blur supports-[backdrop-filter]:bg-slate-900/70 border-b border-slate-800 px-4 sm:px-0 sm:rounded-xl sm:border sm:border-slate-800 sm:bg-slate-900/60 sm:p-1"
              >
                {(
                  [
                    { id: "overview", label: "Overview" },
                    { id: "events", label: "Events" },
                    { id: "news", label: "News" },
                    { id: "financings", label: "Financings" },
                    { id: "resources", label: "Resources" },
                    { id: "forum", label: "Community Forum" },
                  ] as { id: TabId; label: string }[]
                ).map((tab) => {
                  const isActive = activeTab === tab.id;
                  return (
                    <button
                      key={tab.id}
                      role="tab"
                      type="button"
                      {...{ "aria-selected": isActive }}
                      aria-controls={`tab-panel-${tab.id}`}
                      id={`tab-${tab.id}`}
                      onClick={() => setActiveTab(tab.id)}
                      className={`whitespace-nowrap px-4 py-2.5 text-sm font-medium rounded-lg transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-gold-400 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900 ${
                        isActive
                          ? "bg-gold-500/15 text-gold-300 border border-gold-500/40"
                          : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 border border-transparent"
                      }`}
                    >
                      {tab.label}
                      {tab.id === "forum" && (
                        <span
                          className="inline-block ml-2 w-2 h-2 rounded-full bg-green-400 motion-safe:animate-pulse align-middle"
                          aria-hidden="true"
                        />
                      )}
                    </button>
                  );
                })}
              </div>

              {/* Speaking Events & Active Financing — Events tab. The Events
                  tab pairs upcoming speaker events with currently-open
                  financing rounds (which have richer investment-interest
                  stats than the comprehensive list on the Financings tab). */}
              {activeTab === "events" && (
                <div
                  id="tab-panel-events"
                  role="tabpanel"
                  aria-labelledby="tab-events"
                  className="grid grid-cols-1 lg:grid-cols-[2fr_1fr] gap-6 mb-12"
                >
                  {/* Speaking Events - Left Column (wider) */}
                  <div className="min-w-0">
                    <EventBanner companyId={parseInt(companyId)} />
                  </div>

                  {/* Active Financing Rounds - Right Column */}
                  {(financings.filter(
                    (f) =>
                      f.status === "announced" ||
                      f.status === "closing" ||
                      f.status === "open",
                  ).length > 0 ||
                    isCompanyRep) && (
                    <div>
                      <div className="flex items-center justify-between mb-4">
                        <h3 className="text-lg font-semibold text-gold-400 flex items-center gap-2">
                          <svg
                            className="w-5 h-5"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                            />
                          </svg>
                          Financing Rounds
                        </h3>
                        {isCompanyRep && (
                          <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => setShowCreateFinancing(true)}
                          >
                            + New Financing
                          </Button>
                        )}
                      </div>
                      {financings.filter(
                        (f) =>
                          f.status === "announced" ||
                          f.status === "closing" ||
                          f.status === "open",
                      ).length > 0 ? (
                        <div className="space-y-4">
                          {financings
                            .filter(
                              (f) =>
                                f.status === "announced" ||
                                f.status === "closing" ||
                                f.status === "open",
                            )
                            .map((financing) => {
                              const aggregate =
                                interestAggregates[financing.id];
                              return (
                                <Card
                                  key={financing.id}
                                  variant="glass-card"
                                  className="border-gold-500/30 relative"
                                >
                                  <CardContent className="p-4">
                                    {/* Delete button for company reps */}
                                    {isCompanyRep && (
                                      <button
                                        type="button"
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          handleDeleteFinancing(financing.id);
                                        }}
                                        disabled={
                                          deletingFinancingId === financing.id
                                        }
                                        className="absolute top-2 right-2 p-1.5 rounded-full bg-red-900/50 text-red-400 hover:bg-red-800/70 hover:text-red-300 transition-colors z-10"
                                        title="Delete financing"
                                      >
                                        {deletingFinancingId ===
                                        financing.id ? (
                                          <svg
                                            className="w-4 h-4 animate-spin"
                                            fill="none"
                                            viewBox="0 0 24 24"
                                          >
                                            <circle
                                              className="opacity-25"
                                              cx="12"
                                              cy="12"
                                              r="10"
                                              stroke="currentColor"
                                              strokeWidth="4"
                                            ></circle>
                                            <path
                                              className="opacity-75"
                                              fill="currentColor"
                                              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                                            ></path>
                                          </svg>
                                        ) : (
                                          <svg
                                            className="w-4 h-4"
                                            fill="none"
                                            stroke="currentColor"
                                            viewBox="0 0 24 24"
                                          >
                                            <path
                                              strokeLinecap="round"
                                              strokeLinejoin="round"
                                              strokeWidth={2}
                                              d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                                            />
                                          </svg>
                                        )}
                                      </button>
                                    )}
                                    <div className="flex items-center justify-between mb-3">
                                      <Badge variant="gold">
                                        {financing.financing_type_display ||
                                          financing.financing_type}
                                      </Badge>
                                      <Badge
                                        variant="copper"
                                        className={isCompanyRep ? "mr-6" : ""}
                                      >
                                        {financing.status === "announced"
                                          ? "Open"
                                          : financing.status === "closing"
                                            ? "Closing Soon"
                                            : financing.status}
                                      </Badge>
                                    </div>

                                    {/* Investment Interest Stats */}
                                    {aggregate &&
                                    aggregate.total_interest_count > 0 ? (
                                      <div className="space-y-3">
                                        <div className="grid grid-cols-2 gap-3">
                                          <div className="text-center">
                                            <p className="text-2xl font-bold text-gold-400">
                                              {aggregate.total_interest_count}
                                            </p>
                                            <p className="text-xs text-slate-400">
                                              Interested Investors
                                            </p>
                                          </div>
                                          <div className="text-center">
                                            <p className="text-2xl font-bold text-white">
                                              $
                                              {Number(
                                                aggregate.total_amount_interested,
                                              ).toLocaleString()}
                                            </p>
                                            <p className="text-xs text-slate-400">
                                              Total Interest
                                            </p>
                                          </div>
                                        </div>

                                        {/* Progress bar */}
                                        <div>
                                          <div className="flex justify-between text-xs mb-1">
                                            <span className="text-slate-400">
                                              Interest Level
                                            </span>
                                            <span className="text-gold-400">
                                              {Number(
                                                aggregate.percentage_filled,
                                              ).toFixed(0)}
                                              %
                                            </span>
                                          </div>
                                          <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                                            <div
                                              className="h-full bg-gradient-to-r from-gold-500 to-copper-500 rounded-full"
                                              style={{
                                                width: `${Math.min(Number(aggregate.percentage_filled), 100)}%`,
                                              }}
                                            ></div>
                                          </div>
                                        </div>
                                      </div>
                                    ) : (
                                      <p className="text-sm text-slate-400 text-center py-2">
                                        No interests registered yet
                                      </p>
                                    )}

                                    <Button
                                      variant="primary"
                                      size="sm"
                                      className="w-full mt-4"
                                      onClick={() =>
                                        (window.location.href = `/companies/${companyId}/financing`)
                                      }
                                    >
                                      View Financing Details
                                    </Button>
                                  </CardContent>
                                </Card>
                              );
                            })}
                        </div>
                      ) : (
                        <Card variant="glass-card" className="border-slate-700">
                          <CardContent className="p-6 text-center">
                            <svg
                              className="w-12 h-12 text-slate-600 mx-auto mb-3"
                              fill="none"
                              stroke="currentColor"
                              viewBox="0 0 24 24"
                            >
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={1.5}
                                d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                              />
                            </svg>
                            <p className="text-slate-400 text-sm mb-3">
                              No active financing rounds
                            </p>
                            {isCompanyRep && (
                              <Button
                                variant="primary"
                                size="sm"
                                onClick={() => setShowCreateFinancing(true)}
                              >
                                Create Private Placement
                              </Button>
                            )}
                          </CardContent>
                        </Card>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* Projects Section — Overview tab */}
              {activeTab === "overview" && (
                <div
                  id="tab-panel-overview"
                  role="tabpanel"
                  aria-labelledby="tab-overview"
                  className="mb-12"
                >
                  <div className="flex items-center justify-between mb-6">
                    <div>
                      <h2 className="text-3xl font-bold text-gold-400 mb-2">
                        Projects
                      </h2>
                      <p className="text-slate-400">
                        Active mining projects and exploration sites
                      </p>
                    </div>
                    {canEditCompany && (
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => setShowAddProject(true)}
                      >
                        + Add Project
                      </Button>
                    )}
                  </div>

                  {/* Add Project Form */}
                  {showAddProject && canEditCompany && (
                    <Card variant="glass-card" className="mb-6">
                      <CardHeader>
                        <CardTitle className="text-xl text-gold-400">
                          Add New Project
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-4">
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                              <label className="block text-sm text-slate-400 mb-1">
                                Project Name *
                              </label>
                              <input
                                type="text"
                                value={newProject.name}
                                onChange={(e) =>
                                  setNewProject({
                                    ...newProject,
                                    name: e.target.value,
                                  })
                                }
                                className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-gold-400"
                                placeholder="e.g., Gold Mountain Project"
                              />
                            </div>
                            <div>
                              <label className="block text-sm text-slate-400 mb-1">
                                Country *
                              </label>
                              <input
                                type="text"
                                value={newProject.country}
                                onChange={(e) =>
                                  setNewProject({
                                    ...newProject,
                                    country: e.target.value,
                                  })
                                }
                                className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-gold-400"
                                placeholder="e.g., Canada"
                              />
                            </div>
                            <div>
                              <label className="block text-sm text-slate-400 mb-1">
                                Province/State
                              </label>
                              <input
                                type="text"
                                value={newProject.province_state}
                                onChange={(e) =>
                                  setNewProject({
                                    ...newProject,
                                    province_state: e.target.value,
                                  })
                                }
                                className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-gold-400"
                                placeholder="e.g., Ontario"
                              />
                            </div>
                            <div>
                              <label
                                htmlFor="primary_commodity"
                                className="block text-sm text-slate-400 mb-1"
                              >
                                Primary Commodity *
                              </label>
                              <select
                                id="primary_commodity"
                                title="Primary Commodity"
                                value={newProject.primary_commodity}
                                onChange={(e) =>
                                  setNewProject({
                                    ...newProject,
                                    primary_commodity: e.target.value,
                                  })
                                }
                                className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-gold-400"
                              >
                                <option value="gold">Gold</option>
                                <option value="silver">Silver</option>
                                <option value="copper">Copper</option>
                                <option value="lithium">Lithium</option>
                                <option value="nickel">Nickel</option>
                                <option value="cobalt">Cobalt</option>
                                <option value="rare_earths">
                                  Rare Earth Elements
                                </option>
                                <option value="zinc">Zinc</option>
                                <option value="uranium">Uranium</option>
                                <option value="multi_metal">Multi-Metal</option>
                                <option value="other">Other</option>
                              </select>
                            </div>
                            <div>
                              <label
                                htmlFor="project_stage"
                                className="block text-sm text-slate-400 mb-1"
                              >
                                Project Stage *
                              </label>
                              <select
                                id="project_stage"
                                title="Project Stage"
                                value={newProject.project_stage}
                                onChange={(e) =>
                                  setNewProject({
                                    ...newProject,
                                    project_stage: e.target.value,
                                  })
                                }
                                className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-gold-400"
                              >
                                <option value="grassroots">
                                  Grassroots Exploration
                                </option>
                                <option value="early_exploration">
                                  Early Stage Exploration
                                </option>
                                <option value="advanced_exploration">
                                  Advanced Exploration
                                </option>
                                <option value="resource">Resource Stage</option>
                                <option value="pea">PEA Completed</option>
                                <option value="pfs">PFS Completed</option>
                                <option value="fs">Feasibility Study</option>
                                <option value="permitting">Permitting</option>
                                <option value="development">Development</option>
                                <option value="production">Production</option>
                              </select>
                            </div>
                          </div>
                          <div>
                            <label className="block text-sm text-slate-400 mb-1">
                              Description
                            </label>
                            <textarea
                              value={newProject.description}
                              onChange={(e) =>
                                setNewProject({
                                  ...newProject,
                                  description: e.target.value,
                                })
                              }
                              className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-gold-400 h-24"
                              placeholder="Brief description of the project..."
                            />
                          </div>
                          {projectError && (
                            <div className="text-red-400 text-sm">
                              {projectError}
                            </div>
                          )}
                          <div className="flex gap-2">
                            <Button
                              variant="primary"
                              size="sm"
                              onClick={handleAddProject}
                              disabled={
                                savingProject ||
                                !newProject.name ||
                                !newProject.country
                              }
                            >
                              {savingProject ? "Adding..." : "Add Project"}
                            </Button>
                            <Button
                              variant="secondary"
                              size="sm"
                              onClick={() => {
                                setShowAddProject(false);
                                setProjectError(null);
                              }}
                            >
                              Cancel
                            </Button>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  )}

                  {projects.length > 0 ? (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                      {projects.map((project) => (
                        <Card
                          key={project.id}
                          variant="glass-card"
                          className="hover:scale-105 transition-transform relative"
                        >
                          {/* Edit and Delete buttons for admins */}
                          {canEditCompany && (
                            <div className="absolute top-3 right-3 flex gap-2 z-20">
                              <button
                                type="button"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleEditProject(project);
                                }}
                                className="p-2 bg-gold-500/30 hover:bg-gold-500/50 rounded-lg text-gold-400 hover:text-gold-300 transition-colors"
                                title="Edit project"
                              >
                                <svg
                                  className="w-4 h-4"
                                  fill="none"
                                  stroke="currentColor"
                                  viewBox="0 0 24 24"
                                >
                                  <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth={2}
                                    d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                                  />
                                </svg>
                              </button>
                              <button
                                type="button"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleDeleteProject(project.id);
                                }}
                                disabled={deletingProjectId === project.id}
                                className="p-2 bg-red-500/30 hover:bg-red-500/50 rounded-lg text-red-400 hover:text-red-300 transition-colors"
                                title="Delete project"
                              >
                                {deletingProjectId === project.id ? (
                                  <svg
                                    className="w-4 h-4 animate-spin"
                                    fill="none"
                                    viewBox="0 0 24 24"
                                  >
                                    <circle
                                      className="opacity-25"
                                      cx="12"
                                      cy="12"
                                      r="10"
                                      stroke="currentColor"
                                      strokeWidth="4"
                                    ></circle>
                                    <path
                                      className="opacity-75"
                                      fill="currentColor"
                                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                                    ></path>
                                  </svg>
                                ) : (
                                  <svg
                                    className="w-4 h-4"
                                    fill="none"
                                    stroke="currentColor"
                                    viewBox="0 0 24 24"
                                  >
                                    <path
                                      strokeLinecap="round"
                                      strokeLinejoin="round"
                                      strokeWidth={2}
                                      d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                                    />
                                  </svg>
                                )}
                              </button>
                            </div>
                          )}
                          <CardHeader>
                            <div className="flex items-start justify-between mb-2">
                              <CardTitle className="text-xl text-gold-400">
                                {project.name}
                              </CardTitle>
                              {project.is_flagship && (
                                <Badge variant="gold">Flagship</Badge>
                              )}
                            </div>
                            {(project.country || project.province_state) && (
                              <div className="flex items-center gap-2 text-sm text-slate-400 mb-2">
                                <svg
                                  className="w-4 h-4"
                                  fill="none"
                                  stroke="currentColor"
                                  viewBox="0 0 24 24"
                                >
                                  <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth={2}
                                    d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
                                  />
                                  <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth={2}
                                    d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
                                  />
                                </svg>
                                <span>
                                  {[project.province_state, project.country]
                                    .filter(Boolean)
                                    .join(", ")}
                                </span>
                              </div>
                            )}
                            <CardDescription className="line-clamp-2">
                              {project.description ||
                                "Gold exploration and development project"}
                            </CardDescription>
                          </CardHeader>
                          <CardContent>
                            <div className="space-y-3">
                              <div className="flex items-center justify-between text-sm">
                                <span className="text-slate-400">
                                  Primary Commodity
                                </span>
                                <span className="text-white font-semibold">
                                  {project.primary_commodity || "Gold"}
                                </span>
                              </div>
                              {project.project_stage && (
                                <div className="flex items-center justify-between text-sm">
                                  <span className="text-slate-400">Stage</span>
                                  <Badge variant="copper">
                                    {project.project_stage}
                                  </Badge>
                                </div>
                              )}
                              {project.total_resources_oz && (
                                <div className="pt-3 border-t border-slate-700">
                                  <div className="text-xs text-slate-400 mb-1">
                                    Total Resources
                                  </div>
                                  <div className="text-lg font-bold text-gold-400">
                                    {formatNumber(project.total_resources_oz)}{" "}
                                    oz Au
                                  </div>
                                </div>
                              )}
                            </div>
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  ) : (
                    <Card variant="glass-card">
                      <CardContent className="py-12 text-center">
                        <div className="text-slate-400">
                          No projects data available
                        </div>
                      </CardContent>
                    </Card>
                  )}
                </div>
              )}

              {/* Resources & Documents Section — Resources tab */}
              {activeTab === "resources" && (
                <div
                  id="tab-panel-resources"
                  role="tabpanel"
                  aria-labelledby="tab-resources"
                  className="mb-12"
                >
                  <div className="flex items-center justify-between mb-6">
                    <div>
                      <h2 className="text-3xl font-bold text-gold-400 mb-2">
                        Resources & Documents
                      </h2>
                      <p className="text-slate-400">
                        Investor presentations, technical reports, and company
                        documents
                      </p>
                    </div>
                    {isCompanyRep && (
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => setShowResourceUpload(true)}
                      >
                        + Add Resource
                      </Button>
                    )}
                  </div>

                  {resourcesLoading ? (
                    <Card variant="glass-card">
                      <CardContent className="py-12 text-center">
                        <div className="text-slate-400">
                          Loading resources...
                        </div>
                      </CardContent>
                    </Card>
                  ) : companyResources.length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {companyResources.map((resource) => (
                        <div key={resource.id} className="group relative">
                          <a
                            href={
                              resource.file_url || resource.external_url || "#"
                            }
                            target="_blank"
                            rel="noopener noreferrer"
                          >
                            <Card
                              variant="glass-card"
                              className="h-full hover:border-gold-500/50 transition-colors"
                            >
                              <CardContent className="p-4">
                                <div className="flex items-start gap-3">
                                  <div className="w-10 h-10 rounded-lg bg-slate-700 flex items-center justify-center flex-shrink-0">
                                    {resource.resource_type === "document" ||
                                    resource.category === "technical_report" ? (
                                      <svg
                                        className="w-5 h-5 text-gold-500"
                                        fill="none"
                                        viewBox="0 0 24 24"
                                        stroke="currentColor"
                                      >
                                        <path
                                          strokeLinecap="round"
                                          strokeLinejoin="round"
                                          strokeWidth={2}
                                          d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                                        />
                                      </svg>
                                    ) : resource.resource_type ===
                                        "presentation" ||
                                      resource.category ===
                                        "investor_presentation" ? (
                                      <svg
                                        className="w-5 h-5 text-gold-500"
                                        fill="none"
                                        viewBox="0 0 24 24"
                                        stroke="currentColor"
                                      >
                                        <path
                                          strokeLinecap="round"
                                          strokeLinejoin="round"
                                          strokeWidth={2}
                                          d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"
                                        />
                                      </svg>
                                    ) : resource.category === "map" ? (
                                      <svg
                                        className="w-5 h-5 text-gold-500"
                                        fill="none"
                                        viewBox="0 0 24 24"
                                        stroke="currentColor"
                                      >
                                        <path
                                          strokeLinecap="round"
                                          strokeLinejoin="round"
                                          strokeWidth={2}
                                          d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"
                                        />
                                      </svg>
                                    ) : resource.resource_type === "image" ? (
                                      <svg
                                        className="w-5 h-5 text-gold-500"
                                        fill="none"
                                        viewBox="0 0 24 24"
                                        stroke="currentColor"
                                      >
                                        <path
                                          strokeLinecap="round"
                                          strokeLinejoin="round"
                                          strokeWidth={2}
                                          d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                                        />
                                      </svg>
                                    ) : (
                                      <svg
                                        className="w-5 h-5 text-gold-500"
                                        fill="none"
                                        viewBox="0 0 24 24"
                                        stroke="currentColor"
                                      >
                                        <path
                                          strokeLinecap="round"
                                          strokeLinejoin="round"
                                          strokeWidth={2}
                                          d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                                        />
                                      </svg>
                                    )}
                                  </div>
                                  <div className="flex-1 min-w-0">
                                    <p className="text-white font-medium truncate group-hover:text-gold-400 transition-colors">
                                      {resource.title}
                                    </p>
                                    {resource.description && (
                                      <p className="text-sm text-slate-400 truncate">
                                        {resource.description}
                                      </p>
                                    )}
                                    <div className="flex items-center gap-2 mt-1">
                                      <Badge
                                        variant="slate"
                                        className="text-xs"
                                      >
                                        {resource.category.replace(/_/g, " ")}
                                      </Badge>
                                      {resource.file_format && (
                                        <span className="text-xs text-slate-500">
                                          {resource.file_format.toUpperCase()}
                                        </span>
                                      )}
                                    </div>
                                  </div>
                                  <svg
                                    className="w-5 h-5 text-slate-500 group-hover:text-gold-400 transition-colors flex-shrink-0"
                                    fill="none"
                                    viewBox="0 0 24 24"
                                    stroke="currentColor"
                                  >
                                    <path
                                      strokeLinecap="round"
                                      strokeLinejoin="round"
                                      strokeWidth={2}
                                      d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                                    />
                                  </svg>
                                </div>
                              </CardContent>
                            </Card>
                          </a>
                          {isCompanyRep && (
                            <button
                              type="button"
                              onClick={(e) => {
                                e.preventDefault();
                                e.stopPropagation();
                                handleDeleteResource(resource.id);
                              }}
                              disabled={deletingResourceId === resource.id}
                              className="absolute top-2 left-2 p-1.5 bg-red-500/80 hover:bg-red-500 text-white rounded-lg transition-all disabled:opacity-50 z-10"
                              title="Delete resource"
                            >
                              {deletingResourceId === resource.id ? (
                                <svg
                                  className="w-4 h-4 animate-spin"
                                  fill="none"
                                  viewBox="0 0 24 24"
                                >
                                  <circle
                                    className="opacity-25"
                                    cx="12"
                                    cy="12"
                                    r="10"
                                    stroke="currentColor"
                                    strokeWidth="4"
                                  ></circle>
                                  <path
                                    className="opacity-75"
                                    fill="currentColor"
                                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                                  ></path>
                                </svg>
                              ) : (
                                <svg
                                  className="w-4 h-4"
                                  fill="none"
                                  viewBox="0 0 24 24"
                                  stroke="currentColor"
                                >
                                  <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth={2}
                                    d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                                  />
                                </svg>
                              )}
                            </button>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <Card variant="glass-card">
                      <CardContent className="py-12 text-center">
                        <svg
                          className="mx-auto w-12 h-12 text-slate-600 mb-3"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={1.5}
                            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                          />
                        </svg>
                        <p className="text-slate-400 mb-2">
                          No resources uploaded yet
                        </p>
                        {isCompanyRep && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setShowResourceUpload(true)}
                          >
                            Upload your first resource
                          </Button>
                        )}
                      </CardContent>
                    </Card>
                  )}
                </div>
              )}

              {/* Company Representative Registration Section — Overview tab */}
              {activeTab === "overview" && !isCompanyRep && (
                <div className="mb-12">
                  <Card variant="glass-card" className="border-gold-500/30">
                    <CardContent className="p-6">
                      <div className="flex items-start gap-6">
                        <div className="w-16 h-16 bg-gradient-to-br from-gold-500/20 to-copper-500/20 rounded-lg flex items-center justify-center flex-shrink-0">
                          <svg
                            className="w-8 h-8 text-gold-400"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
                            />
                          </svg>
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <h3 className="text-xl font-bold text-white">
                              Are you a company representative?
                            </h3>
                            <Badge variant="gold" className="animate-pulse">
                              Limited Time: $50/mo
                            </Badge>
                          </div>
                          <p className="text-slate-400 mb-3">
                            If you work for {company.name}, register as a
                            company representative to access premium features:
                          </p>
                          <ul className="text-sm text-slate-300 mb-3 space-y-1">
                            <li className="flex items-center gap-2">
                              <svg
                                className="w-4 h-4 text-green-400 flex-shrink-0"
                                fill="none"
                                viewBox="0 0 24 24"
                                stroke="currentColor"
                              >
                                <path
                                  strokeLinecap="round"
                                  strokeLinejoin="round"
                                  strokeWidth={2}
                                  d="M5 13l4 4L19 7"
                                />
                              </svg>
                              Upload investor presentations, technical reports &
                              documents
                            </li>
                            <li className="flex items-center gap-2">
                              <svg
                                className="w-4 h-4 text-green-400 flex-shrink-0"
                                fill="none"
                                viewBox="0 0 24 24"
                                stroke="currentColor"
                              >
                                <path
                                  strokeLinecap="round"
                                  strokeLinejoin="round"
                                  strokeWidth={2}
                                  d="M5 13l4 4L19 7"
                                />
                              </svg>
                              Create & schedule live speaking events, webinars &
                              investor days
                            </li>
                            <li className="flex items-center gap-2">
                              <svg
                                className="w-4 h-4 text-green-400 flex-shrink-0"
                                fill="none"
                                viewBox="0 0 24 24"
                                stroke="currentColor"
                              >
                                <path
                                  strokeLinecap="round"
                                  strokeLinejoin="round"
                                  strokeWidth={2}
                                  d="M5 13l4 4L19 7"
                                />
                              </svg>
                              Manage financing rounds & track investor interest
                            </li>
                          </ul>
                          <p className="text-sm text-gold-400 mb-4">
                            Start with a 30-day FREE trial. No credit card
                            required.
                          </p>
                          {pendingRequest ? (
                            <div className="flex items-center gap-3 p-3 bg-gold-500/10 border border-gold-500/30 rounded-lg">
                              <svg
                                className="w-5 h-5 text-gold-400 flex-shrink-0"
                                fill="none"
                                viewBox="0 0 24 24"
                                stroke="currentColor"
                              >
                                <path
                                  strokeLinecap="round"
                                  strokeLinejoin="round"
                                  strokeWidth={2}
                                  d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                                />
                              </svg>
                              <div>
                                <p className="text-gold-400 font-medium">
                                  Request Pending
                                </p>
                                <p className="text-sm text-slate-400">
                                  Your request to represent this company is
                                  under review. We'll notify you when it's
                                  processed.
                                </p>
                              </div>
                            </div>
                          ) : user ? (
                            <Button
                              variant="primary"
                              onClick={() => setShowRepRegistration(true)}
                            >
                              <svg
                                className="w-4 h-4 mr-2"
                                fill="none"
                                viewBox="0 0 24 24"
                                stroke="currentColor"
                              >
                                <path
                                  strokeLinecap="round"
                                  strokeLinejoin="round"
                                  strokeWidth={2}
                                  d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z"
                                />
                              </svg>
                              Register as Company Representative
                            </Button>
                          ) : (
                            <Button
                              variant="primary"
                              onClick={() => setShowLogin(true)}
                            >
                              <svg
                                className="w-4 h-4 mr-2"
                                fill="none"
                                viewBox="0 0 24 24"
                                stroke="currentColor"
                              >
                                <path
                                  strokeLinecap="round"
                                  strokeLinejoin="round"
                                  strokeWidth={2}
                                  d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1"
                                />
                              </svg>
                              Sign In to Register as Representative
                            </Button>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              )}

              {/* Community Forum Section — Forum tab. Visually distinct from
                  the data sections; the gradient border + glow cue "this is a
                  people section, not another table." */}
              {activeTab === "forum" && (
                <section
                  id="community-forum"
                  role="tabpanel"
                  aria-labelledby="community-forum-heading"
                  className="mb-12 scroll-mt-24 relative rounded-2xl border border-gold-500/30 bg-gradient-to-br from-slate-800/60 to-slate-900/80 p-6 md:p-8 shadow-[0_0_40px_-15px_rgba(212,175,55,0.4)]"
                >
                  <div className="mb-6 flex items-start justify-between gap-4 flex-wrap">
                    <div className="flex items-start gap-4">
                      <div
                        className="w-12 h-12 rounded-xl bg-gold-500/15 border border-gold-500/30 flex items-center justify-center flex-shrink-0"
                        aria-hidden="true"
                      >
                        <svg
                          className="w-6 h-6 text-gold-400"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                          />
                        </svg>
                      </div>
                      <div>
                        <h2
                          id="community-forum-heading"
                          className="text-3xl font-bold text-gold-400 mb-1"
                        >
                          Community Forum
                        </h2>
                        <p className="text-slate-400">
                          Real-time discussion with investors and analysts
                          following {company.name}
                        </p>
                      </div>
                    </div>
                    <span
                      className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-green-500/10 border border-green-500/30 text-xs font-semibold text-green-300 uppercase tracking-wide"
                      aria-label="Live discussion"
                    >
                      <span
                        className="w-2 h-2 rounded-full bg-green-400 motion-safe:animate-pulse"
                        aria-hidden="true"
                      />
                      Live
                    </span>
                  </div>

                  <CompanyForum
                    companyId={parseInt(companyId)}
                    companyName={company.name}
                  />
                </section>
              )}

              {/* News Releases Section — News tab */}
              {activeTab === "news" && (
                <div
                  id="tab-panel-news"
                  role="tabpanel"
                  aria-labelledby="tab-news"
                  className="mb-12"
                >
                  <div className="mb-6 flex items-center justify-between">
                    <div>
                      <h2 className="text-3xl font-bold text-gold-400 mb-2">
                        Company News Releases
                      </h2>
                      <p className="text-slate-400">
                        Recent updates and announcements from {company.name}
                      </p>
                      {newsData?.last_updated && (
                        <p className="text-xs text-slate-500 mt-1">
                          Last updated:{" "}
                          {new Date(newsData.last_updated).toLocaleString()}
                        </p>
                      )}
                      {scrapeError && (
                        <p className="text-xs text-red-400 mt-2 flex items-center gap-1">
                          <svg
                            className="w-4 h-4"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                            />
                          </svg>
                          {scrapeError}
                        </p>
                      )}
                    </div>
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={handleScrapeNews}
                      disabled={scrapingNews || !company.website}
                    >
                      {scrapingNews ? (
                        <>
                          <svg
                            className="animate-spin -ml-1 mr-2 h-4 w-4"
                            fill="none"
                            viewBox="0 0 24 24"
                          >
                            <circle
                              className="opacity-25"
                              cx="12"
                              cy="12"
                              r="10"
                              stroke="currentColor"
                              strokeWidth="4"
                            ></circle>
                            <path
                              className="opacity-75"
                              fill="currentColor"
                              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                            ></path>
                          </svg>
                          Updating...
                        </>
                      ) : (
                        <>
                          <svg
                            className="w-4 h-4 mr-2"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                            />
                          </svg>
                          Update News
                        </>
                      )}
                    </Button>
                  </div>

                  {newsLoading ? (
                    <Card variant="glass-card">
                      <CardContent className="py-12 text-center">
                        <div className="text-slate-400">
                          Loading news releases...
                        </div>
                      </CardContent>
                    </Card>
                  ) : (
                    <div className="space-y-8">
                      {/* Financial News Section */}
                      <div>
                        <h3 className="text-xl font-bold text-copper-400 mb-4 flex items-center gap-2">
                          <svg
                            className="w-5 h-5"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z"
                            />
                          </svg>
                          Financial News
                        </h3>
                        {newsData?.financial &&
                        newsData.financial.length > 0 ? (
                          <div className="grid grid-cols-1 gap-4">
                            {newsData.financial.map((release) => (
                              <Card key={release.id} variant="glass-card">
                                <CardHeader>
                                  <div className="flex items-start justify-between">
                                    <CardTitle className="text-lg text-white">
                                      {release.title}
                                    </CardTitle>
                                    <Badge variant="gold">Financial</Badge>
                                  </div>
                                  {release.release_date && (
                                    <div className="text-sm text-slate-400 mt-1">
                                      {new Date(
                                        release.release_date + "T00:00:00",
                                      ).toLocaleDateString("en-US", {
                                        year: "numeric",
                                        month: "long",
                                        day: "numeric",
                                      })}
                                    </div>
                                  )}
                                </CardHeader>
                                <CardContent>
                                  <p className="text-slate-300 text-sm mb-3">
                                    {release.summary}
                                  </p>
                                  {release.url && (
                                    <a
                                      href={release.url}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="text-gold-400 hover:text-gold-300 text-sm flex items-center gap-1"
                                    >
                                      <span>Read Full Release</span>
                                      <svg
                                        className="w-3 h-3"
                                        fill="none"
                                        stroke="currentColor"
                                        viewBox="0 0 24 24"
                                      >
                                        <path
                                          strokeLinecap="round"
                                          strokeLinejoin="round"
                                          strokeWidth={2}
                                          d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                                        />
                                      </svg>
                                    </a>
                                  )}
                                </CardContent>
                              </Card>
                            ))}
                          </div>
                        ) : (
                          <Card variant="glass-card">
                            <CardContent className="py-8 text-center">
                              <div className="text-slate-400 text-sm">
                                No financial news releases available
                              </div>
                            </CardContent>
                          </Card>
                        )}
                      </div>

                      {/* Non-Financial News Section */}
                      <div>
                        <h3 className="text-xl font-bold text-copper-400 mb-4 flex items-center gap-2">
                          <svg
                            className="w-5 h-5"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z"
                            />
                          </svg>
                          Company Updates
                        </h3>
                        {newsData?.non_financial &&
                        newsData.non_financial.length > 0 ? (
                          <div className="grid grid-cols-1 gap-4">
                            {newsData.non_financial.map((release) => (
                              <Card key={release.id} variant="glass-card">
                                <CardHeader>
                                  <div className="flex items-start justify-between">
                                    <CardTitle className="text-lg text-white">
                                      {release.title}
                                    </CardTitle>
                                    <Badge variant="copper">
                                      {release.release_type.replace(/_/g, " ")}
                                    </Badge>
                                  </div>
                                  {release.release_date && (
                                    <div className="text-sm text-slate-400 mt-1">
                                      {new Date(
                                        release.release_date + "T00:00:00",
                                      ).toLocaleDateString("en-US", {
                                        year: "numeric",
                                        month: "long",
                                        day: "numeric",
                                      })}
                                    </div>
                                  )}
                                </CardHeader>
                                <CardContent>
                                  <p className="text-slate-300 text-sm mb-3">
                                    {release.summary}
                                  </p>
                                  {release.url && (
                                    <a
                                      href={release.url}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="text-gold-400 hover:text-gold-300 text-sm flex items-center gap-1"
                                    >
                                      <span>Read Full Release</span>
                                      <svg
                                        className="w-3 h-3"
                                        fill="none"
                                        stroke="currentColor"
                                        viewBox="0 0 24 24"
                                      >
                                        <path
                                          strokeLinecap="round"
                                          strokeLinejoin="round"
                                          strokeWidth={2}
                                          d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                                        />
                                      </svg>
                                    </a>
                                  )}
                                </CardContent>
                              </Card>
                            ))}
                          </div>
                        ) : (
                          <Card variant="glass-card">
                            <CardContent className="py-8 text-center">
                              <div className="text-slate-400 text-sm">
                                No company updates available
                              </div>
                            </CardContent>
                          </Card>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Financings Section — Financings tab. Renders the full
                  financings list from the already-fetched `financings` state
                  so no extra round-trip is needed when switching tabs. */}
              {activeTab === "financings" && (
                <div
                  id="tab-panel-financings"
                  role="tabpanel"
                  aria-labelledby="tab-financings"
                  className="mb-12"
                >
                  <div className="mb-6">
                    <h2 className="text-3xl font-bold text-gold-400 mb-2">
                      Financings
                    </h2>
                    <p className="text-slate-400">
                      All capital raises for {company.name} — open and closed
                    </p>
                  </div>

                  {financings.length === 0 ? (
                    <Card variant="glass-card">
                      <CardContent className="p-8 text-center text-slate-400">
                        No financing rounds recorded yet for this company.
                      </CardContent>
                    </Card>
                  ) : (
                    <div className="space-y-3">
                      {financings.map((f) => {
                        const isOpen = !f.is_closed;
                        return (
                          <Card
                            key={f.id}
                            variant="glass-card"
                            className={
                              isOpen
                                ? "border-gold-500/30"
                                : "border-slate-700/50"
                            }
                          >
                            <CardContent className="p-5">
                              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                                <div className="flex items-center gap-3 flex-wrap">
                                  <Badge
                                    variant={isOpen ? "gold" : "slate"}
                                    className="text-xs"
                                  >
                                    {isOpen ? "Open" : "Closed"}
                                  </Badge>
                                  <span className="text-sm font-medium text-slate-200">
                                    {f.financing_type_display ||
                                      f.financing_type}
                                  </span>
                                  {f.announced_date && (
                                    <span className="text-xs text-slate-500">
                                      Announced{" "}
                                      {new Date(
                                        f.announced_date,
                                      ).toLocaleDateString("en-US", {
                                        month: "short",
                                        day: "numeric",
                                        year: "numeric",
                                      })}
                                    </span>
                                  )}
                                  {f.closing_date && (
                                    <span className="text-xs text-slate-500">
                                      · {isOpen ? "Closes" : "Closed"}{" "}
                                      {new Date(
                                        f.closing_date,
                                      ).toLocaleDateString("en-US", {
                                        month: "short",
                                        day: "numeric",
                                        year: "numeric",
                                      })}
                                    </span>
                                  )}
                                </div>
                                <div className="flex items-center gap-3">
                                  {f.amount_raised_usd && (
                                    <span className="text-lg font-bold text-gold-400">
                                      {new Intl.NumberFormat("en-CA", {
                                        style: "currency",
                                        currency: "CAD",
                                        minimumFractionDigits: 0,
                                        maximumFractionDigits: 0,
                                      }).format(Number(f.amount_raised_usd))}
                                    </span>
                                  )}
                                  {f.press_release_url && (
                                    <a
                                      href={f.press_release_url}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="text-xs text-gold-400 hover:text-gold-300 hover:underline"
                                    >
                                      Press release →
                                    </a>
                                  )}
                                </div>
                              </div>
                              {f.use_of_proceeds && (
                                <p className="text-sm text-slate-400 mt-3">
                                  {f.use_of_proceeds}
                                </p>
                              )}
                            </CardContent>
                          </Card>
                        );
                      })}
                    </div>
                  )}
                </div>
              )}
            </div>
          </section>
        </>
      ) : null}

      {/* Company Chatbot */}
      {company && (
        <CompanyChatbot
          companyId={parseInt(companyId)}
          companyName={company.name}
        />
      )}

      {/* Persistent jump-to-forum FAB. Sits opposite the chatbot FAB to avoid
          collision, and hides itself when the user is already on the Forum
          tab. */}
      {company && (
        <FloatingForumButton
          onClick={jumpToForum}
          hidden={activeTab === "forum"}
        />
      )}
    </div>
  );
}
