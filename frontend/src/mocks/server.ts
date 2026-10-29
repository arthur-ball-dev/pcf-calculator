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
 * beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
 * afterEach(() => server.resetHandlers());
 * afterAll(() => server.close());
 * ```
 *
 * Override handlers in specific tests:
 * ```typescript
 * import { rest } from 'msw';
 *
 * server.use(
 *   rest.get('/api/v1/products/search', (req, res, ctx) => {
 *     return res(ctx.status(500), ctx.json({ error: 'Server error' }));
 *   })
 * );
 * ```
 */
export const server = setupServer(...phase5Handlers);
