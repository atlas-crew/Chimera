import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

/**
 * Vite config for bundling the SPA into the Flask package.
 *
 * Usage: vite build --config vite.config.bundle.ts
 *
 * Outputs to ../vuln-api/app/web_dist/ so the Python wheel
 * includes the built frontend.
 */
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: '../vuln-api/app/web_dist',
    emptyOutDir: true,
  },
})
