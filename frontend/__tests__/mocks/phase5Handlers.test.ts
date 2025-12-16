/**
 * Phase 5 MSW Handlers Unit Tests
 * TASK-FE-P5-001: MSW Mock Server Setup
 *
 * TDD Tests - Written BEFORE implementation
 * Tests for all Phase 5 API endpoint mock handlers
 */

import { describe, it, expect, beforeAll, afterAll, afterEach } from 'vitest';
import { setupServer } from 'msw/node';
import axios from 'axios';

// These imports will be created during implementation
import { phase5Handlers } from '../../src/mocks/handlers/phase5Handlers';

const API_BASE_URL = 'http://localhost:8000';
const server = setupServer(...phase5Handlers);

beforeAll(() => {
  server.listen({ onUnhandledRequest: 'error' });
});

afterEach(() => {
  server.resetHandlers();
});

afterAll(() => {
  server.close();
});

// ============================================================================
// Product Search Endpoint Tests
// ============================================================================

describe('GET /api/v1/products/search', () => {
  const endpoint = `${API_BASE_URL}/api/v1/products/search`;

  it('returns valid JSON structure matching contract schema', async () => {
    const response = await axios.get(endpoint);

    expect(response.status).toBe(200);
    expect(response.data).toHaveProperty('items');
    expect(response.data).toHaveProperty('total');
    expect(response.data).toHaveProperty('limit');
    expect(response.data).toHaveProperty('offset');
    expect(response.data).toHaveProperty('has_more');
    expect(Array.isArray(response.data.items)).toBe(true);
  });

  it('returns products with all required fields', async () => {
    const response = await axios.get(endpoint);
    const item = response.data.items[0];

    expect(item).toHaveProperty('id');
    expect(item).toHaveProperty('code');
    expect(item).toHaveProperty('name');
    expect(item).toHaveProperty('unit');
    expect(item).toHaveProperty('is_finished_product');
    expect(item).toHaveProperty('created_at');
  });

  it('filters by query parameter', async () => {
    const response = await axios.get(`${endpoint}?query=laptop`);

    expect(response.status).toBe(200);
    response.data.items.forEach((item: { name: string; description?: string }) => {
      const matchesQuery =
        item.name.toLowerCase().includes('laptop') ||
        item.description?.toLowerCase().includes('laptop');
      expect(matchesQuery).toBe(true);
    });
  });

  it('filters by category_id parameter', async () => {
    // First get a category ID from the response
    const initialResponse = await axios.get(endpoint);
    const productWithCategory = initialResponse.data.items.find(
      (item: { category?: { id: string } }) => item.category?.id
    );

    if (productWithCategory?.category?.id) {
      const categoryId = productWithCategory.category.id;
      const response = await axios.get(`${endpoint}?category_id=${categoryId}`);

      expect(response.status).toBe(200);
      response.data.items.forEach((item: { category?: { id: string } }) => {
        expect(item.category?.id).toBe(categoryId);
      });
    }
  });

  it('filters by industry parameter', async () => {
    const response = await axios.get(`${endpoint}?industry=electronics`);

    expect(response.status).toBe(200);
    response.data.items.forEach((item: { category?: { industry_sector: string } }) => {
      expect(item.category?.industry_sector).toBe('electronics');
    });
  });

  it('respects limit parameter', async () => {
    const limit = 10;
    const response = await axios.get(`${endpoint}?limit=${limit}`);

    expect(response.status).toBe(200);
    expect(response.data.items.length).toBeLessThanOrEqual(limit);
    expect(response.data.limit).toBe(limit);
  });

  it('respects offset parameter for pagination', async () => {
    const limit = 10;
    const offset = 10;
    const response = await axios.get(`${endpoint}?limit=${limit}&offset=${offset}`);

    expect(response.status).toBe(200);
    expect(response.data.offset).toBe(offset);
  });

  it('calculates has_more correctly', async () => {
    const limit = 10;
    const response = await axios.get(`${endpoint}?limit=${limit}&offset=0`);

    const expectedHasMore = response.data.offset + limit < response.data.total;
    expect(response.data.has_more).toBe(expectedHasMore);
  });

  it('returns empty results for non-matching query', async () => {
    const response = await axios.get(`${endpoint}?query=xyz123nonexistent`);

    expect(response.status).toBe(200);
    expect(response.data.items).toEqual([]);
    expect(response.data.total).toBe(0);
    expect(response.data.has_more).toBe(false);
  });

  it('product categories have correct structure', async () => {
    const response = await axios.get(endpoint);
    const productWithCategory = response.data.items.find(
      (item: { category?: object }) => item.category
    );

    if (productWithCategory?.category) {
      expect(productWithCategory.category).toHaveProperty('id');
      expect(productWithCategory.category).toHaveProperty('code');
      expect(productWithCategory.category).toHaveProperty('name');
      expect(productWithCategory.category).toHaveProperty('industry_sector');
    }
  });
});

