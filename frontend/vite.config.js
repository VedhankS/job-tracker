import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss()],
  server: {
    proxy: {
          '/register': {
            target: 'http://127.0.0.1:8080',
            changeOrigin: true,
          },
          '/login': {
            target: 'http://127.0.0.1:8080',
            changeOrigin: true,
          },
          '/jobs': {
            target: 'http://127.0.0.1:8080',
            changeOrigin: true,
          },
          '/health': {
            target: 'http://127.0.0.1:8080',
            changeOrigin: true,
          },
        },
  },
})
