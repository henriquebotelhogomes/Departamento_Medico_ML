import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import { fileURLToPath, URL } from "node:url";

// In dev, proxy /api and /media to the FastAPI backend so the SPA can use
// same-origin relative URLs (no CORS, matches the production single-container setup).
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  server: {
    port: 5173,
    proxy: {
      "/api": { target: "http://localhost:8000", changeOrigin: true },
      "/media": { target: "http://localhost:8000", changeOrigin: true },
    },
  },
  build: {
    outDir: "dist",
    sourcemap: false,
  },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: "./src/test/setup.ts",
    css: false,
  },
});