// ============================================================================
// Product Categories Endpoint Tests
// ============================================================================

describe('GET /api/v1/products/categories', () => {
  const endpoint = `${API_BASE_URL}/api/v1/products/categories`;

  it('returns valid JSON structure matching contract schema', async () => {
    const response = await axios.get(endpoint);

    expect(response.status).toBe(200);
    expect(response.data).toHaveProperty('categories');
    expect(response.data).toHaveProperty('total_categories');
    expect(response.data).toHaveProperty('max_depth');
    expect(Array.isArray(response.data.categories)).toBe(true);
  });

  it('returns categories with all required fields', async () => {
    const response = await axios.get(endpoint);
    const category = response.data.categories[0];

    expect(category).toHaveProperty('id');
    expect(category).toHaveProperty('code');
    expect(category).toHaveProperty('name');
    expect(category).toHaveProperty('level');
    expect(category).toHaveProperty('children');
    expect(Array.isArray(category.children)).toBe(true);
  });

  it('returns at least 20 categories total', async () => {
    const response = await axios.get(endpoint);

    expect(response.data.total_categories).toBeGreaterThanOrEqual(20);
  });

  it('filters by industry parameter', async () => {
    const response = await axios.get(`${endpoint}?industry=electronics`);

    expect(response.status).toBe(200);
    response.data.categories.forEach((category: { industry_sector?: string }) => {
      expect(category.industry_sector).toBe('electronics');
    });
  });

  it('includes product count when requested', async () => {
    const response = await axios.get(`${endpoint}?include_product_count=true`);

    expect(response.status).toBe(200);
    response.data.categories.forEach((category: { product_count?: number }) => {
      expect(typeof category.product_count).toBe('number');
    });
  });

  it('respects depth parameter', async () => {
    const response = await axios.get(`${endpoint}?depth=1`);

    expect(response.status).toBe(200);
    expect(response.data.max_depth).toBe(1);
  });

  it('supports hierarchical structure with nested children', async () => {
    const response = await axios.get(`${endpoint}?depth=3`);

    const categoryWithChildren = response.data.categories.find(
      (cat: { children?: unknown[] }) => cat.children && cat.children.length > 0
    );

    if (categoryWithChildren) {
      expect(categoryWithChildren.children[0]).toHaveProperty('id');
      expect(categoryWithChildren.children[0]).toHaveProperty('name');
      expect(categoryWithChildren.children[0]).toHaveProperty('level');
    }
  });
});

// ============================================================================
// Emission Factors Endpoint Tests (Enhanced Phase 5)
// ============================================================================

