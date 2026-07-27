# Frontend dev image (Vite dev server). Production uses the root Dockerfile.
FROM node:20-slim
WORKDIR /web
COPY package.json package-lock.json* ./
RUN npm ci || npm install
COPY . ./
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
