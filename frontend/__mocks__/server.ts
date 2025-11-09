/**
 * MSW Server Setup
 * TASK-FE-011: Integration Testing Infrastructure
 *
 * Configures Mock Service Worker for testing environment.
 * Provides API mocking without actual network requests.
 */

import { setupServer } from 'msw/node';
import { handlers } from './handlers';

/**
 * MSW server instance
 *
 * Usage in tests:
 * - beforeAll(() => server.listen())
 * - afterEach(() => server.resetHandlers())
 * - afterAll(() => server.close())
 *
 * Override handlers:
 * server.use(
 *   rest.get('/api/v1/products', (req, res, ctx) => {
 *     return res(ctx.status(500), ctx.json({ error: 'Server error' }))
 *   })
 * )
 */
export const server = setupServer(...handlers);
