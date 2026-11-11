/**
 * loadExcelExport tests (#179)
 *
 * The loader imports the Excel export module on demand so ExcelJS stays out of the main bundle.
 * Each test imports a fresh copy of the loader, because it caches the module it loaded.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

const exportToExcel = vi.fn();

async function freshLoader() {
  vi.resetModules();
  return import('@/utils/export/loadExcelExport');
}

describe('loadExcelExport', () => {
  beforeEach(() => {
    vi.doMock('@/utils/export/excelExport', () => ({ exportToExcel }));
  });

  afterEach(() => {
    vi.doUnmock('@/utils/export/excelExport');
  });

  it('has no module before a load starts', async () => {
    const loader = await freshLoader();

    expect(loader.getLoadedExcelExport()).toBeNull();
  });

  it('preloadExcelExport resolves with the Excel export module', async () => {
    const loader = await freshLoader();

    const module = await loader.preloadExcelExport();

    expect(module.exportToExcel).toBe(exportToExcel);
  });

  it('returns the loaded module synchronously once loaded', async () => {
    const loader = await freshLoader();

    const module = await loader.preloadExcelExport();

    expect(loader.getLoadedExcelExport()).toBe(module);
  });

  it('starts only one load for repeated preloads', async () => {
    const loader = await freshLoader();

    const first = loader.preloadExcelExport();
    const second = loader.preloadExcelExport();

    expect(second).toBe(first);
    await first;
  });

  it('loadExcelExport loads the module when nothing is loaded yet', async () => {
    const loader = await freshLoader();

    const module = await loader.loadExcelExport();

    expect(module.exportToExcel).toBe(exportToExcel);
    expect(loader.getLoadedExcelExport()).toBe(module);
  });

  it('loadExcelExport returns the already loaded module', async () => {
    const loader = await freshLoader();
    const preloaded = await loader.preloadExcelExport();

    const module = await loader.loadExcelExport();

    expect(module).toBe(preloaded);
  });

  it('rejects when the module fails to load and retries on the next call', async () => {
    vi.doMock('@/utils/export/excelExport', () => {
      throw new Error('chunk load failed');
    });
    const loader = await freshLoader();

    // vitest wraps a mock factory's error in its own message
    await expect(loader.preloadExcelExport()).rejects.toThrow();
    expect(loader.getLoadedExcelExport()).toBeNull();

    vi.doMock('@/utils/export/excelExport', () => ({ exportToExcel }));
    const module = await loader.preloadExcelExport();

    expect(module.exportToExcel).toBe(exportToExcel);
  });
});
