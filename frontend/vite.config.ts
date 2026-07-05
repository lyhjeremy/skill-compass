import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Served at https://lyhjeremy.github.io/skill-compass/
export default defineConfig({
  base: '/skill-compass/',
  plugins: [react()],
})
