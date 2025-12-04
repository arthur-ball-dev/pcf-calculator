/**
 * Mock Sync Logs Data
 * TASK-FE-P5-001: MSW Mock Server Setup
 *
 * Historical sync operation logs for data sources.
 */

export interface MockSyncLog {
  id: string;
  data_source: {
    id: string;
    name: string;
  };
  sync_type: 'scheduled' | 'manual' | 'initial';
  status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'cancelled';
  celery_task_id: string | null;
  started_at: string;
  completed_at: string | null;
  duration_seconds: number | null;
  records_processed: number;
  records_created: number;
  records_updated: number;
  records_skipped: number;
  records_failed: number;
  error_message: string | null;
  error_details: Array<{
    record_id: string | null;
    field: string | null;
    message: string;
  }> | null;
  metadata: {
    file_name: string | null;
    file_size_bytes: number | null;
    api_calls_made: number | null;
    triggered_by: string | null;
  } | null;
  created_at: string;
}

// Data sources reference
const dataSources = {
  EPA: {
    id: '550e8400-e29b-41d4-a716-446655440001',
    name: 'EPA GHG Emission Factors Hub',
  },
  DEFRA: {
    id: '550e8400-e29b-41d4-a716-446655440002',
    name: 'DEFRA Conversion Factors',
  },
  EXIOBASE: {
    id: '550e8400-e29b-41d4-a716-446655440003',
    name: 'Exiobase',
  },
};

