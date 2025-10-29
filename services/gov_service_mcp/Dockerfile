FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy application code
COPY . .

# Expose port
EXPOSE 8005

# Set environment variables
ENV TRANSPORT_MODE=http
ENV MCP_PORT=8005
ENV GOV_SERVICE_URL=http://gov-service:8003

# Start the server
CMD ["node", "index.js"]

