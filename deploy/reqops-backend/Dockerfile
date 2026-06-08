# Build context: Reqops-agents repo root (./ReqOps staged by deploy/up.sh).
FROM node:20-bookworm-slim AS deps
WORKDIR /app
COPY ReqOps/Reqops_backend/package.json ReqOps/Reqops_backend/package-lock.json ./
RUN npm ci

FROM node:20-bookworm-slim AS build
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY ReqOps/Reqops_backend/package.json ReqOps/Reqops_backend/package-lock.json ReqOps/Reqops_backend/tsconfig.json ./
COPY ReqOps/Reqops_backend/prisma ./prisma
COPY ReqOps/Reqops_backend/src ./src
RUN apt-get update && apt-get install -y --no-install-recommends openssl ca-certificates && rm -rf /var/lib/apt/lists/*
RUN npx prisma generate
RUN npm run build
RUN mkdir -p dist/frameworks && cp -r src/frameworks/defs dist/frameworks/defs

FROM node:20-bookworm-slim AS run
RUN apt-get update && apt-get install -y --no-install-recommends openssl ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /app
ENV NODE_ENV=production
COPY --from=build /app/dist ./dist
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/package.json /app/package-lock.json ./
COPY --from=build /app/prisma ./prisma
EXPOSE 3000
CMD ["sh", "-c", "npx prisma migrate deploy && node dist/server.js"]
