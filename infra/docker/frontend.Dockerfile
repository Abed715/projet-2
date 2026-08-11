# syntax=docker/dockerfile:1
#
# Multi-stage build using Next.js's `output: "standalone"` (next.config.ts)
# so the runtime image ships a minimal self-contained server bundle
# instead of the full node_modules tree.
#
# NEXT_PUBLIC_API_BASE_URL is a *build-time* value baked into the client
# JS bundle - Next.js does not re-read NEXT_PUBLIC_* vars at container
# runtime. It must be passed as a `docker build --build-arg` (or compose
# `build.args`), and it must be a URL the *browser* can reach (typically
# the host's published backend port), not an internal Docker network
# hostname. See docs/deployment.md.

FROM node:22-slim AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM node:22-slim AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

ARG NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL
ENV NEXT_TELEMETRY_DISABLED=1

RUN npm run build

FROM node:22-slim AS runtime
WORKDIR /app

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000

RUN useradd --create-home --uid 1000 jarvis

# `public/` isn't copied here because this app doesn't have one yet (no
# static assets) - add `COPY --from=builder /app/public ./public` back if
# one is introduced; see the standalone-output docs this pattern follows.
COPY --from=builder --chown=jarvis:jarvis /app/.next/standalone ./
COPY --from=builder --chown=jarvis:jarvis /app/.next/static ./.next/static

USER jarvis

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD node -e "require('http').get('http://localhost:3000/', (r) => process.exit(r.statusCode < 500 ? 0 : 1)).on('error', () => process.exit(1))"

CMD ["node", "server.js"]
