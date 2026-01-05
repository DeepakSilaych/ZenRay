FROM node:20-alpine

WORKDIR /app

# Copy package files first (for better caching)
COPY package.json ./

# Install dependencies
RUN npm install

# Copy source code (node_modules excluded via .dockerignore)
COPY . .

# Port from env (default 4002)
ARG PORT=4002
ENV DASHBOARD_PORT=${PORT}
EXPOSE ${PORT}

# Use dev server
CMD npm run dev -- --host 0.0.0.0 --port ${DASHBOARD_PORT:-4002}
