import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
  server: {
    proxy: {
      '/register': 'http://nginx:80',
      '/login': 'http://nginx:80',
      '/jobs': 'http://nginx:80',
      '/resume': 'http://nginx:80',
      '/health': 'http://nginx:80',
      '/ai': {
        target: 'http://nginx:80',
        changeOrigin: true,
      },
    },
  },
})
