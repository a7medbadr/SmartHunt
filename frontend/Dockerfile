FROM node:20-slim AS deps
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

FROM node:20-slim AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY frontend/ .
# BACKEND_ORIGIN IS needed at build time despite next.config.ts's rewrites()
# reading process.env — found 2026-08-04 chasing "حصل خطأ، جرب تاني" on
# every login/register attempt on OpenShift. With `output: "standalone"`,
# Next.js evaluates next.config.ts (and therefore this env read) once
# during `next build` and bakes the resulting rewrite destination into the
# build manifest; the runtime container's own BACKEND_ORIGIN (set via the
# configmap) is never re-read. Locally this was invisible because the
# fallback default ("http://localhost:8000") already happens to be
# correct for local dev, so build-time vs runtime made no observable
# difference there — only OpenShift, where the real value
# (http://smarthunt-backend) differs from the default, exposed it: the
# pod's Next server kept trying to proxy to 127.0.0.1:8000 (ECONNREFUSED)
# for every single /api/* call. Must be passed as a build ARG (see
# k8s/base/frontend-buildconfig.yaml's dockerStrategy.buildArgs) so it's
# present when `next build` actually runs.
ARG BACKEND_ORIGIN=http://localhost:8000
ENV BACKEND_ORIGIN=$BACKEND_ORIGIN
# NEXT_TELEMETRY_DISABLED avoids an outbound telemetry call that can hang
# for a long time on OpenShift's restricted build-pod network — found
# 2026-08-04 after a build sat at "Creating an optimized production
# build ..." for 90+ minutes using <10% of its CPU limit (i.e. blocked on
# network I/O, not actually compiling).
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

FROM node:20-slim AS runner
WORKDIR /app
ENV NODE_ENV=production

# output: "standalone" (next.config.ts) traces only the files actually
# needed at runtime — no full node_modules copied into the final image.
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME=0.0.0.0

CMD ["node", "server.js"]
