import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

const apiTarget = process.env.VITE_API_TARGET || "http://localhost:8000";

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: apiTarget,
        changeOrigin: true,
      },
    },
  },
  // SPA fallback for client-side routing
  appType: "spa",
});

