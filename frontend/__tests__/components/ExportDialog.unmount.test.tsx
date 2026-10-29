/**
 * ExportDialog: an export that finishes after the dialog has unmounted must not
 * touch the component any more.
 *
 * CI (PR #78) failed with an unhandled rejection, "ReferenceError: window is not
 * defined", raised from `setIsExporting(false)` in handleExport's `finally` after the
 * test environment had been torn down: the export promise resolved late and the
 * handler still called setState and onClose on an unmounted dialog.
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen, userEvent } from '../testUtils';
import { ExportDialog } from '@/components/ExportDialog';
import type { CalculationStatusResponse } from '@/types/api.types';

vi.mock('@/utils/export/csvExport', () => ({
  exportToCSV: vi.fn(),
}));
vi.mock('@/utils/export/excelExport', () => ({
  exportToExcel: vi.fn(),
}));

import { exportToCSV } from '@/utils/export/csvExport';

const results: CalculationStatusResponse = {
  calculation_id: 'calc-123',
  status: 'completed',
  product_id: 'prod-456',
  created_at: '2024-06-15T10:30:00Z',
  total_co2e_kg: 2.5,
};

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

describe('ExportDialog after unmount', () => {
  it('does not call onClose when the export resolves after the dialog unmounted', async () => {
    const pending = deferred<void>();
    vi.mocked(exportToCSV).mockReturnValueOnce(pending.promise);
    const onClose = vi.fn();
    const user = userEvent.setup();

    const { unmount } = render(
      <ExportDialog open onClose={onClose} results={results} productName="Test Widget" productCode="TW-001" />
    );
    await user.click(screen.getByRole('button', { name: /^export$/i }));
    expect(exportToCSV).toHaveBeenCalledTimes(1);

    unmount();
    pending.resolve();
    await pending.promise;
    await new Promise((r) => setTimeout(r, 0));

    expect(onClose).not.toHaveBeenCalled();
  });

  it('does not surface an error state when the export rejects after unmount', async () => {
    const pending = deferred<void>();
    vi.mocked(exportToCSV).mockReturnValueOnce(pending.promise);
    const onClose = vi.fn();
    const user = userEvent.setup();

    const { unmount } = render(
      <ExportDialog open onClose={onClose} results={results} productName="Test Widget" productCode="TW-001" />
    );
    await user.click(screen.getByRole('button', { name: /^export$/i }));

    unmount();
    pending.reject(new Error('disk full'));
    await pending.promise.catch(() => undefined);
    await new Promise((r) => setTimeout(r, 0));

    // Nothing to assert on screen (it is gone); the test fails on an unhandled
    // rejection or a thrown setState. onClose must still not have fired.
    expect(onClose).not.toHaveBeenCalled();
  });
});
