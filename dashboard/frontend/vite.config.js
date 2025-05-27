import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',            // Permite acesso externo
    port: 5173,
    strictPort: true,
    allowedHosts: [
      '.ngrok-free.app',        // Permite todos os subdomínios do ngrok
      '.manusvm.computer',      // Permite todos os subdomínios do manusvm
      '5173-i3of3wnuma4y8gf9bv22c-67dbdd6c.manusvm.computer' // Domínio específico atual
    ],
    cors: true
  }
})
