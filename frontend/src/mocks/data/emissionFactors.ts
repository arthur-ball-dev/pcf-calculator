/**
 * Mock Emission Factors Data
 * TASK-FE-P5-001: MSW Mock Server Setup
 *
 * Emission factors from EPA, DEFRA, and EXIOBASE sources
 * with Phase 5 enhanced fields.
 */

export interface MockEmissionFactor {
  id: string;
  activity_name: string;
  co2e_factor: number;
  unit: string;
  data_source: 'EPA_GHG_HUB' | 'DEFRA_CONVERSION' | 'EXIOBASE' | 'ECOINVENT' | 'CUSTOM';
  data_source_id: string | null;
  external_id: string | null;
  geography: string;
  reference_year: number | null;
  data_quality_rating: number | null;
  uncertainty_min: number | null;
  uncertainty_max: number | null;
  is_active: boolean;
  relevance_score: number | null;
  sync_batch_id: string | null;
  created_at: string;
  updated_at: string;
}

// Data source IDs
const dataSourceIds = {
  EPA: '550e8400-e29b-41d4-a716-446655440001',
  DEFRA: '550e8400-e29b-41d4-a716-446655440002',
  EXIOBASE: '550e8400-e29b-41d4-a716-446655440003',
};

// Sync batch IDs
const syncBatchIds = {
  EPA: '770e8400-e29b-41d4-a716-446655440001',
  DEFRA: '770e8400-e29b-41d4-a716-446655440002',
  EXIOBASE: '770e8400-e29b-41d4-a716-446655440003',
};

