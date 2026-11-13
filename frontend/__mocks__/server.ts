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
 *   http.get('/api/v1/products', () => {
 *     return HttpResponse.json({ error: 'Server error' }, { status: 500 })
 *   })
 * )
 */
export const server = setupServer(...handlers);
