import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./__tests__/setup.ts', './__tests__/setup.timeouts.ts'],
    // The integration files render the full wizard and 100-row virtualised forms in jsdom.
    // The slowest single test takes ~3.5 s on one idle core; under a full parallel run on a
    // shared runner the same work takes several times longer. Vitest's 5 s default made those
    // tests fail on load alone. 30 s keeps a genuine hang detectable while removing the
    // load dependence. (The matching waitFor budget is set in __tests__/setup.ts.)
    testTimeout: 30000,
    hookTimeout: 30000,
    // Two integration files (wizardFlow, BOMEditor.virtualization) are timing-sensitive under
    // the load of a full parallel run and occasionally exceed their waitFor budgets on shared
    // runners while passing alone. Retry on CI only, so a genuine failure still fails after
    // three attempts but a load blip does not cost a 25-minute re-run. Vitest reports retries.
    retry: process.env.CI ? 2 : 0,
    // The MSW handlers mock absolute http://localhost:8000 URLs, so the unit tests need the
    // dev API base even in a clean checkout (CI, a fresh clone) that has no frontend/.env.
    env: {
      VITE_API_BASE_URL: 'http://localhost:8000',
    },
    exclude: [
      '**/node_modules/**',
      '**/dist/**',
      '**/tests/e2e/**',  // Exclude E2E tests (Playwright)
      '**/*.spec.ts',      // Exclude all .spec.ts files (E2E convention)
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
      lines: 80,
      functions: 80,
      branches: 80,
      statements: 80,
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});