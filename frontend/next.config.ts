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
  // Next.js's rewrites() proxy is implemented on top of `http-proxy`
  // internally, which has its own request timeout completely separate
  // from any client-side axios timeout — found live 2026-08-06 chasing
  // "the LinkedIn scan always says حصل خطأ أثناء الفحص": every real scan
  // call to /api/v1/linkedin-monitor/scan-feed (etc.) succeeded when hit
  // directly against the backend (confirmed via curl, real posts
  // returned), but through this proxy the exact same request died with
  // a 500 at *exactly* 30.0s every time — the client's own
  // SCAN_TIMEOUT_MS (240s)/AI_REQUEST_TIMEOUT_MS (850s) never got a
  // chance to matter, since the proxy itself killed the connection
  // first. `proxyTimeout` (ms) is the knob for this — undocumented in
  // the public Next.js docs but present in the framework's own
  // config-schema.js under `experimental`. Set comfortably above the
  // longest real client-side timeout in the app (AI calls at 850s) so
  // this layer is never the bottleneck for any legitimately slow-but-
  // real request again.
  experimental: {
    proxyTimeout: 900000,
  },
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
