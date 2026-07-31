import type { NextConfig } from "next";

const backendOrigin = process.env.BACKEND_ORIGIN ?? "http://localhost:8000";

const nextConfig: NextConfig = {
  // Single-user app accessed over the LAN from other devices in dev mode —
  // Next.js blocks cross-origin dev requests (HMR, RSC) by default otherwise.
  allowedDevOrigins: ["192.168.8.22"],
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
