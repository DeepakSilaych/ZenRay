import { defineConfig } from 'vite'

export default defineConfig({
  server: {
    host: '0.0.0.0',
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
    allowedHosts: [
      'zenray.live',
      'app.zenray.live',
      'api.zenray.live',
      'localhost',
      '127.0.0.1',
      '.zenray.live'
    ]
  }
})

