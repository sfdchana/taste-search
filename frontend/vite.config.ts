import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// base is '/taste-search/' for the production build (served from GitHub Pages at
// sfdchana.github.io/taste-search/), and '/' for local dev.
export default defineConfig(({ command }) => ({
  base: command === 'build' ? '/taste-search/' : '/',
  plugins: [react()],
}))
