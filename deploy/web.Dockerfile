# syntax=docker/dockerfile:1
# Portfolio-mode website only (no scan input, no API). Build context: repository root.

FROM node:24-slim AS build
WORKDIR /app
COPY web/package.json web/package-lock.json ./web/
RUN --mount=type=cache,target=/root/.npm cd web && npm ci
# The benchmarks page imports these two aggregate reports at build time.
COPY ml/results/baseline.json ml/results/xgboost.json ./ml/results/
COPY web/ ./web/
WORKDIR /app/web
ENV NEXT_PUBLIC_SECRETSENSE_MODE=portfolio
RUN npm run build:portfolio

FROM node:24-slim
WORKDIR /app/web
ENV NODE_ENV=production \
    NEXT_PUBLIC_SECRETSENSE_MODE=portfolio \
    NEXT_TELEMETRY_DISABLED=1
COPY --from=build /app/web/package.json /app/web/package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci --omit=dev
COPY --from=build /app/web/.next ./.next
COPY --from=build /app/web/next.config.ts ./
USER node
EXPOSE 3000
CMD ["npx", "next", "start", "--hostname", "0.0.0.0", "--port", "3000"]
