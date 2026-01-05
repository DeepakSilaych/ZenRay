FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package.json ./
RUN npm install

# Copy source code
COPY . .

# Build the site
RUN npm run build

# Production stage
FROM node:20-alpine

WORKDIR /app

# Copy built files
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/package.json ./
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/astro.config.mjs ./

# Port from env (default 4001)
ARG PORT=4001
ENV WEB_PORT=${PORT}
EXPOSE ${PORT}

CMD npm run preview -- --host 0.0.0.0 --port ${WEB_PORT:-4001}
