import { ImageResponse } from "next/og";
import { parseCompanyIdParam } from "@/lib/companyUrl";

export const runtime = "nodejs";
export const revalidate = 3600;

const API_BASE_URL =
  process.env.API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000/api";

const FALLBACK_BG =
  "linear-gradient(135deg, #0f172a 0%, #1e293b 60%, #312e2b 100%)";

export async function GET(
  _request: Request,
  context: { params: Promise<{ id: string }> },
) {
  const { id: rawSegment } = await context.params;
  const numericId = parseCompanyIdParam(rawSegment);

  let company: any = null;
  if (numericId !== null) {
    try {
      const res = await fetch(`${API_BASE_URL}/companies/${numericId}/`, {
        next: { revalidate: 3600 },
      });
      if (res.ok) company = await res.json();
    } catch {
      // fall through to generic
    }
  }

  const name = company?.name || "Junior Mining Intelligence";
  const tickerLine = company
    ? `${(company.exchange || "").toUpperCase()}${company.ticker_symbol ? `: ${company.ticker_symbol}` : ""}`.trim()
    : "AI-Powered Mining Intelligence";
  const commodity =
    Array.isArray(company?.projects) && company.projects.length
      ? `${(company.projects[0].primary_commodity || "Mineral").toString().toUpperCase()} EXPLORATION`
      : "JUNIOR MINING";

  return new ImageResponse(
    <div
      style={{
        height: "100%",
        width: "100%",
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
        background: FALLBACK_BG,
        padding: "80px",
        fontFamily: "sans-serif",
        color: "white",
      }}
    >
      <div
        style={{
          fontSize: 28,
          letterSpacing: 8,
          color: "#D4AF37",
          fontWeight: 600,
        }}
      >
        {commodity}
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
        <div
          style={{
            fontSize: 80,
            fontWeight: 800,
            lineHeight: 1.05,
            maxWidth: "1040px",
          }}
        >
          {name}
        </div>
        {tickerLine && (
          <div style={{ fontSize: 40, color: "#D4AF37" }}>{tickerLine}</div>
        )}
      </div>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          fontSize: 28,
          color: "#94a3b8",
        }}
      >
        <span>juniorminingintelligence.com</span>
        <span style={{ color: "#D4AF37" }}>JMI</span>
      </div>
    </div>,
    { width: 1200, height: 630 },
  );
}
