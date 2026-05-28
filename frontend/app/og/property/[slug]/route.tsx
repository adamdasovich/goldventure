import { ImageResponse } from "next/og";

export const runtime = "nodejs";
export const revalidate = 3600;

const API_BASE_URL =
  process.env.API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000/api";

const FALLBACK_BG =
  "linear-gradient(135deg, #0c1a14 0%, #1c2e1f 60%, #2a2316 100%)";

export async function GET(
  _request: Request,
  context: { params: Promise<{ slug: string }> },
) {
  const { slug } = await context.params;

  let property: any = null;
  try {
    const res = await fetch(`${API_BASE_URL}/properties/listings/${slug}/`, {
      next: { revalidate: 1800 },
    });
    if (res.ok) property = await res.json();
  } catch {
    // fall through to generic
  }

  const title = property?.title || "Prospector's Exchange";
  const location = property
    ? [property.province_state, property.country_display]
        .filter(Boolean)
        .join(", ")
    : "Junior Mining Intelligence";
  const mineral = property?.primary_mineral_display || "Mineral Exploration";
  const hectares = property?.total_hectares
    ? `${Number(property.total_hectares).toLocaleString()} hectares`
    : "";
  const listingType = property?.listing_type
    ? property.listing_type.replace(/_/g, " ").toUpperCase()
    : "FOR SALE";

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
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
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
          {mineral.toUpperCase()}
        </div>
        <div
          style={{
            fontSize: 22,
            padding: "10px 20px",
            border: "2px solid #D4AF37",
            borderRadius: 8,
            color: "#D4AF37",
            fontWeight: 600,
          }}
        >
          {listingType}
        </div>
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
        <div
          style={{
            fontSize: 76,
            fontWeight: 800,
            lineHeight: 1.05,
            maxWidth: "1040px",
          }}
        >
          {title}
        </div>
        <div style={{ fontSize: 36, color: "#cbd5e1" }}>{location}</div>
        {hectares && (
          <div style={{ fontSize: 32, color: "#D4AF37" }}>{hectares}</div>
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
        <span>juniorminingintelligence.com/properties</span>
        <span style={{ color: "#D4AF37" }}>Prospector&apos;s Exchange</span>
      </div>
    </div>,
    { width: 1200, height: 630 },
  );
}
