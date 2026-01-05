FROM node:20-alpine

WORKDIR /app

# Copy package files first (for better caching)
COPY package.json ./

# Install dependencies
RUN npm install

# Copy source code (node_modules excluded via .dockerignore)
COPY . .

EXPOSE 5174

# Use dev server - Caddy will handle host rewriting
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5174", "--", "--disable-host-check"]

