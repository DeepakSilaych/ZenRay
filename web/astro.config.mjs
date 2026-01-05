import { defineConfig, envField } from 'astro/config'
import tailwind from '@astrojs/tailwind'
import { loadEnv } from 'vite'
import path from 'path'

// Load env from parent directory
const env = loadEnv(process.env.NODE_ENV || 'development', path.resolve(process.cwd(), '..'), '')

const webPort = parseInt(env.WEB_PORT || '4001')

export default defineConfig({
  integrations: [tailwind()],
  site: 'https://zenray.live',
  server: {
    host: '0.0.0.0',
    port: webPort,
  },
  vite: {
    server: {
      host: '0.0.0.0',
      port: webPort,
      allowedHosts: [
        'zenray.live',
        'app.zenray.live',
        'api.zenray.live',
        'localhost',
        '127.0.0.1',
        '.zenray.live'
      ]
    },
    preview: {
      host: '0.0.0.0',
      port: webPort,
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