describe('GET /api/v1/emission-factors (Enhanced Phase 5)', () => {
  const endpoint = `${API_BASE_URL}/api/v1/emission-factors`;

  it('returns valid JSON structure matching enhanced contract schema', async () => {
    const response = await axios.get(endpoint);

    expect(response.status).toBe(200);
    expect(response.data).toHaveProperty('items');
    expect(response.data).toHaveProperty('total');
    expect(response.data).toHaveProperty('limit');
    expect(response.data).toHaveProperty('offset');
    expect(response.data).toHaveProperty('has_more');
    expect(Array.isArray(response.data.items)).toBe(true);
  });

  it('returns emission factors with all required fields', async () => {
    const response = await axios.get(endpoint);
    const factor = response.data.items[0];

    expect(factor).toHaveProperty('id');
    expect(factor).toHaveProperty('activity_name');
    expect(factor).toHaveProperty('co2e_factor');
    expect(factor).toHaveProperty('unit');
    expect(factor).toHaveProperty('data_source');
    expect(factor).toHaveProperty('geography');
    expect(factor).toHaveProperty('is_active');
    expect(factor).toHaveProperty('created_at');
    expect(factor).toHaveProperty('updated_at');
  });

  it('includes enhanced Phase 5 fields', async () => {
    const response = await axios.get(endpoint);
    const factor = response.data.items[0];

    // Phase 5 new fields
    expect(factor).toHaveProperty('data_source_id');
    expect(factor).toHaveProperty('external_id');
    expect(factor).toHaveProperty('reference_year');
    expect(factor).toHaveProperty('data_quality_rating');
    expect(factor).toHaveProperty('uncertainty_min');
    expect(factor).toHaveProperty('uncertainty_max');
    expect(factor).toHaveProperty('sync_batch_id');
  });

  it('filters by data_source parameter', async () => {
    const response = await axios.get(`${endpoint}?data_source=EPA_GHG_HUB`);

    expect(response.status).toBe(200);
    response.data.items.forEach((factor: { data_source: string }) => {
      expect(factor.data_source).toBe('EPA_GHG_HUB');
    });
  });

  it('filters by geography parameter', async () => {
    const response = await axios.get(`${endpoint}?geography=US`);

    expect(response.status).toBe(200);
    response.data.items.forEach((factor: { geography: string }) => {
      expect(factor.geography).toBe('US');
    });
  });

  it('filters by min_quality parameter', async () => {
    const minQuality = 0.8;
    const response = await axios.get(`${endpoint}?min_quality=${minQuality}`);

    expect(response.status).toBe(200);
    response.data.items.forEach((factor: { data_quality_rating?: number }) => {
      if (factor.data_quality_rating !== null) {
        expect(factor.data_quality_rating).toBeGreaterThanOrEqual(minQuality);
      }
    });
  });

  it('filters by query parameter', async () => {
    const response = await axios.get(`${endpoint}?query=electricity`);

    expect(response.status).toBe(200);
    response.data.items.forEach((factor: { activity_name: string }) => {
      expect(factor.activity_name.toLowerCase()).toContain('electricity');
    });
  });

  it('supports sorting by co2e_factor', async () => {
    const response = await axios.get(`${endpoint}?sort_by=co2e_factor&sort_order=desc`);

    expect(response.status).toBe(200);
    const factors = response.data.items;
    for (let i = 1; i < factors.length; i++) {
      expect(factors[i - 1].co2e_factor).toBeGreaterThanOrEqual(factors[i].co2e_factor);
    }
  });

  it('includes aggregations when query is provided', async () => {
    const response = await axios.get(`${endpoint}?query=electricity`);

    expect(response.status).toBe(200);
    if (response.data.aggregations) {
      expect(response.data.aggregations).toHaveProperty('by_source');
      expect(response.data.aggregations).toHaveProperty('by_geography');
    }
  });
});

// ============================================================================
// Admin Data Sources Endpoint Tests
// ============================================================================

describe('GET /admin/data-sources', () => {
  const endpoint = `${API_BASE_URL}/admin/data-sources`;

  it('returns valid JSON structure matching contract schema', async () => {
    const response = await axios.get(endpoint);

    expect(response.status).toBe(200);
    expect(response.data).toHaveProperty('data_sources');
    expect(response.data).toHaveProperty('total');
    expect(response.data).toHaveProperty('summary');
    expect(Array.isArray(response.data.data_sources)).toBe(true);
  });

  it('returns data sources with all required fields', async () => {
    const response = await axios.get(endpoint);
    const source = response.data.data_sources[0];

    expect(source).toHaveProperty('id');
    expect(source).toHaveProperty('name');
    expect(source).toHaveProperty('source_type');
    expect(source).toHaveProperty('sync_frequency');
    expect(source).toHaveProperty('is_active');
    expect(source).toHaveProperty('statistics');
    expect(source).toHaveProperty('created_at');
  });

  it('returns at least 3 data sources (EPA, DEFRA, Exiobase)', async () => {
    const response = await axios.get(endpoint);

    expect(response.data.data_sources.length).toBeGreaterThanOrEqual(3);
  });

  it('includes last_sync information', async () => {
    const response = await axios.get(endpoint);
    const sourceWithSync = response.data.data_sources.find(
      (s: { last_sync?: object }) => s.last_sync
    );

    if (sourceWithSync?.last_sync) {
      expect(sourceWithSync.last_sync).toHaveProperty('sync_id');
      expect(sourceWithSync.last_sync).toHaveProperty('status');
      expect(sourceWithSync.last_sync).toHaveProperty('started_at');
      expect(sourceWithSync.last_sync).toHaveProperty('records_processed');
    }
  });

  it('includes statistics for each source', async () => {
    const response = await axios.get(endpoint);
    const source = response.data.data_sources[0];

    expect(source.statistics).toHaveProperty('total_factors');
    expect(source.statistics).toHaveProperty('active_factors');
    expect(source.statistics).toHaveProperty('geographies_covered');
  });

  it('includes summary statistics', async () => {
    const response = await axios.get(endpoint);

    expect(response.data.summary).toHaveProperty('total_sources');
    expect(response.data.summary).toHaveProperty('active_sources');
    expect(response.data.summary).toHaveProperty('total_emission_factors');
    expect(response.data.summary).toHaveProperty('sources_with_recent_sync');
    expect(response.data.summary).toHaveProperty('sources_needing_sync');
  });

  it('filters by is_active parameter', async () => {
    const response = await axios.get(`${endpoint}?is_active=true`);

    expect(response.status).toBe(200);
    response.data.data_sources.forEach((source: { is_active: boolean }) => {
      expect(source.is_active).toBe(true);
    });
  });

  it('filters by source_type parameter', async () => {
    const response = await axios.get(`${endpoint}?source_type=file`);

    expect(response.status).toBe(200);
    response.data.data_sources.forEach((source: { source_type: string }) => {
      expect(source.source_type).toBe('file');
    });
  });
});

