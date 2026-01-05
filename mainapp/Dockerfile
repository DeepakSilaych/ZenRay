FROM node:20-alpine

WORKDIR /app

# Copy package files first (for better caching)
COPY package.json ./

# Install dependencies
RUN npm install

# Copy source code (node_modules excluded via .dockerignore)
COPY . .

EXPOSE 5173

# Use dev server for development (with hot reload)
# For production, uncomment the build step and use preview
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]

