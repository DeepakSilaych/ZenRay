import { defineConfig } from 'astro/config'
import tailwind from '@astrojs/tailwind'
import { loadEnv } from 'vite'

// Load env from current directory
const env = loadEnv(process.env.NODE_ENV || 'development', process.cwd(), '')

const webPort = parseInt(env.WEB_PORT || '4001')
const siteUrl = env.PUBLIC_SITE_URL || 'http://localhost:4001'

// Parse allowed hosts from env or use defaults
const allowedHostsStr = env.ALLOWED_HOSTS || 'localhost,127.0.0.1'
const allowedHosts = allowedHostsStr.split(',').map(h => h.trim())

export default defineConfig({
  site: siteUrl,
  integrations: [
    tailwind(),
  ],
  server: {
    host: '0.0.0.0',
    port: webPort,
  },
  vite: {
    server: {
      host: '0.0.0.0',
      port: webPort,
      allowedHosts: allowedHosts
    },
    preview: {
      host: '0.0.0.0',
      port: webPort,
      allowedHosts: allowedHosts
    }
  }
})