// ============================================================================
// Admin Sync Trigger Endpoint Tests
// ============================================================================

describe('POST /admin/data-sources/:id/sync', () => {
  it('returns 202 with task info for valid sync trigger', async () => {
    const dataSourceId = '550e8400-e29b-41d4-a716-446655440001';
    const response = await axios.post(
      `${API_BASE_URL}/admin/data-sources/${dataSourceId}/sync`,
      {}
    );

    expect(response.status).toBe(202);
    expect(response.data).toHaveProperty('task_id');
    expect(response.data).toHaveProperty('sync_log_id');
    expect(response.data).toHaveProperty('status');
    expect(response.data).toHaveProperty('message');
    expect(response.data).toHaveProperty('data_source');
    expect(response.data).toHaveProperty('poll_url');
  });

  it('status is queued or started', async () => {
    const dataSourceId = '550e8400-e29b-41d4-a716-446655440001';
    const response = await axios.post(
      `${API_BASE_URL}/admin/data-sources/${dataSourceId}/sync`,
      {}
    );

    expect(['queued', 'started']).toContain(response.data.status);
  });

  it('accepts force_refresh option', async () => {
    const dataSourceId = '550e8400-e29b-41d4-a716-446655440001';
    const response = await axios.post(
      `${API_BASE_URL}/admin/data-sources/${dataSourceId}/sync`,
      { force_refresh: true }
    );

    expect(response.status).toBe(202);
    expect(response.data.task_id).toBeDefined();
  });

  it('accepts dry_run option', async () => {
    const dataSourceId = '550e8400-e29b-41d4-a716-446655440001';
    const response = await axios.post(
      `${API_BASE_URL}/admin/data-sources/${dataSourceId}/sync`,
      { dry_run: true }
    );

    expect(response.status).toBe(202);
    expect(response.data.message.toLowerCase()).toContain('dry run');
  });

  it('returns 404 for non-existent data source', async () => {
    try {
      await axios.post(
        `${API_BASE_URL}/admin/data-sources/nonexistent-id/sync`,
        {}
      );
    } catch (error: unknown) {
      if (axios.isAxiosError(error)) {
        expect(error.response?.status).toBe(404);
        expect(error.response?.data.error.code).toBe('NOT_FOUND');
      }
    }
  });
});

// ============================================================================
// Admin Sync Logs Endpoint Tests
// ============================================================================

