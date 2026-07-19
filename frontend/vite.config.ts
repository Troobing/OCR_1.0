import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // 开发代理：把前端发出的 /api 请求转发到后端 localhost:8000
    // 这样前端代码写 /api/upload，开发时 Vite 自动转发，不需要处理跨域
    proxy: {
      '/api': {
        target: 'http://localhost:5073',
        changeOrigin: true,
      },
    },
  },
})
