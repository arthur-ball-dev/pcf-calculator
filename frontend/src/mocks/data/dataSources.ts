/**
 * Mock Data Sources Configuration
 * TASK-FE-P5-001: MSW Mock Server Setup
 *
 * EPA, DEFRA, and Exiobase data source configurations
 * with sync status and statistics.
 */

export interface MockDataSource {
  id: string;
  name: string;
  source_type: 'api' | 'file' | 'database' | 'manual';
  base_url: string | null;
  sync_frequency: 'daily' | 'weekly' | 'biweekly' | 'monthly' | 'manual';
  is_active: boolean;
  last_sync: {
    sync_id: string;
    status: 'completed' | 'failed' | 'in_progress' | 'cancelled';
    started_at: string;
    completed_at: string | null;
    records_processed: number;
    records_created: number;
    records_updated: number;
    records_failed: number;
    error_message: string | null;
  } | null;
  next_scheduled_sync: string | null;
  statistics: {
    total_factors: number;
    active_factors: number;
    average_quality: number | null;
    geographies_covered: number;
    oldest_reference_year: number | null;
    newest_reference_year: number | null;
  };
  created_at: string;
}

export const mockDataSources: MockDataSource[] = [
  {
    id: '550e8400-e29b-41d4-a716-446655440001',
    name: 'EPA GHG Emission Factors Hub',
    source_type: 'file',
    base_url: 'https://www.epa.gov/climateleadership/ghg-emission-factors-hub',
    sync_frequency: 'biweekly',
    is_active: true,
    last_sync: {
      sync_id: '660e8400-e29b-41d4-a716-446655440001',
      status: 'completed',
      started_at: '2025-12-01T02:00:00Z',
      completed_at: '2025-12-01T02:05:30Z',
      records_processed: 285,
      records_created: 12,
      records_updated: 8,
      records_failed: 0,
      error_message: null,
    },
    next_scheduled_sync: '2025-12-15T02:00:00Z',
    statistics: {
      total_factors: 285,
      active_factors: 280,
      average_quality: 0.90,
      geographies_covered: 2,
      oldest_reference_year: 2020,
      newest_reference_year: 2023,
    },
    created_at: '2025-10-01T00:00:00Z',
  },
  {
    id: '550e8400-e29b-41d4-a716-446655440002',
    name: 'DEFRA Conversion Factors',
    source_type: 'file',
    base_url: 'https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors',
    sync_frequency: 'biweekly',
    is_active: true,
    last_sync: {
      sync_id: '660e8400-e29b-41d4-a716-446655440002',
      status: 'completed',
      started_at: '2025-12-02T03:00:00Z',
      completed_at: '2025-12-02T03:08:15Z',
      records_processed: 380,
      records_created: 15,
      records_updated: 22,
      records_failed: 2,
      error_message: null,
    },
    next_scheduled_sync: '2025-12-16T03:00:00Z',
    statistics: {
      total_factors: 378,
      active_factors: 375,
      average_quality: 0.88,
      geographies_covered: 1,
      oldest_reference_year: 2021,
      newest_reference_year: 2024,
    },
    created_at: '2025-10-01T00:00:00Z',
  },
  {
    id: '550e8400-e29b-41d4-a716-446655440003',
    name: 'Exiobase',
    source_type: 'file',
    base_url: 'https://zenodo.org/record/5589597',
    sync_frequency: 'monthly',
    is_active: true,
    last_sync: {
      sync_id: '660e8400-e29b-41d4-a716-446655440003',
      status: 'failed',
      started_at: '2025-11-28T04:00:00Z',
      completed_at: '2025-11-28T04:15:00Z',
      records_processed: 500,
      records_created: 0,
      records_updated: 0,
      records_failed: 500,
      error_message: 'Connection timeout while downloading file',
    },
    next_scheduled_sync: '2025-12-05T04:00:00Z',
    statistics: {
      total_factors: 1250,
      active_factors: 1200,
      average_quality: 0.75,
      geographies_covered: 49,
      oldest_reference_year: 2019,
      newest_reference_year: 2022,
    },
    created_at: '2025-10-15T00:00:00Z',
  },
  {
    id: '550e8400-e29b-41d4-a716-446655440004',
    name: 'Ecoinvent (Manual)',
    source_type: 'manual',
    base_url: null,
    sync_frequency: 'manual',
    is_active: false,
    last_sync: null,
    next_scheduled_sync: null,
    statistics: {
      total_factors: 0,
      active_factors: 0,
      average_quality: null,
      geographies_covered: 0,
      oldest_reference_year: null,
      newest_reference_year: null,
    },
    created_at: '2025-11-01T00:00:00Z',
  },
];

// Filter helper for data sources
export function filterDataSources(
  sources: MockDataSource[],
  filters: {
    is_active?: boolean;
    source_type?: string;
  }
): MockDataSource[] {
  let filtered = [...sources];

  if (filters.is_active !== undefined) {
    filtered = filtered.filter((s) => s.is_active === filters.is_active);
  }

  if (filters.source_type) {
    filtered = filtered.filter((s) => s.source_type === filters.source_type);
  }

  return filtered;
}

// Generate summary statistics
export function generateDataSourceSummary(sources: MockDataSource[]) {
  const activeSources = sources.filter((s) => s.is_active);
  const totalEmissionFactors = sources.reduce(
    (sum, s) => sum + s.statistics.total_factors,
    0
  );

  const now = new Date();
  const sevenDaysAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);

  const sourcesWithRecentSync = sources.filter(
    (s) => s.last_sync && new Date(s.last_sync.completed_at || s.last_sync.started_at) > sevenDaysAgo
  ).length;

  const sourcesNeedingSync = sources.filter((s) => {
    if (!s.is_active) return false;
    if (!s.last_sync) return true;
    if (s.last_sync.status === 'failed') return true;
    if (s.next_scheduled_sync && new Date(s.next_scheduled_sync) < now) return true;
    return false;
  }).length;

  return {
    total_sources: sources.length,
    active_sources: activeSources.length,
    total_emission_factors: totalEmissionFactors,
    sources_with_recent_sync: sourcesWithRecentSync,
    sources_needing_sync: sourcesNeedingSync,
  };
}