// Generate UUID
function generateUUID(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

// EPA emission factors
const epaFactors: MockEmissionFactor[] = [
  // Electricity
  {
    id: generateUUID(),
    activity_name: 'Electricity, grid mix, US average',
    co2e_factor: 0.417,
    unit: 'kWh',
    data_source: 'EPA_GHG_HUB',
    data_source_id: dataSourceIds.EPA,
    external_id: 'EPA-EGRID-2022-US',
    geography: 'US',
    reference_year: 2022,
    data_quality_rating: 0.92,
    uncertainty_min: 0.38,
    uncertainty_max: 0.45,
    is_active: true,
    relevance_score: null,
    sync_batch_id: syncBatchIds.EPA,
    created_at: '2025-11-15T08:00:00Z',
    updated_at: '2025-11-15T08:00:00Z',
  },
  {
    id: generateUUID(),
    activity_name: 'Electricity, renewable sources, US',
    co2e_factor: 0.021,
    unit: 'kWh',
    data_source: 'EPA_GHG_HUB',
    data_source_id: dataSourceIds.EPA,
    external_id: 'EPA-EGRID-2022-US-REN',
    geography: 'US',
    reference_year: 2022,
    data_quality_rating: 0.90,
    uncertainty_min: 0.015,
    uncertainty_max: 0.028,
    is_active: true,
    relevance_score: null,
    sync_batch_id: syncBatchIds.EPA,
    created_at: '2025-11-15T08:00:00Z',
    updated_at: '2025-11-15T08:00:00Z',
  },
  // Natural Gas
  {
    id: generateUUID(),
    activity_name: 'Natural gas, combustion',
    co2e_factor: 2.02,
    unit: 'm3',
    data_source: 'EPA_GHG_HUB',
    data_source_id: dataSourceIds.EPA,
    external_id: 'EPA-NG-2023',
    geography: 'US',
    reference_year: 2023,
    data_quality_rating: 0.95,
    uncertainty_min: 1.92,
    uncertainty_max: 2.12,
    is_active: true,
    relevance_score: null,
    sync_batch_id: syncBatchIds.EPA,
    created_at: '2025-11-15T08:00:00Z',
    updated_at: '2025-11-15T08:00:00Z',
  },
  // Transport
  {
    id: generateUUID(),
    activity_name: 'Road freight, truck, average',
    co2e_factor: 0.089,
    unit: 'tkm',
    data_source: 'EPA_GHG_HUB',
    data_source_id: dataSourceIds.EPA,
    external_id: 'EPA-TRANS-TRUCK-2023',
    geography: 'US',
    reference_year: 2023,
    data_quality_rating: 0.85,
    uncertainty_min: 0.075,
    uncertainty_max: 0.105,
    is_active: true,
    relevance_score: null,
    sync_batch_id: syncBatchIds.EPA,
    created_at: '2025-11-15T08:00:00Z',
    updated_at: '2025-11-15T08:00:00Z',
  },
];

// DEFRA emission factors
const defraFactors: MockEmissionFactor[] = [
  {
    id: generateUUID(),
    activity_name: 'Electricity, grid mix, UK',
    co2e_factor: 0.212,
    unit: 'kWh',
    data_source: 'DEFRA_CONVERSION',
    data_source_id: dataSourceIds.DEFRA,
    external_id: 'DEFRA-2023-ELEC-UK',
    geography: 'GB',
    reference_year: 2023,
    data_quality_rating: 0.88,
    uncertainty_min: 0.19,
    uncertainty_max: 0.23,
    is_active: true,
    relevance_score: null,
    sync_batch_id: syncBatchIds.DEFRA,
    created_at: '2025-11-20T10:30:00Z',
    updated_at: '2025-11-20T10:30:00Z',
  },
  {
    id: generateUUID(),
    activity_name: 'Diesel, combustion',
    co2e_factor: 2.68,
    unit: 'L',
    data_source: 'DEFRA_CONVERSION',
    data_source_id: dataSourceIds.DEFRA,
    external_id: 'DEFRA-2023-DIESEL',
    geography: 'GB',
    reference_year: 2023,
    data_quality_rating: 0.90,
    uncertainty_min: 2.55,
    uncertainty_max: 2.82,
    is_active: true,
    relevance_score: null,
    sync_batch_id: syncBatchIds.DEFRA,
    created_at: '2025-11-20T10:30:00Z',
    updated_at: '2025-11-20T10:30:00Z',
  },
  {
    id: generateUUID(),
    activity_name: 'Petrol, combustion',
    co2e_factor: 2.31,
    unit: 'L',
    data_source: 'DEFRA_CONVERSION',
    data_source_id: dataSourceIds.DEFRA,
    external_id: 'DEFRA-2023-PETROL',
    geography: 'GB',
    reference_year: 2023,
    data_quality_rating: 0.90,
    uncertainty_min: 2.20,
    uncertainty_max: 2.42,
    is_active: true,
    relevance_score: null,
    sync_batch_id: syncBatchIds.DEFRA,
    created_at: '2025-11-20T10:30:00Z',
    updated_at: '2025-11-20T10:30:00Z',
  },
  {
    id: generateUUID(),
    activity_name: 'Air freight, long-haul',
    co2e_factor: 1.13,
    unit: 'tkm',
    data_source: 'DEFRA_CONVERSION',
    data_source_id: dataSourceIds.DEFRA,
    external_id: 'DEFRA-2023-AIR-LH',
    geography: 'GB',
    reference_year: 2023,
    data_quality_rating: 0.82,
    uncertainty_min: 0.95,
    uncertainty_max: 1.35,
    is_active: true,
    relevance_score: null,
    sync_batch_id: syncBatchIds.DEFRA,
    created_at: '2025-11-20T10:30:00Z',
    updated_at: '2025-11-20T10:30:00Z',
  },
];

// EXIOBASE emission factors (more extensive list)
const exiobaseGeographies = ['US', 'CN', 'DE', 'JP', 'GB', 'FR', 'IT', 'KR', 'IN', 'BR', 'GLO'];
const exiobaseActivities = [
  { name: 'Steel production, primary', factor: 1.89, unit: 'kg' },
  { name: 'Steel production, secondary', factor: 0.42, unit: 'kg' },
  { name: 'Aluminum production, primary', factor: 8.24, unit: 'kg' },
  { name: 'Aluminum production, secondary', factor: 0.65, unit: 'kg' },
  { name: 'Plastic production, HDPE', factor: 1.92, unit: 'kg' },
  { name: 'Plastic production, PET', factor: 2.73, unit: 'kg' },
  { name: 'Glass production, container', factor: 0.86, unit: 'kg' },
  { name: 'Paper production, virgin', factor: 1.29, unit: 'kg' },
  { name: 'Paper production, recycled', factor: 0.67, unit: 'kg' },
  { name: 'Cotton fabric production', factor: 8.5, unit: 'kg' },
  { name: 'Polyester fabric production', factor: 5.5, unit: 'kg' },
  { name: 'Cement production', factor: 0.91, unit: 'kg' },
  { name: 'Concrete production', factor: 0.13, unit: 'kg' },
  { name: 'Copper production', factor: 3.81, unit: 'kg' },
  { name: 'Lithium-ion battery production', factor: 75.0, unit: 'kWh' },
  { name: 'Semiconductor production', factor: 25.0, unit: 'kg' },
  { name: 'Circuit board production', factor: 18.5, unit: 'kg' },
  { name: 'Display panel production', factor: 45.0, unit: 'm2' },
];

const exiobaseFactors: MockEmissionFactor[] = [];
let exiobaseIndex = 0;

for (const activity of exiobaseActivities) {
  for (const geo of exiobaseGeographies.slice(0, 5)) {
    // Vary the factor by geography
    const geoMultiplier = geo === 'CN' ? 1.2 : geo === 'DE' ? 0.85 : geo === 'US' ? 1.0 : 0.95;

    exiobaseFactors.push({
      id: generateUUID(),
      activity_name: `${activity.name}`,
      co2e_factor: Math.round(activity.factor * geoMultiplier * 100) / 100,
      unit: activity.unit,
      data_source: 'EXIOBASE',
      data_source_id: dataSourceIds.EXIOBASE,
      external_id: `EXIO-${exiobaseIndex.toString().padStart(5, '0')}`,
      geography: geo,
      reference_year: 2021,
      data_quality_rating: 0.7 + Math.random() * 0.15,
      uncertainty_min: Math.round(activity.factor * geoMultiplier * 0.85 * 100) / 100,
      uncertainty_max: Math.round(activity.factor * geoMultiplier * 1.15 * 100) / 100,
      is_active: true,
      relevance_score: null,
      sync_batch_id: syncBatchIds.EXIOBASE,
      created_at: '2025-10-01T00:00:00Z',
      updated_at: '2025-10-01T00:00:00Z',
    });
    exiobaseIndex++;
  }
}

// Combined emission factors
export const mockEmissionFactors: MockEmissionFactor[] = [
  ...epaFactors,
  ...defraFactors,
  ...exiobaseFactors,
];

// Filter helper for emission factors
export function filterEmissionFactors(
  factors: MockEmissionFactor[],
  filters: {
    query?: string;
    data_source?: string;
    data_source_id?: string;
    geography?: string;
    unit?: string;
    reference_year?: number;
    min_quality?: number;
    is_active?: boolean;
    sort_by?: string;
    sort_order?: 'asc' | 'desc';
  }
): MockEmissionFactor[] {
  let filtered = [...factors];

  if (filters.query) {
    const query = filters.query.toLowerCase();
    filtered = filtered.filter((f) =>
      f.activity_name.toLowerCase().includes(query)
    );
    // Add relevance scores
    filtered = filtered.map((f) => ({
      ...f,
      relevance_score: f.activity_name.toLowerCase().startsWith(query) ? 0.95 : 0.75,
    }));
  }

  if (filters.data_source) {
    filtered = filtered.filter((f) => f.data_source === filters.data_source);
  }

  if (filters.data_source_id) {
    filtered = filtered.filter((f) => f.data_source_id === filters.data_source_id);
  }

  if (filters.geography) {
    filtered = filtered.filter((f) => f.geography === filters.geography);
  }

  if (filters.unit) {
    filtered = filtered.filter((f) => f.unit === filters.unit);
  }

  if (filters.reference_year) {
    filtered = filtered.filter((f) => f.reference_year === filters.reference_year);
  }

  if (filters.min_quality !== undefined) {
    filtered = filtered.filter(
      (f) => f.data_quality_rating !== null && f.data_quality_rating >= filters.min_quality!
    );
  }

  if (filters.is_active !== undefined) {
    filtered = filtered.filter((f) => f.is_active === filters.is_active);
  }

  // Sorting
  if (filters.sort_by) {
    const order = filters.sort_order === 'desc' ? -1 : 1;
    filtered.sort((a, b) => {
      const aVal = a[filters.sort_by as keyof MockEmissionFactor];
      const bVal = b[filters.sort_by as keyof MockEmissionFactor];
      if (aVal === null) return 1;
      if (bVal === null) return -1;
      if (typeof aVal === 'number' && typeof bVal === 'number') {
        return (aVal - bVal) * order;
      }
      return String(aVal).localeCompare(String(bVal)) * order;
    });
  }

  return filtered;
}

// Generate aggregations for search results
export function generateAggregations(factors: MockEmissionFactor[]) {
  const bySource: Record<string, number> = {};
  const byGeography: Record<string, number> = {};

  for (const f of factors) {
    bySource[f.data_source] = (bySource[f.data_source] || 0) + 1;
    byGeography[f.geography] = (byGeography[f.geography] || 0) + 1;
  }

  return {
    by_source: Object.entries(bySource).map(([source, count]) => ({ source, count })),
    by_geography: Object.entries(byGeography).map(([geography, count]) => ({ geography, count })),
  };
}

export { dataSourceIds, syncBatchIds };
