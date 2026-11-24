import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'
import vueDevTools from 'vite-plugin-vue-devtools'

const bff = 'http://127.0.0.1:8000' // the UI only talks to the BFF

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue(), tailwindcss(), vueDevTools()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    // the UI calls /api/... and /media/...; the dev server forwards them to the BFF
    proxy: {
      '/api': { target: bff, rewrite: (path) => path.replace(/^\/api/, '') },
      '/media': bff,
    },
  },
})
