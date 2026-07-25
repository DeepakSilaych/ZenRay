FROM node:20-alpine AS builder

WORKDIR /app

# Build-time environment variables for Astro (PUBLIC_ vars)
ARG PUBLIC_SITE_URL=http://localhost:4001
ARG PUBLIC_DASHBOARD_URL=http://localhost:4002
ARG PUBLIC_API_URL=http://localhost:4003
ARG PUBLIC_GITHUB_URL=https://github.com/DeepakSilaych/ZenRay
ARG ALLOWED_HOSTS=localhost,127.0.0.1

ENV PUBLIC_SITE_URL=${PUBLIC_SITE_URL}
ENV PUBLIC_DASHBOARD_URL=${PUBLIC_DASHBOARD_URL}
ENV PUBLIC_API_URL=${PUBLIC_API_URL}
ENV PUBLIC_GITHUB_URL=${PUBLIC_GITHUB_URL}
ENV ALLOWED_HOSTS=${ALLOWED_HOSTS}

# Copy package files
COPY package.json ./
RUN npm install

# Copy source code
COPY . .

# Persist build-time env into a .env file so Astro's loadEnv picks them up
RUN printf "PUBLIC_SITE_URL=%s\nPUBLIC_DASHBOARD_URL=%s\nPUBLIC_API_URL=%s\nPUBLIC_GITHUB_URL=%s\nALLOWED_HOSTS=%s\n" \
    "$PUBLIC_SITE_URL" "$PUBLIC_DASHBOARD_URL" "$PUBLIC_API_URL" "$PUBLIC_GITHUB_URL" "$ALLOWED_HOSTS" > .env

# Build the site
RUN npm run build

# Production stage — serve the static dist via nginx (bypasses Astro preview's host filter)
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
RUN printf 'server {\n  listen 4001;\n  root /usr/share/nginx/html;\n  index index.html;\n  location / { try_files $uri $uri/ /index.html; }\n}\n' > /etc/nginx/conf.d/default.conf
EXPOSE 4001
