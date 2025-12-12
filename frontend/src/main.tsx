import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import './index.css'
import App from './App.tsx'

// Create a QueryClient instance for React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
})

/**
 * Enable MSW mocking conditionally based on environment variable
 *
 * TASK-FE-P5-006: Switch to Real Backend
 *
 * By default (VITE_USE_MOCKS not set or set to 'false'), MSW is disabled
 * and the frontend connects to the real backend API.
 *
 * To enable mocking for development without backend:
 * 1. Set VITE_USE_MOCKS=true in .env or .env.development
 * 2. Restart the dev server
 *
 * For production builds, MSW is never enabled regardless of env vars.
 */
async function enableMocking(): Promise<void> {
  // Only enable MSW in development mode AND when explicitly requested
  const useMocks = import.meta.env.VITE_USE_MOCKS === 'true'

  if (import.meta.env.DEV && useMocks) {
    const { worker } = await import('./mocks/browser')
    await worker.start({
      onUnhandledRequest: 'warn',
      serviceWorker: {
        url: '/mockServiceWorker.js',
      },
    })
    console.log('[MSW] Mock Service Worker enabled')
  } else if (import.meta.env.DEV) {
    console.log('[API] Connecting to real backend (MSW disabled)')
  }
}

enableMocking().then(() => {
  createRoot(document.getElementById('root')!).render(
    <StrictMode>
      <QueryClientProvider client={queryClient}>
        <App />
      </QueryClientProvider>
    </StrictMode>,
  )
})
