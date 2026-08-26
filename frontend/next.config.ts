import type { NextConfig } from "next";

// CSP is stricter in production - no unsafe-eval
const isDev = process.env.NODE_ENV === "development";
const scriptSrc = isDev
  ? "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://www.googletagmanager.com https://www.google-analytics.com"
  : "script-src 'self' 'unsafe-inline' https://www.googletagmanager.com https://www.google-analytics.com";

const nextConfig: NextConfig = {
  // Enable React strict mode for better development experience
  reactStrictMode: true,

  // Image optimization
  images: {
    formats: ["image/avif", "image/webp"],
    dangerouslyAllowSVG: true,
    contentSecurityPolicy: "default-src 'self'; script-src 'none'; sandbox;",
    remotePatterns: [
      {
        protocol: "https",
        hostname: "placehold.co",
      },
      {
        protocol: "https",
        hostname: "*.amazonaws.com",
      },
      {
        protocol: "https",
        hostname: "juniorminingintelligence.com",
      },
      {
        protocol: "https",
        hostname: "api.juniorminingintelligence.com",
      },
    ],
  },

  // Compression
  compress: true,

  // Hide X-Powered-By header
  poweredByHeader: false,

  // Generate ETags for better caching
  generateEtags: true,

  // Headers for security, SEO, and caching
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          {
            key: "X-DNS-Prefetch-Control",
            value: "on",
          },
          {
            key: "X-Frame-Options",
            value: "SAMEORIGIN",
          },
          {
            key: "X-Content-Type-Options",
            value: "nosniff",
          },
          {
            key: "Referrer-Policy",
            value: "origin-when-cross-origin",
          },
          {
            key: "Content-Security-Policy",
            value: [
              "default-src 'self'",
              scriptSrc,
              "style-src 'self' 'unsafe-inline'",
              "img-src 'self' data: https: blob:",
              "font-src 'self' data:",
              "connect-src 'self' https://juniorminingintelligence.com https://api.juniorminingintelligence.com wss://juniorminingintelligence.com wss://api.juniorminingintelligence.com https://www.google-analytics.com https://analytics.google.com",
              "frame-ancestors 'none'",
              "base-uri 'self'",
              "form-action 'self'",
              "object-src 'none'",
            ].join("; "),
          },
          {
            key: "Permissions-Policy",
            value:
              "camera=(), microphone=(), geolocation=(), payment=(), usb=(), magnetometer=(), gyroscope=(), accelerometer=()",
          },
        ],
      },
      {
        // Cache static assets (images, fonts, etc.) for 1 year
        source: "/static/:path*",
        headers: [
          {
            key: "Cache-Control",
            value: "public, max-age=31536000, immutable",
          },
        ],
      },
      {
        // Cache images for 1 week with revalidation
        source: "/:path*\\.(png|jpg|jpeg|gif|webp|svg|ico|avif)",
        headers: [
          {
            key: "Cache-Control",
            value: "public, max-age=604800, stale-while-revalidate=86400",
          },
        ],
      },
      {
        // Cache fonts for 1 year
        source: "/:path*\\.(woff|woff2|ttf|otf|eot)",
        headers: [
          {
            key: "Cache-Control",
            value: "public, max-age=31536000, immutable",
          },
        ],
      },
      {
        // API responses MUST NOT be publicly cached — most carry per-user data
        // (auth headers, watchlist, inquiry inbox, etc.). Public caching here
        // can leak one user's data to another via shared intermediate caches.
        // Routes that want caching should set their own headers.
        source: "/api/:path*",
        headers: [
          {
            key: "Cache-Control",
            value: "private, no-store, max-age=0, must-revalidate",
          },
        ],
      },
    ];
  },

  // Three pages competed for private-placement searches: the 4,554-word guide
  // below, /guides/private-placements-and-warrants (1,591, actually about units
  // and warrants), and this one (1,087, a straight duplicate sitting in the
  // financial-hub section). Google had to pick among three of ours for the same
  // query and split authority instead — the best of them earned 4 organic
  // sessions in the 30 days to 2026-08-26.
  //
  // The duplicate redirects into the canonical guide. The warrants page keeps
  // its URL and content but was retitled to lead with units and warrants rather
  // than "private placements", which removes the overlap without deleting a
  // distinct subtopic that Warrant Radar links to.
  //
  // 308 (permanent: true) rather than 302 — link equity only passes on a
  // permanent redirect, and passing it is the entire point.
  async redirects() {
    return [
      {
        source: "/financial-hub/private-placements-guide",
        destination: "/guides/how-junior-mining-companies-raise-money",
        permanent: true,
      },
    ];
  },
};

export default nextConfig;
