# Dockerfile for React Frontend - Self-serving (no nginx wrapper)

# Stage 1: Build React app
FROM node:18-alpine as builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY public ./public
COPY src ./src

# Build React app
RUN NODE_OPTIONS=--openssl-legacy-provider npm run build

# Stage 2: Runtime with serve
FROM node:18-alpine

WORKDIR /app

# Install serve - lightweight HTTP server for React apps
RUN npm install -g serve

# Copy built app from builder stage
COPY --from=builder /app/build ./build

# Create non-root user
RUN addgroup -g 1001 -S appgroup && \
    adduser -S appuser -u 1001 -G appgroup

# Set permissions
RUN chown -R appuser:appgroup /app

USER appuser

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/ || exit 1

# Start React app with serve
# -s flag enables SPA routing (all routes served by index.html)
# -l 3000 sets the port
CMD ["serve", "-s", "build", "-l", "3000"]