// Generate UUID
function generateUUID(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

// Generate sync logs
function generateSyncLogs(): MockSyncLog[] {
  const logs: MockSyncLog[] = [];
  const now = new Date();

  // EPA syncs - successful history
  for (let i = 0; i < 10; i++) {
    const startDate = new Date(now.getTime() - (i * 14 + 1) * 24 * 60 * 60 * 1000);
    const duration = 300 + Math.floor(Math.random() * 60);
    const endDate = new Date(startDate.getTime() + duration * 1000);

    logs.push({
      id: generateUUID(),
      data_source: dataSources.EPA,
      sync_type: 'scheduled',
      status: 'completed',
      celery_task_id: `celery-task-epa-${generateUUID().slice(0, 8)}`,
      started_at: startDate.toISOString(),
      completed_at: endDate.toISOString(),
      duration_seconds: duration,
      records_processed: 280 + Math.floor(Math.random() * 20),
      records_created: Math.floor(Math.random() * 20),
      records_updated: Math.floor(Math.random() * 15),
      records_skipped: 250 + Math.floor(Math.random() * 20),
      records_failed: 0,
      error_message: null,
      error_details: null,
      metadata: {
        file_name: `ghg_emission_factors_${2023 - Math.floor(i / 2)}.xlsx`,
        file_size_bytes: 1500000 + Math.floor(Math.random() * 100000),
        api_calls_made: null,
        triggered_by: 'celery_beat',
      },
      created_at: startDate.toISOString(),
    });
  }

  // DEFRA syncs - mostly successful with a few minor issues
  for (let i = 0; i < 10; i++) {
    const startDate = new Date(now.getTime() - (i * 14 + 2) * 24 * 60 * 60 * 1000);
    const duration = 480 + Math.floor(Math.random() * 120);
    const endDate = new Date(startDate.getTime() + duration * 1000);
    const recordsFailed = i === 3 ? 5 : i === 7 ? 2 : 0;

    logs.push({
      id: generateUUID(),
      data_source: dataSources.DEFRA,
      sync_type: i === 5 ? 'manual' : 'scheduled',
      status: 'completed',
      celery_task_id: `celery-task-defra-${generateUUID().slice(0, 8)}`,
      started_at: startDate.toISOString(),
      completed_at: endDate.toISOString(),
      duration_seconds: duration,
      records_processed: 370 + Math.floor(Math.random() * 30),
      records_created: 10 + Math.floor(Math.random() * 15),
      records_updated: 15 + Math.floor(Math.random() * 20),
      records_skipped: 340 + Math.floor(Math.random() * 20),
      records_failed: recordsFailed,
      error_message: recordsFailed > 0 ? 'Some records failed validation' : null,
      error_details: recordsFailed > 0
        ? [
            {
              record_id: 'DEFRA-2023-ERR-001',
              field: 'co2e_factor',
              message: 'Value out of expected range',
            },
          ]
        : null,
      metadata: {
        file_name: `defra_conversion_factors_${2024 - Math.floor(i / 3)}.xlsx`,
        file_size_bytes: 2500000 + Math.floor(Math.random() * 200000),
        api_calls_made: null,
        triggered_by: i === 5 ? 'admin_user@example.com' : 'celery_beat',
      },
      created_at: startDate.toISOString(),
    });
  }

  // EXIOBASE syncs - some failures
  for (let i = 0; i < 8; i++) {
    const startDate = new Date(now.getTime() - (i * 30 + 5) * 24 * 60 * 60 * 1000);
    const isFailed = i === 0 || i === 2;
    const duration = isFailed ? 900 : 1800 + Math.floor(Math.random() * 600);
    const endDate = new Date(startDate.getTime() + duration * 1000);

    logs.push({
      id: generateUUID(),
      data_source: dataSources.EXIOBASE,
      sync_type: i === 4 ? 'manual' : 'scheduled',
      status: isFailed ? 'failed' : 'completed',
      celery_task_id: `celery-task-exio-${generateUUID().slice(0, 8)}`,
      started_at: startDate.toISOString(),
      completed_at: endDate.toISOString(),
      duration_seconds: duration,
      records_processed: isFailed ? 500 : 1200 + Math.floor(Math.random() * 100),
      records_created: isFailed ? 0 : 20 + Math.floor(Math.random() * 30),
      records_updated: isFailed ? 0 : 50 + Math.floor(Math.random() * 50),
      records_skipped: isFailed ? 0 : 1100 + Math.floor(Math.random() * 50),
      records_failed: isFailed ? 500 : Math.floor(Math.random() * 5),
      error_message: isFailed ? 'Connection timeout while downloading file' : null,
      error_details: isFailed
        ? [
            {
              record_id: null,
              field: null,
              message: 'HTTP 504: Gateway timeout after 5 retries',
            },
          ]
        : null,
      metadata: {
        file_name: 'exiobase_v3.8.2.zip',
        file_size_bytes: isFailed ? null : 85000000,
        api_calls_made: isFailed ? 5 : 1,
        triggered_by: i === 4 ? 'admin_user@example.com' : 'celery_beat',
      },
      created_at: startDate.toISOString(),
    });
  }

  // Add one in-progress sync
  logs.push({
    id: generateUUID(),
    data_source: dataSources.EPA,
    sync_type: 'manual',
    status: 'in_progress',
    celery_task_id: `celery-task-epa-live-${generateUUID().slice(0, 8)}`,
    started_at: new Date(now.getTime() - 2 * 60 * 1000).toISOString(), // 2 minutes ago
    completed_at: null,
    duration_seconds: null,
    records_processed: 145,
    records_created: 3,
    records_updated: 2,
    records_skipped: 140,
    records_failed: 0,
    error_message: null,
    error_details: null,
    metadata: {
      file_name: 'ghg_emission_factors_2024.xlsx',
      file_size_bytes: 1650000,
      api_calls_made: null,
      triggered_by: 'test_admin@example.com',
    },
    created_at: new Date(now.getTime() - 2 * 60 * 1000).toISOString(),
  });

  // Sort by started_at descending
  logs.sort((a, b) => new Date(b.started_at).getTime() - new Date(a.started_at).getTime());

  return logs;
}

export const mockSyncLogs: MockSyncLog[] = generateSyncLogs();

// Filter helper for sync logs
export function filterSyncLogs(
  logs: MockSyncLog[],
  filters: {
    data_source_id?: string;
    status?: string;
    sync_type?: string;
    start_date?: string;
    end_date?: string;
    has_errors?: boolean;
    sort_by?: string;
    sort_order?: 'asc' | 'desc';
  }
): MockSyncLog[] {
  let filtered = [...logs];

  if (filters.data_source_id) {
    filtered = filtered.filter((l) => l.data_source.id === filters.data_source_id);
  }

  if (filters.status) {
    filtered = filtered.filter((l) => l.status === filters.status);
  }

  if (filters.sync_type) {
    filtered = filtered.filter((l) => l.sync_type === filters.sync_type);
  }

  if (filters.start_date) {
    const startDate = new Date(filters.start_date);
    filtered = filtered.filter((l) => new Date(l.started_at) >= startDate);
  }

  if (filters.end_date) {
    const endDate = new Date(filters.end_date);
    endDate.setHours(23, 59, 59, 999);
    filtered = filtered.filter((l) => new Date(l.started_at) <= endDate);
  }

  if (filters.has_errors) {
    filtered = filtered.filter((l) => l.records_failed > 0);
  }

  // Sorting
  if (filters.sort_by) {
    const order = filters.sort_order === 'asc' ? 1 : -1;
    filtered.sort((a, b) => {
      const aVal = a[filters.sort_by as keyof MockSyncLog];
      const bVal = b[filters.sort_by as keyof MockSyncLog];
      if (aVal === null) return 1;
      if (bVal === null) return -1;
      if (typeof aVal === 'number' && typeof bVal === 'number') {
        return (aVal - bVal) * order;
      }
      if (filters.sort_by === 'started_at' || filters.sort_by === 'completed_at') {
        return (new Date(aVal as string).getTime() - new Date(bVal as string).getTime()) * order;
      }
      return String(aVal).localeCompare(String(bVal)) * order;
    });
  }

  return filtered;
}

// Generate summary statistics
export function generateSyncLogsSummary(logs: MockSyncLog[]) {
  const completedSyncs = logs.filter((l) => l.status === 'completed');
  const failedSyncs = logs.filter((l) => l.status === 'failed');

  const totalRecordsProcessed = logs.reduce((sum, l) => sum + l.records_processed, 0);
  const totalRecordsFailed = logs.reduce((sum, l) => sum + l.records_failed, 0);

  const completedWithDuration = completedSyncs.filter((l) => l.duration_seconds !== null);
  const averageDuration =
    completedWithDuration.length > 0
      ? completedWithDuration.reduce((sum, l) => sum + (l.duration_seconds || 0), 0) /
        completedWithDuration.length
      : 0;

  return {
    total_syncs: logs.length,
    completed_syncs: completedSyncs.length,
    failed_syncs: failedSyncs.length,
    total_records_processed: totalRecordsProcessed,
    total_records_failed: totalRecordsFailed,
    average_duration_seconds: Math.round(averageDuration * 10) / 10,
  };
}
