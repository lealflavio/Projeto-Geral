import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',            // Permite acesso externo
    port: 5173,
    strictPort: true,
    allowedHosts: ['.ngrok-free.app'],  // Permite todos os subdomínios do ngrok
    cors: true
  }
})
