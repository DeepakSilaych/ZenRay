import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig(({ mode }) => {
  // Load env from current directory
  const env = loadEnv(mode, __dirname, '')
  
  const dashboardPort = parseInt(env.DASHBOARD_PORT || '4002')
  const serverHost = env.SERVER_HOST || 'localhost'
  const serverPort = parseInt(env.SERVER_PORT || '4003')
  
  return {
    plugins: [react()],
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "./src"),
      },
    },
    server: {
      host: '0.0.0.0',
      port: dashboardPort,
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
          target: `http://${serverHost}:${serverPort}`,
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, '')
        }
      }
    },
    preview: {
      host: '0.0.0.0',
      port: dashboardPort,
      allowedHosts: [
        'zenray.live',
        'app.zenray.live',
        'api.zenray.live',
        'localhost',
        '127.0.0.1',
        '.zenray.live'
      ]
    }
  }
})
