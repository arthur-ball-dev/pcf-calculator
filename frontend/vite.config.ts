// @ts-nocheck - Suppress type errors from Vite/Vitest plugin type incompatibility
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import { VitePWA } from 'vite-plugin-pwa';
import path from 'path';

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.ico', 'apple-touch-icon.png', 'robots.txt'],
      manifest: false, // We provide our own manifest.json
      workbox: {
        // Cache strategies
        runtimeCaching: [
          {
            // Cache API responses (with network fallback)
            urlPattern: /^https?:\/\/.*\/api\/v1\/.*/i,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'api-cache',
              expiration: {
                maxEntries: 100,
                maxAgeSeconds: 60 * 60, // 1 hour
              },
              cacheableResponse: {
                statuses: [0, 200],
              },
            },
          },
          {
            // Cache static assets
            urlPattern: /\.(?:png|jpg|jpeg|svg|gif|webp|ico)$/i,
            handler: 'CacheFirst',
            options: {
              cacheName: 'image-cache',
              expiration: {
                maxEntries: 50,
                maxAgeSeconds: 60 * 60 * 24 * 30, // 30 days
              },
            },
          },
          {
            // Cache fonts
            urlPattern: /\.(?:woff|woff2|ttf|otf|eot)$/i,
            handler: 'CacheFirst',
            options: {
              cacheName: 'font-cache',
              expiration: {
                maxEntries: 20,
                maxAgeSeconds: 60 * 60 * 24 * 365, // 1 year
              },
            },
          },
        ],
        // Don't cache the following
        navigateFallbackDenylist: [/^\/api\//],
      },
      devOptions: {
        enabled: true, // Enable in development for testing
        type: 'module',
      },
    }),
  ],
  // =============================================================================
  // Build Configuration - TASK-FE-P7-024: Bundle Optimization
  // =============================================================================
  build: {
    rollupOptions: {
      output: {
        // Manual chunk splitting for optimal bundle sizes
        // All React-dependent libraries go in vendor-react to avoid hook errors
        manualChunks: (id: string) => {
          // Vendor chunk: React, React DOM, and ALL React-dependent libraries
          // This prevents "Cannot read properties of undefined" errors in production
          if (id.includes('node_modules/react-dom') ||
              id.includes('node_modules/react/') ||
              id.includes('node_modules/scheduler') ||
              id.includes('node_modules/react-router') ||
              id.includes('node_modules/@remix-run/router') ||
              id.includes('node_modules/@nivo') ||
              id.includes('node_modules/d3-') ||
              id.includes('node_modules/zustand') ||
              id.includes('node_modules/immer') ||
              id.includes('node_modules/@tanstack/react-query') ||
              id.includes('node_modules/@radix-ui') ||
              id.includes('node_modules/react-hook-form') ||
              id.includes('node_modules/@hookform') ||
              id.includes('node_modules/lucide-react')) {
            return 'vendor';
          }

          // Export chunk: xlsx library (loaded on demand) - no React dependency
          if (id.includes('node_modules/xlsx') ||
              id.includes('node_modules/cfb') ||
              id.includes('node_modules/codepage') ||
              id.includes('node_modules/frac') ||
              id.includes('node_modules/ssf') ||
              id.includes('node_modules/wmf') ||
              id.includes('node_modules/adler-32') ||
              id.includes('node_modules/crc-32')) {
            return 'export';
          }

          // Zod validation library - no React dependency
          if (id.includes('node_modules/zod')) {
            return 'validation';
          }
        },
      },
    },
    // Set chunk size warning threshold (250KB for gzipped)
    chunkSizeWarningLimit: 500, // 500KB minified (roughly 150KB gzipped)
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./__tests__/setup.ts'],
    exclude: [
      '**/node_modules/**',
      '**/dist/**',
      '**/cypress/**',
      '**/.{idea,git,cache,output,temp}/**',
      '**/{karma,rollup,webpack,vite,vitest,jest,ava,babel,nyc,cypress,tsup,build}.config.*',
      '**/tests/e2e/**', // Exclude Playwright tests
    ],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'lcov'],
      exclude: [
        'node_modules/',
        '__tests__/',
        '**/*.d.ts',
        '**/*.config.*',
        '**/mockData',
        'dist/',
        'src/main.tsx',
        'src/vite-env.d.ts',
        'src/components/ui/**', // UI components from shadcn (not our code)
      ],
      include: [
        'src/**/*.{ts,tsx}',
      ],
      all: true,
      thresholds: {
        lines: 80,
        functions: 80,
        branches: 80,
        statements: 80,
      },
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});
