# Stage 1: Build
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm ci --prefer-offline || npm install

# Copy source
COPY . .

# Full backend URL — overridden at build time by Render/docker-compose
ARG NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
ENV NEXT_PUBLIC_BACKEND_URL=$NEXT_PUBLIC_BACKEND_URL

# Build
RUN npm run build

# Stage 2: Production
FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production

# Copy built output from builder
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["node", "server.js"]
