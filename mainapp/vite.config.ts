import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    host: '0.0.0.0',
    port: 5174,
    strictPort: false,
    allowedHosts: [
      'zenray.live',
      'app.zenray.live',
      'api.zenray.live',
      'localhost',
      '127.0.0.1',
      '.zenray.live'
    ],
    hmr: {
      clientPort: 443
    },
    proxy: {
      '/api/': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  },
  preview: {
    host: '0.0.0.0',
    port: 5174,
    allowedHosts: [
      'zenray.live',
      'app.zenray.live',
      'api.zenray.live',
      'localhost',
      '127.0.0.1',
      '.zenray.live'  // Allow all subdomains
    ]
  }
})

