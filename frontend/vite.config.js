import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api/intake': {
        target: 'http://localhost:8002',
        rewrite: (path) => path.replace(/^\/api\/intake/, ''),
        changeOrigin: true,
      },
      '/api/optimizer': {
        target: 'http://localhost:8003',
        rewrite: (path) => path.replace(/^\/api\/optimizer/, ''),
        changeOrigin: true,
      },
      '/api/reasoner': {
        target: 'http://localhost:8004',
        rewrite: (path) => path.replace(/^\/api\/reasoner/, ''),
        changeOrigin: true,
      },
    },
  },
})
