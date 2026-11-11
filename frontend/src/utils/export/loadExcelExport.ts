/**
 * On-demand loader for the Excel export module (#179)
 *
 * excelExport.ts imports ExcelJS (~900 kB minified). Importing it dynamically keeps ExcelJS in its
 * own chunk instead of the main bundle. preloadExcelExport() starts the download early; once the
 * module has loaded, getLoadedExcelExport() returns it synchronously, so an export runs without
 * waiting on the chunk.
 */

type ExcelExportModule = typeof import('./excelExport');

let loaded: ExcelExportModule | null = null;
let pending: Promise<ExcelExportModule> | null = null;

/** Starts loading the Excel export module (once) and resolves with it. A failed load can be retried. */
export function preloadExcelExport(): Promise<ExcelExportModule> {
  pending ??= import('./excelExport').then(
    (module) => {
      loaded = module;
      return module;
    },
    (error: unknown) => {
      pending = null;
      throw error;
    }
  );
  return pending;
}

/** The Excel export module if it has finished loading, otherwise null */
export function getLoadedExcelExport(): ExcelExportModule | null {
  return loaded;
}

/** The Excel export module, loading it first if needed */
export async function loadExcelExport(): Promise<ExcelExportModule> {
  return getLoadedExcelExport() ?? preloadExcelExport();
}
