/**
 * MSW Browser Setup
 * TASK-FE-P5-001: MSW Mock Server Setup
 *
 * Configures Mock Service Worker for browser development environment.
 * Import and start this worker in main.tsx for development mocking.
 */

import { setupWorker } from 'msw';
import { phase5Handlers } from './handlers/phase5Handlers';

/**
 * MSW browser worker instance
 *
 * Usage in main.tsx:
 * ```typescript
 * import { worker } from './mocks/browser';
 *
 * if (import.meta.env.DEV) {
 *   worker.start({
 *     onUnhandledRequest: 'warn',
 *   });
 * }
 * ```
 */
export const worker = setupWorker(...phase5Handlers);