describe('GET /admin/sync-logs', () => {
  const endpoint = `${API_BASE_URL}/admin/sync-logs`;

  it('returns valid JSON structure matching contract schema', async () => {
    const response = await axios.get(endpoint);

    expect(response.status).toBe(200);
    expect(response.data).toHaveProperty('items');
    expect(response.data).toHaveProperty('total');
    expect(response.data).toHaveProperty('limit');
    expect(response.data).toHaveProperty('offset');
    expect(response.data).toHaveProperty('has_more');
    expect(response.data).toHaveProperty('summary');
    expect(Array.isArray(response.data.items)).toBe(true);
  });

  it('returns sync logs with all required fields', async () => {
    const response = await axios.get(endpoint);
    const log = response.data.items[0];

    expect(log).toHaveProperty('id');
    expect(log).toHaveProperty('data_source');
    expect(log).toHaveProperty('sync_type');
    expect(log).toHaveProperty('status');
    expect(log).toHaveProperty('started_at');
    expect(log).toHaveProperty('records_processed');
    expect(log).toHaveProperty('records_created');
    expect(log).toHaveProperty('records_updated');
    expect(log).toHaveProperty('records_failed');
    expect(log).toHaveProperty('created_at');
  });

  it('data_source object has id and name', async () => {
    const response = await axios.get(endpoint);
    const log = response.data.items[0];

    expect(log.data_source).toHaveProperty('id');
    expect(log.data_source).toHaveProperty('name');
  });

  it('includes summary statistics', async () => {
    const response = await axios.get(endpoint);

    expect(response.data.summary).toHaveProperty('total_syncs');
    expect(response.data.summary).toHaveProperty('completed_syncs');
    expect(response.data.summary).toHaveProperty('failed_syncs');
    expect(response.data.summary).toHaveProperty('total_records_processed');
    expect(response.data.summary).toHaveProperty('total_records_failed');
    expect(response.data.summary).toHaveProperty('average_duration_seconds');
  });

  it('filters by data_source_id', async () => {
    const dataSourceId = '550e8400-e29b-41d4-a716-446655440001';
    const response = await axios.get(`${endpoint}?data_source_id=${dataSourceId}`);

    expect(response.status).toBe(200);
    response.data.items.forEach((log: { data_source: { id: string } }) => {
      expect(log.data_source.id).toBe(dataSourceId);
    });
  });

  it('filters by status', async () => {
    const response = await axios.get(`${endpoint}?status=completed`);

    expect(response.status).toBe(200);
    response.data.items.forEach((log: { status: string }) => {
      expect(log.status).toBe('completed');
    });
  });

  it('filters by sync_type', async () => {
    const response = await axios.get(`${endpoint}?sync_type=scheduled`);

    expect(response.status).toBe(200);
    response.data.items.forEach((log: { sync_type: string }) => {
      expect(log.sync_type).toBe('scheduled');
    });
  });

  it('filters by has_errors', async () => {
    const response = await axios.get(`${endpoint}?has_errors=true`);

    expect(response.status).toBe(200);
    response.data.items.forEach((log: { records_failed: number }) => {
      expect(log.records_failed).toBeGreaterThan(0);
    });
  });

  it('respects pagination parameters', async () => {
    const limit = 5;
    const offset = 5;
    const response = await axios.get(`${endpoint}?limit=${limit}&offset=${offset}`);

    expect(response.status).toBe(200);
    expect(response.data.limit).toBe(limit);
    expect(response.data.offset).toBe(offset);
    expect(response.data.items.length).toBeLessThanOrEqual(limit);
  });

  it('sorts by started_at descending by default', async () => {
    const response = await axios.get(endpoint);

    const logs = response.data.items;
    for (let i = 1; i < logs.length; i++) {
      const prevDate = new Date(logs[i - 1].started_at).getTime();
      const currDate = new Date(logs[i].started_at).getTime();
      expect(prevDate).toBeGreaterThanOrEqual(currDate);
    }
  });
});

// ============================================================================
// Admin Coverage Stats Endpoint Tests
// ============================================================================

