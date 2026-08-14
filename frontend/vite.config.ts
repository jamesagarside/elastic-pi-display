import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [react({ jsxImportSource: '@emotion/react' })],
  // Relative base so the bundle works wherever the backend mounts it.
  base: './',
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
    },
  },
  build: {
    chunkSizeWarningLimit: 2000,
  },
});
