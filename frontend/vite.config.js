import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  base: './',
  plugins: [vue()],
  server: {
    port: 3001,
    proxy: {
      '/ws': {
        target: 'ws://localhost:9000',
        ws: true
      },
      '/api': {
        target: 'http://localhost:9000',
        changeOrigin: true
      }
    }
  }
})
