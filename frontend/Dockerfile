FROM node:20-alpine AS builder

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# Copy application code
COPY . .

# Build arguments for API URL
ARG NEXT_PUBLIC_API_URL=http://localhost
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built static files from builder
COPY --from=builder /app/out /usr/share/nginx/html

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
