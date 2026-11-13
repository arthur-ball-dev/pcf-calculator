/**
 * MSW Node Server Setup
 * TASK-FE-P5-001: MSW Mock Server Setup
 *
 * Configures Mock Service Worker for Node.js testing environment.
 * Used by Vitest for API mocking in tests.
 */

import { setupServer } from 'msw/node';
import { phase5Handlers } from './handlers/phase5Handlers';

/**
 * MSW server instance for testing
 *
 * Usage in test setup:
 * ```typescript
 * import { server } from './mocks/server';
 *
 * beforeAll(() => server.listen({ onUnhandledFrame: 'error' }));
 * afterEach(() => server.resetHandlers());
 * afterAll(() => server.close());
 * ```
 *
 * Override handlers in specific tests:
 * ```typescript
 * import { http, HttpResponse } from 'msw';
 *
 * server.use(
 *   http.get('/api/v1/products/search', () => {
 *     return HttpResponse.json({ error: 'Server error' }, { status: 500 });
 *   })
 * );
 * ```
 */
export const server = setupServer(...phase5Handlers);
