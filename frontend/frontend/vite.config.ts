import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
// Demo builds (`npm run build:demo`) run without a backend and are served from
// GitHub Pages at https://deokhwajeong.github.io/demos/storytailor/. They use a
// relative base so the same output works under that path or any other folder.
export default defineConfig(({ mode }) => ({
  plugins: [react()],
  base: mode === 'demo' || process.env.VITE_DEMO === '1' ? './' : '/',
}))
