/**
 * Phase 5 MSW Handlers
 * TASK-FE-P5-001: MSW Mock Server Setup
 *
 * Mock Service Worker handlers for all Phase 5 API endpoints.
 * Responses match API contracts exactly.
 */

import { rest } from 'msw';
import {
  mockProducts,
  filterProducts,
  mockCategories,
  countCategories,
  getMaxDepth,
  filterByIndustry,
  limitDepth,
  mockEmissionFactors,
  filterEmissionFactors,
  generateAggregations,
  mockDataSources,
  filterDataSources,
  generateDataSourceSummary,
  mockSyncLogs,
  filterSyncLogs,
  generateSyncLogsSummary,
} from '../data';

const API_BASE_URL = 'http://localhost:8000';

// Generate UUID
function generateUUID(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

export const phase5Handlers = [
  // ============================================================================
  // Product Search Endpoint
  // GET /api/v1/products/search
  // ============================================================================
  rest.get(`${API_BASE_URL}/api/v1/products/search`, (req, res, ctx) => {
    const url = new URL(req.url);
    const query = url.searchParams.get('query') || undefined;
    const categoryId = url.searchParams.get('category_id') || undefined;
    const industry = url.searchParams.get('industry') || undefined;
    const manufacturer = url.searchParams.get('manufacturer') || undefined;
    const countryOfOrigin = url.searchParams.get('country_of_origin') || undefined;
    const isFinishedProductParam = url.searchParams.get('is_finished_product');
    const limit = parseInt(url.searchParams.get('limit') || '50', 10);
    const offset = parseInt(url.searchParams.get('offset') || '0', 10);

    const isFinishedProduct =
      isFinishedProductParam === 'true'
        ? true
        : isFinishedProductParam === 'false'
        ? false
        : undefined;

    const filtered = filterProducts(mockProducts, {
      query,
      category_id: categoryId,
      industry,
      manufacturer,
      country_of_origin: countryOfOrigin,
      is_finished_product: isFinishedProduct,
    });

    const total = filtered.length;
    const items = filtered.slice(offset, offset + limit);
    const hasMore = offset + limit < total;

    return res(
      ctx.status(200),
      ctx.json({
        items,
        total,
        limit,
        offset,
        has_more: hasMore,
      })
    );
  }),

  // ============================================================================
  // Product Categories Endpoint
  // GET /api/v1/products/categories
  // ============================================================================
  rest.get(`${API_BASE_URL}/api/v1/products/categories`, (req, res, ctx) => {
    const url = new URL(req.url);
    const parentId = url.searchParams.get('parent_id') || undefined;
    const depth = parseInt(url.searchParams.get('depth') || '3', 10);
    const includeProductCount = url.searchParams.get('include_product_count') === 'true';
    const industry = url.searchParams.get('industry') || undefined;

    let categories = [...mockCategories];

    // Filter by parent_id if provided
    if (parentId) {
      // Find children of the specified parent
      const findChildren = (cats: typeof categories, id: string): typeof categories | null => {
        for (const cat of cats) {
          if (cat.id === id) {
            return cat.children;
          }
          const found = findChildren(cat.children, id);
          if (found) return found;
        }
        return null;
      };
      const children = findChildren(categories, parentId);
      if (children) {
        categories = children;
      } else {
        return res(
          ctx.status(404),
          ctx.json({
            error: {
              code: 'NOT_FOUND',
              message: 'Category not found',
              details: [
                {
                  field: 'parent_id',
                  message: `No category exists with ID ${parentId}`,
                },
              ],
            },
            request_id: `req_${generateUUID().slice(0, 8)}`,
            timestamp: new Date().toISOString(),
          })
        );
      }
    }

    // Filter by industry
    if (industry) {
      categories = filterByIndustry(categories, industry);
    }

    // Limit depth
    categories = limitDepth(categories, depth);

    // Remove product_count if not requested
    const processCategories = (cats: typeof categories): typeof categories => {
      return cats.map((cat) => {
        const processed = { ...cat };
        if (!includeProductCount) {
          delete (processed as { product_count?: number }).product_count;
        }
        processed.children = processCategories(cat.children);
        return processed;
      });
    };
    categories = processCategories(categories);

    const totalCategories = countCategories(categories);
    const maxDepth = getMaxDepth(categories);

    return res(
      ctx.status(200),
      ctx.json({
        categories,
        total_categories: totalCategories,
        max_depth: Math.min(maxDepth, depth),
      })
    );
  }),

  // ============================================================================
  // Emission Factors Endpoint (Enhanced Phase 5)
  // GET /api/v1/emission-factors
  // ============================================================================
  rest.get(`${API_BASE_URL}/api/v1/emission-factors`, (req, res, ctx) => {
    const url = new URL(req.url);
    const query = url.searchParams.get('query') || undefined;
    const dataSource = url.searchParams.get('data_source') || undefined;
    const dataSourceId = url.searchParams.get('data_source_id') || undefined;
    const geography = url.searchParams.get('geography') || undefined;
    const unit = url.searchParams.get('unit') || undefined;
    const referenceYearParam = url.searchParams.get('reference_year');
    const minQualityParam = url.searchParams.get('min_quality');
    const isActiveParam = url.searchParams.get('is_active');
    const limit = parseInt(url.searchParams.get('limit') || '50', 10);
    const offset = parseInt(url.searchParams.get('offset') || '0', 10);
    const sortBy = url.searchParams.get('sort_by') || undefined;
    const sortOrder = (url.searchParams.get('sort_order') as 'asc' | 'desc') || 'asc';

    const referenceYear = referenceYearParam ? parseInt(referenceYearParam, 10) : undefined;
    const minQuality = minQualityParam ? parseFloat(minQualityParam) : undefined;
    const isActive =
      isActiveParam === 'true' ? true : isActiveParam === 'false' ? false : undefined;

    const filtered = filterEmissionFactors(mockEmissionFactors, {
      query,
      data_source: dataSource,
      data_source_id: dataSourceId,
      geography,
      unit,
      reference_year: referenceYear,
      min_quality: minQuality,
      is_active: isActive,
      sort_by: sortBy,
      sort_order: sortOrder,
    });

    const total = filtered.length;
    const items = filtered.slice(offset, offset + limit);
    const hasMore = offset + limit < total;

    // Include aggregations only when query is provided
    const aggregations = query ? generateAggregations(filtered) : undefined;

    return res(
      ctx.status(200),
      ctx.json({
        items,
        total,
        limit,
        offset,
        has_more: hasMore,
        aggregations,
      })
    );
  }),

  // ============================================================================
  // Admin Data Sources Endpoint
  // GET /admin/data-sources
  // ============================================================================
  rest.get(`${API_BASE_URL}/admin/data-sources`, (req, res, ctx) => {
    const url = new URL(req.url);
    const isActiveParam = url.searchParams.get('is_active');
    const sourceType = url.searchParams.get('source_type') || undefined;

    const isActive =
      isActiveParam === 'true' ? true : isActiveParam === 'false' ? false : undefined;

    const filtered = filterDataSources(mockDataSources, {
      is_active: isActive,
      source_type: sourceType,
    });

    const summary = generateDataSourceSummary(filtered);

    return res(
      ctx.status(200),
      ctx.json({
        data_sources: filtered,
        total: filtered.length,
        summary,
      })
    );
  }),

  // ============================================================================
  // Admin Sync Trigger Endpoint
  // POST /admin/data-sources/:id/sync
  // ============================================================================
  rest.post(`${API_BASE_URL}/admin/data-sources/:id/sync`, async (req, res, ctx) => {
    const { id } = req.params;
    const body = await req.json().catch(() => ({}));

    // Find the data source
    const dataSource = mockDataSources.find((s) => s.id === id);

    if (!dataSource) {
      return res(
        ctx.status(404),
        ctx.json({
          error: {
            code: 'NOT_FOUND',
            message: 'Data source not found',
            details: [
              {
                field: 'id',
                message: `No data source exists with ID ${id}`,
              },
            ],
          },
          request_id: `req_${generateUUID().slice(0, 8)}`,
          timestamp: new Date().toISOString(),
        })
      );
    }

    const taskId = `celery-task-${generateUUID()}`;
    const syncLogId = generateUUID();
    const isDryRun = body.dry_run === true;

    return res(
      ctx.status(202),
      ctx.json({
        task_id: taskId,
        sync_log_id: syncLogId,
        status: 'queued',
        message: isDryRun
          ? `Dry run sync task queued for ${dataSource.name}`
          : `Sync task queued successfully`,
        data_source: {
          id: dataSource.id,
          name: dataSource.name,
        },
        estimated_duration: '5 minutes',
        poll_url: `/admin/sync-logs/${syncLogId}`,
      })
    );
  }),

  // ============================================================================
  // Admin Sync Logs Endpoint
  // GET /admin/sync-logs
  // ============================================================================
  rest.get(`${API_BASE_URL}/admin/sync-logs`, (req, res, ctx) => {
    const url = new URL(req.url);
    const dataSourceId = url.searchParams.get('data_source_id') || undefined;
    const status = url.searchParams.get('status') || undefined;
    const syncType = url.searchParams.get('sync_type') || undefined;
    const startDate = url.searchParams.get('start_date') || undefined;
    const endDate = url.searchParams.get('end_date') || undefined;
    const hasErrorsParam = url.searchParams.get('has_errors');
    const limit = parseInt(url.searchParams.get('limit') || '50', 10);
    const offset = parseInt(url.searchParams.get('offset') || '0', 10);
    const sortBy = url.searchParams.get('sort_by') || 'started_at';
    const sortOrder = (url.searchParams.get('sort_order') as 'asc' | 'desc') || 'desc';

    const hasErrors = hasErrorsParam === 'true';

    const filtered = filterSyncLogs(mockSyncLogs, {
      data_source_id: dataSourceId,
      status,
      sync_type: syncType,
      start_date: startDate,
      end_date: endDate,
      has_errors: hasErrors ? true : undefined,
      sort_by: sortBy,
      sort_order: sortOrder,
    });

    const total = filtered.length;
    const items = filtered.slice(offset, offset + limit);
    const hasMore = offset + limit < total;

    const summary = generateSyncLogsSummary(filtered);

    return res(
      ctx.status(200),
      ctx.json({
        items,
        total,
        limit,
        offset,
        has_more: hasMore,
        summary,
      })
    );
  }),

  // ============================================================================
  // Admin Coverage Stats Endpoint
  // GET /admin/emission-factors/coverage
  // ============================================================================
  rest.get(`${API_BASE_URL}/admin/emission-factors/coverage`, (req, res, ctx) => {
    const activeSources = mockDataSources.filter((s) => s.is_active);

    // Calculate summary from actual mock data
    const totalFactors = mockEmissionFactors.length;
    const activeFactors = mockEmissionFactors.filter((f) => f.is_active).length;
    const uniqueActivities = new Set(mockEmissionFactors.map((f) => f.activity_name)).size;
    const geographiesCovered = new Set(mockEmissionFactors.map((f) => f.geography)).size;

    // Categories coverage (simulated)
    const categoriesWithFactors = 180;
    const categoriesWithoutFactors = 45;
    const coveragePercentage = 78.5;

    const avgQuality =
      mockEmissionFactors
        .filter((f) => f.data_quality_rating !== null)
        .reduce((sum, f) => sum + (f.data_quality_rating || 0), 0) /
      mockEmissionFactors.filter((f) => f.data_quality_rating !== null).length;

    // By source breakdown - calculate actual counts from mock data
    const sourceFactorCounts = new Map<string, number>();
    for (const factor of mockEmissionFactors) {
      const count = sourceFactorCounts.get(factor.data_source_id || '') || 0;
      sourceFactorCounts.set(factor.data_source_id || '', count + 1);
    }

    const bySource = activeSources.map((source) => {
      const sourceFactors = mockEmissionFactors.filter(
        (f) => f.data_source_id === source.id
      );
      const actualFactorCount = sourceFactors.length;
      const geographies = [...new Set(sourceFactors.map((f) => f.geography))];
      const years = sourceFactors
        .map((f) => f.reference_year)
        .filter((y): y is number => y !== null);

      // Calculate actual quality rating from mock data
      const qualityRatings = sourceFactors
        .map((f) => f.data_quality_rating)
        .filter((q): q is number => q !== null);
      const avgSourceQuality = qualityRatings.length > 0
        ? qualityRatings.reduce((sum, q) => sum + q, 0) / qualityRatings.length
        : null;

      return {
        source_id: source.id,
        source_name: source.name,
        total_factors: actualFactorCount,
        active_factors: sourceFactors.filter((f) => f.is_active).length,
        percentage_of_total:
          totalFactors > 0
            ? Math.round((actualFactorCount / totalFactors) * 1000) / 10
            : 0,
        geographies,
        average_quality: avgSourceQuality !== null
          ? Math.round(avgSourceQuality * 100) / 100
          : null,
        year_range: {
          min: years.length > 0 ? Math.min(...years) : null,
          max: years.length > 0 ? Math.max(...years) : null,
        },
      };
    });

    // By geography breakdown
    const geographyMap = new Map<string, { count: number; sources: Set<string> }>();
    for (const factor of mockEmissionFactors) {
      const existing = geographyMap.get(factor.geography) || {
        count: 0,
        sources: new Set<string>(),
      };
      existing.count++;
      existing.sources.add(factor.data_source);
      geographyMap.set(factor.geography, existing);
    }

    const geographyNames: Record<string, string> = {
      US: 'United States',
      GB: 'United Kingdom',
      DE: 'Germany',
      CN: 'China',
      JP: 'Japan',
      GLO: 'Global',
      FR: 'France',
      IT: 'Italy',
      KR: 'South Korea',
    };

    const byGeography = Array.from(geographyMap.entries())
      .map(([geo, data]) => ({
        geography: geo,
        geography_name: geographyNames[geo] || geo,
        total_factors: data.count,
        sources: Array.from(data.sources),
        percentage_of_total: Math.round((data.count / totalFactors) * 1000) / 10,
      }))
      .sort((a, b) => b.total_factors - a.total_factors);

    // By category breakdown (simulated)
    const byCategory = [
      {
        category_id: '770e8400-e29b-41d4-a716-446655440001',
        category_name: 'Electronics',
        category_code: 'ELEC',
        products_count: 450,
        products_with_factors: 420,
        coverage_percentage: 93.3,
        factors_available: 125,
        gap_status: 'full' as const,
      },
      {
        category_id: '770e8400-e29b-41d4-a716-446655440002',
        category_name: 'Apparel',
        category_code: 'APRL',
        products_count: 320,
        products_with_factors: 250,
        coverage_percentage: 78.1,
        factors_available: 85,
        gap_status: 'partial' as const,
      },
      {
        category_id: '770e8400-e29b-41d4-a716-446655440003',
        category_name: 'Specialty Chemicals',
        category_code: 'CHEM-SPEC',
        products_count: 45,
        products_with_factors: 0,
        coverage_percentage: 0.0,
        factors_available: 0,
        gap_status: 'none' as const,
      },
      {
        category_id: '770e8400-e29b-41d4-a716-446655440004',
        category_name: 'Automotive',
        category_code: 'AUTO',
        products_count: 280,
        products_with_factors: 240,
        coverage_percentage: 85.7,
        factors_available: 95,
        gap_status: 'partial' as const,
      },
    ];

    // Gaps
    const gaps = {
      missing_geographies: [
        { geography: 'IN', products_affected: 35 },
        { geography: 'BR', products_affected: 22 },
        { geography: 'MX', products_affected: 18 },
      ],
      missing_categories: [
        {
          category_id: '770e8400-e29b-41d4-a716-446655440003',
          category_name: 'Specialty Chemicals',
          products_count: 45,
        },
        {
          category_id: '770e8400-e29b-41d4-a716-446655440005',
          category_name: 'Rare Earth Components',
          products_count: 12,
        },
      ],
      outdated_factors: [
        {
          source_name: 'Exiobase',
          count: 850,
          oldest_year: 2019,
        },
      ],
    };

    return res(
      ctx.status(200),
      ctx.json({
        summary: {
          total_emission_factors: totalFactors,
          active_emission_factors: activeFactors,
          unique_activities: uniqueActivities,
          geographies_covered: geographiesCovered,
          categories_with_factors: categoriesWithFactors,
          categories_without_factors: categoriesWithoutFactors,
          average_quality_rating: Math.round(avgQuality * 100) / 100,
          coverage_percentage: coveragePercentage,
        },
        by_source: bySource,
        by_geography: byGeography,
        by_category: byCategory,
        gaps,
      })
    );
  }),
];
