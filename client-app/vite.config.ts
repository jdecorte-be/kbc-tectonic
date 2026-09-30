import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  preview: {
    allowedHosts: true, // behind a PaaS domain (nixpacks start)
  },
  server: {
    host: '0.0.0.0',
    port: 3001,
    watch: {
      usePolling: true,
    },
    proxy: {
      '/api': {
        target: process.env.VITE_API_INTERNAL_URL || 'http://backend:8000',
        changeOrigin: true,
      },
    },
  },
});
