import SiteHeader from "@/components/SiteHeader";

export default function CompanyDetailLoading() {
  return (
    <div className="min-h-screen">
      <SiteHeader active="/companies" />

      <section className="relative py-12 px-4 sm:px-6 lg:px-8 bg-gradient-slate">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center gap-4 mb-6">
            <div className="w-16 h-16 rounded-lg bg-slate-700 animate-pulse" />
            <div>
              <div className="h-8 w-64 bg-slate-700 rounded animate-pulse mb-2" />
              <div className="h-5 w-32 bg-slate-700 rounded animate-pulse" />
            </div>
          </div>
          <div className="h-20 w-full max-w-3xl bg-slate-700 rounded animate-pulse mb-8" />
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-8">
            {Array.from({ length: 4 }).map((_, i) => (
              <div
                key={i}
                className="h-24 bg-slate-800/50 border border-slate-700 rounded-xl animate-pulse"
              />
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
