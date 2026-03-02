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
        // Uses object syntax to avoid circular dependency issues with Rollup helpers
        manualChunks: {
          'vendor-react': [
            'react',
            'react-dom',
            'scheduler',
          ],
          'charts': [
            '@nivo/core',
            '@nivo/sankey',
            '@nivo/colors',
            '@nivo/legends',
            '@nivo/text',
            '@nivo/theming',
            '@nivo/tooltip',
          ],
          'state': [
            'zustand',
            'immer',
            '@tanstack/react-query',
          ],
          'vendor-ui': [
            '@radix-ui/react-dialog',
            '@radix-ui/react-select',
            '@radix-ui/react-popover',
            '@radix-ui/react-dropdown-menu',
            '@radix-ui/react-tooltip',
            '@radix-ui/react-checkbox',
            '@radix-ui/react-radio-group',
            '@radix-ui/react-label',
            '@radix-ui/react-separator',
            '@radix-ui/react-alert-dialog',
            '@radix-ui/react-slot',
          ],
          'forms': [
            'react-hook-form',
            '@hookform/resolvers',
            'zod',
          ],
          'icons': [
            'lucide-react',
          ],
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