describe('GET /admin/emission-factors/coverage', () => {
  const endpoint = `${API_BASE_URL}/admin/emission-factors/coverage`;

  it('returns valid JSON structure matching contract schema', async () => {
    const response = await axios.get(endpoint);

    expect(response.status).toBe(200);
    expect(response.data).toHaveProperty('summary');
    expect(response.data).toHaveProperty('by_source');
    expect(response.data).toHaveProperty('by_geography');
    expect(response.data).toHaveProperty('by_category');
    expect(response.data).toHaveProperty('gaps');
  });

  it('summary has all required fields', async () => {
    const response = await axios.get(endpoint);

    expect(response.data.summary).toHaveProperty('total_emission_factors');
    expect(response.data.summary).toHaveProperty('active_emission_factors');
    expect(response.data.summary).toHaveProperty('unique_activities');
    expect(response.data.summary).toHaveProperty('geographies_covered');
    expect(response.data.summary).toHaveProperty('categories_with_factors');
    expect(response.data.summary).toHaveProperty('categories_without_factors');
    expect(response.data.summary).toHaveProperty('average_quality_rating');
    expect(response.data.summary).toHaveProperty('coverage_percentage');
  });

  it('by_source entries have correct structure', async () => {
    const response = await axios.get(endpoint);
    const source = response.data.by_source[0];

    expect(source).toHaveProperty('source_id');
    expect(source).toHaveProperty('source_name');
    expect(source).toHaveProperty('total_factors');
    expect(source).toHaveProperty('active_factors');
    expect(source).toHaveProperty('percentage_of_total');
    expect(source).toHaveProperty('geographies');
    expect(source).toHaveProperty('year_range');
    expect(Array.isArray(source.geographies)).toBe(true);
  });

  it('by_geography entries have correct structure', async () => {
    const response = await axios.get(endpoint);
    const geo = response.data.by_geography[0];

    expect(geo).toHaveProperty('geography');
    expect(geo).toHaveProperty('geography_name');
    expect(geo).toHaveProperty('total_factors');
    expect(geo).toHaveProperty('sources');
    expect(geo).toHaveProperty('percentage_of_total');
  });

  it('by_category entries have correct structure', async () => {
    const response = await axios.get(endpoint);
    const category = response.data.by_category[0];

    expect(category).toHaveProperty('category_id');
    expect(category).toHaveProperty('category_name');
    expect(category).toHaveProperty('category_code');
    expect(category).toHaveProperty('products_count');
    expect(category).toHaveProperty('products_with_factors');
    expect(category).toHaveProperty('coverage_percentage');
    expect(category).toHaveProperty('factors_available');
    expect(category).toHaveProperty('gap_status');
  });

  it('gaps object has required sections', async () => {
    const response = await axios.get(endpoint);

    expect(response.data.gaps).toHaveProperty('missing_geographies');
    expect(response.data.gaps).toHaveProperty('missing_categories');
    expect(response.data.gaps).toHaveProperty('outdated_factors');
    expect(Array.isArray(response.data.gaps.missing_geographies)).toBe(true);
    expect(Array.isArray(response.data.gaps.missing_categories)).toBe(true);
    expect(Array.isArray(response.data.gaps.outdated_factors)).toBe(true);
  });

  it('percentages sum approximately to 100', async () => {
    const response = await axios.get(endpoint);

    const totalPercentage = response.data.by_source.reduce(
      (sum: number, source: { percentage_of_total: number }) =>
        sum + source.percentage_of_total,
      0
    );

    expect(totalPercentage).toBeGreaterThan(95);
    expect(totalPercentage).toBeLessThan(105);
  });

  it('coverage_percentage is between 0 and 100', async () => {
    const response = await axios.get(endpoint);

    expect(response.data.summary.coverage_percentage).toBeGreaterThanOrEqual(0);
    expect(response.data.summary.coverage_percentage).toBeLessThanOrEqual(100);
  });
});

// ============================================================================
// Mock Data Validation Tests
// ============================================================================

describe('Mock Data Quality', () => {
  it('products mock contains at least 100 items', async () => {
    const response = await axios.get(`${API_BASE_URL}/api/v1/products/search`);

    expect(response.data.total).toBeGreaterThanOrEqual(100);
  });

  it('categories mock contains at least 20 items', async () => {
    const response = await axios.get(`${API_BASE_URL}/api/v1/products/categories`);

    expect(response.data.total_categories).toBeGreaterThanOrEqual(20);
  });

  it('emission factors cover EPA, DEFRA, and EXIOBASE sources', async () => {
    const response = await axios.get(`${API_BASE_URL}/api/v1/emission-factors`);

    const sources = new Set(
      response.data.items.map((f: { data_source: string }) => f.data_source)
    );

    expect(sources.has('EPA_GHG_HUB')).toBe(true);
    expect(sources.has('DEFRA_CONVERSION')).toBe(true);
    expect(sources.has('EXIOBASE')).toBe(true);
  });

  it('products have realistic industry sectors', async () => {
    const response = await axios.get(`${API_BASE_URL}/api/v1/products/search`);

    const validSectors = [
      'electronics',
      'apparel',
      'automotive',
      'construction',
      'food_beverage',
      'chemicals',
      'machinery',
      'other',
    ];

    const productWithCategory = response.data.items.find(
      (p: { category?: { industry_sector: string } }) => p.category?.industry_sector
    );

    if (productWithCategory?.category?.industry_sector) {
      expect(validSectors).toContain(productWithCategory.category.industry_sector);
    }
  });

  it('data sources have realistic sync history', async () => {
    const response = await axios.get(`${API_BASE_URL}/admin/sync-logs`);

    expect(response.data.items.length).toBeGreaterThan(0);

    // Should have mix of completed and some failed syncs
    const statuses = response.data.items.map((log: { status: string }) => log.status);
    expect(statuses.some((s: string) => s === 'completed')).toBe(true);
  });
});
