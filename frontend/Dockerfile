FROM node:20-alpine

WORKDIR /app

# Copy package files and install dependencies
COPY package.json package-lock.json* ./
RUN npm install

# Copy all frontend files
COPY . .

# Expose Vite's default port
EXPOSE 5173

# Start Vite dev server on all interfaces so it's accessible outside the container
CMD ["npm", "run", "dev", "--", "--host"]
