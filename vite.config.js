import { defineConfig } from 'vite';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  build: {
    outDir: 'app/static/dist',
    emptyOutDir: true,
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'frontend/main.js'),
        submitPhoto: resolve(__dirname, 'frontend/submit_photo_entry.js')
      },
      output: {
        entryFileNames: '[name].js',
        chunkFileNames: 'chunk-[hash].js',
        assetFileNames: '[name][extname]'
      }
    }
  }
});
