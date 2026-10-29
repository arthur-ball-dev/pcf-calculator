/**
 * Async wait budget for Testing Library.
 *
 * `waitFor` / `findBy*` default to a 1 s budget. The wizard and virtualised-BOM
 * integration tests render large trees in jsdom; their slowest step takes ~3 s on one
 * idle core and several times that under a full parallel run on a shared CI runner, so
 * the 1 s default turned load into failures. 10 s keeps a genuine never-satisfied
 * assertion visible while removing the dependence on machine load. The matching
 * per-test budget (testTimeout) is set in vitest.config.ts.
 */
import { configure } from '@testing-library/react';

configure({ asyncUtilTimeout: 10000 });
