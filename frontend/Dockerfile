# Frontend Dockerfile
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Serve the application
EXPOSE 3000

# Use a simple HTTP server to serve the built files
RUN npm install -g serve
CMD ["serve", "-s", "dist", "-l", "3000"]