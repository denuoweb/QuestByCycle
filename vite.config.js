import { defineConfig } from 'vite';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  root: 'frontend',                       // ← treat `frontend/` as your project root
  base: '/static/dist/',                  // ← ensure chunks load from Flask static
  resolve: {
    alias: {
      '@': resolve(__dirname, 'frontend') // ← lets you import modules via "@/utils.js" etc.
    },
    extensions: ['.js']
  },
  build: {
    outDir: '../app/static/dist',         // ← emit into Flask’s `static/dist/`
    emptyOutDir: true,
    cssCodeSplit: false,                  // ← bundle *all* your SCSS into single style.css
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'frontend/main.js'),
        submitPhoto: resolve(__dirname, 'frontend/submit_photo_entry.js')
      },
      output: {
        entryFileNames: '[name].js',       // → main.js & submitPhoto.js
        chunkFileNames: 'chunk-[hash].js',
        assetFileNames: '[name][extname]'  // → style.css (no hash)
      }
    }
  },
  server: {
    // if you want to test dev against Flask backend:
    // proxy: { '/': 'http://localhost:5000' }
  }
});