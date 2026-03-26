import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/analyze": {
        target: `http://localhost:${process.env.VITE_BACKEND_PORT || 8000}`,
        changeOrigin: true,
      },
    },
  },
});

