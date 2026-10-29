/**
 * MSW Mocks Index
 * TASK-FE-P5-001: MSW Mock Server Setup
 *
 * Central export for MSW handlers and data.
 */

export * from './handlers/phase5Handlers';
export * from './data';

// Re-export setup utilities (conditional on environment)
// Browser setup: import { worker } from './mocks/browser'
// Node setup: import { server } from './mocks/server'
