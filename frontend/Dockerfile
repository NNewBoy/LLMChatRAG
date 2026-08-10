# ── Stage 1: 构建前端 ──────────────────────────
FROM node:20-alpine AS builder
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --registry=https://registry.npmmirror.com

COPY . .
RUN npm run build

# ── Stage 2: Nginx 托管静态文件 ────────────────
FROM nginx:alpine

COPY --from=builder /app/dist /var/www/llmchatrag
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]