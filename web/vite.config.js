import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// During development, Vite runs on :5173 and sends every /api/ call on to Flask on :5050.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { "/api": "http://localhost:5050" },
  },
  test: {
    environment: "jsdom",
    include: ["tests/**/*.test.{js,jsx}"],
  },
});
