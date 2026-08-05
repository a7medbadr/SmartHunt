import type { NextConfig } from "next";

const backendOrigin = process.env.BACKEND_ORIGIN ?? "http://localhost:8000";

const nextConfig: NextConfig = {
  // Single-user app accessed over the LAN from other devices in dev mode —
  // Next.js blocks cross-origin dev requests (HMR, RSC) by default otherwise.
  allowedDevOrigins: ["192.168.8.22"],
  // A self-contained server bundle (only the files actually needed at
  // runtime, no full node_modules) — what the OpenShift container image
  // build copies in, added 2026-08-04 alongside the frontend's first
  // real Dockerfile.
  output: "standalone",
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${backendOrigin}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
