# Build context: Reqops-agents repo root (./ReqOps staged by deploy/up.sh).
FROM node:20-alpine AS build
WORKDIR /app

ARG VITE_API_BASE_URL=/api/v1
ARG VITE_WS_BASE_URL
ARG VITE_LANGFLOW_USE_BACKEND=true
ARG VITE_AUTH0_DOMAIN
ARG VITE_AUTH0_CLIENT_ID
ARG VITE_DEV_AUTH_BYPASS

ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
ENV VITE_WS_BASE_URL=${VITE_WS_BASE_URL}
ENV VITE_LANGFLOW_USE_BACKEND=${VITE_LANGFLOW_USE_BACKEND}
ENV VITE_AUTH0_DOMAIN=${VITE_AUTH0_DOMAIN}
ENV VITE_AUTH0_CLIENT_ID=${VITE_AUTH0_CLIENT_ID}
ENV VITE_DEV_AUTH_BYPASS=${VITE_DEV_AUTH_BYPASS}

COPY ReqOps/Reqops_Frontend/package.json ReqOps/Reqops_Frontend/package-lock.json ./
RUN npm ci
COPY ReqOps/Reqops_Frontend/ ./
RUN npm run build

FROM nginx:1.27-alpine
RUN rm -f /etc/nginx/conf.d/default.conf
COPY deploy/reqops-frontend/nginx-spa.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
