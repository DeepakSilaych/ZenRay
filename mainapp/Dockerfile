FROM node:20-alpine

WORKDIR /app

# Build-time environment variables for Vite (VITE_ vars)
ARG VITE_SERVER_URL
ARG VITE_SITE_URL=https://zenray.live
ARG VITE_GITHUB_URL=https://github.com/DeepakSilaych/ZenRay
ARG VITE_DOCS_URL=https://zenray.live/docs
ARG VITE_ALLOWED_HOSTS=zenray.live,app.zenray.live,api.zenray.live,localhost,127.0.0.1,.zenray.live

ENV VITE_SERVER_URL=${VITE_SERVER_URL}
ENV VITE_SITE_URL=${VITE_SITE_URL}
ENV VITE_GITHUB_URL=${VITE_GITHUB_URL}
ENV VITE_DOCS_URL=${VITE_DOCS_URL}
ENV VITE_ALLOWED_HOSTS=${VITE_ALLOWED_HOSTS}

# Copy package files first (for better caching)
COPY package.json ./

# Install dependencies
RUN npm install

# Copy source code (node_modules excluded via .dockerignore)
COPY . .

# Runtime port
ARG PORT=4002
ENV DASHBOARD_PORT=${PORT}
ENV SERVER_PORT=4003
EXPOSE ${PORT}

# Use dev server
CMD npm run dev -- --host 0.0.0.0 --port ${DASHBOARD_PORT:-4002}
