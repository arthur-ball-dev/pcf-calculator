/**
 * MSW Handlers - API Mock Responses
 * TASK-FE-011: Integration Testing Infrastructure
 * TASK-FE-P5-001: Phase 5 MSW Mock Server Setup
 *
 * Mock Service Worker handlers for all API endpoints.
 * Includes both MVP handlers and Phase 5 handlers.
 * Provides realistic responses for integration testing.
 */

import { delay, http, HttpResponse } from 'msw';
import type {
  ProductListResponse,
  ProductDetail,
  CalculationStartResponse,
  CalculationStatusResponse,
} from '../src/types/api.types';

// Import Phase 5 handlers
import { phase5Handlers } from '../src/mocks/handlers/phase5Handlers';

const API_BASE_URL = 'http://localhost:8000/api/v1';

/**
 * Mock product data
 */
export const mockProducts: ProductListResponse = {
  items: [
    {
      id: 'prod-001',
      code: 'TSHIRT-001',
      name: 'Cotton T-Shirt',
      category: 'Apparel',
      unit: 'unit',
      is_finished_product: true,
      created_at: '2024-01-01T00:00:00Z',
    },
    {
      id: 'prod-002',
      code: 'BOTTLE-001',
      name: 'Water Bottle (500ml)',
      category: 'Consumer Goods',
      unit: 'unit',
      is_finished_product: true,
      created_at: '2024-01-01T00:00:00Z',
    },
    {
      id: 'prod-003',
      code: 'LAPTOP-001',
      name: 'Laptop Computer',
      category: 'Electronics',
      unit: 'unit',
      is_finished_product: true,
      created_at: '2024-01-01T00:00:00Z',
    },
  ],
  total: 3,
  limit: 100,
  offset: 0,
};

/**
 * Mock product detail with BOM
 */
export const mockProductDetail: ProductDetail = {
  id: 'prod-001',
  code: 'TSHIRT-001',
  name: 'Cotton T-Shirt',
  description: 'Organic cotton t-shirt',
  category: 'Apparel',
  unit: 'unit',
  is_finished_product: true,
  created_at: '2024-01-01T00:00:00Z',
  bill_of_materials: [
    {
      id: 'comp-001',
      child_product_id: 'mat-001',
      child_product_name: 'Organic Cotton Fabric',
      quantity: 0.5,
      unit: 'kg',
      notes: null,
      emission_factor_id: 'ef-cotton-001',
    },
    {
      id: 'comp-002',
      child_product_id: 'mat-002',
      child_product_name: 'Polyester Thread',
      quantity: 0.05,
      unit: 'kg',
      notes: null,
      emission_factor_id: 'ef-polyester-001',
    },
    {
      id: 'comp-003',
      child_product_id: 'eng-001',
      child_product_name: 'Electricity (Manufacturing)',
      quantity: 2.5,
      unit: 'kWh',
      notes: null,
      emission_factor_id: 'ef-electricity-001',
    },
    {
      id: 'comp-004',
      child_product_id: 'trn-001',
      child_product_name: 'Transportation (Freight)',
      quantity: 50,
      unit: 'tkm',
      notes: null,
      emission_factor_id: 'ef-transport-001',
    },
  ],
};

/**
 * Mock calculation results
 */
export const mockCalculationResult: CalculationStatusResponse = {
  calculation_id: 'calc-123',
  product_id: 'prod-001',
  status: 'completed',
  created_at: '2024-01-01T00:00:00Z',
  total_co2e_kg: 12.456,
  materials_co2e: 7.5,
  energy_co2e: 2.8,
  transport_co2e: 1.5,
  calculation_time_ms: 150,
};

/**
 * Mock emission factors data
 */
export const mockEmissionFactors = {
  emission_factors: [
    {
      id: 'ef-cotton-001',
      activity_name: 'Organic Cotton Fabric',
      co2e_factor: 2.5,
      unit: 'kg',
      category: 'materials',
      data_source: 'EPA',
      geography: 'GLO',
      reference_year: 2020,
      data_quality_rating: 4,
      created_at: '2024-01-01T00:00:00Z',
    },
    {
      id: 'ef-polyester-001',
      activity_name: 'Polyester Thread',
      co2e_factor: 5.5,
      unit: 'kg',
      category: 'materials',
      data_source: 'EPA',
      geography: 'GLO',
      reference_year: 2020,
      data_quality_rating: 4,
      created_at: '2024-01-01T00:00:00Z',
    },
    {
      id: 'ef-electricity-001',
      activity_name: 'Electricity (Manufacturing)',
      co2e_factor: 0.45,
      unit: 'kWh',
      category: 'energy',
      data_source: 'EPA',
      geography: 'US',
      reference_year: 2022,
      data_quality_rating: 5,
      created_at: '2024-01-01T00:00:00Z',
    },
    {
      id: 'ef-transport-001',
      activity_name: 'Transportation (Freight)',
      co2e_factor: 0.062,
      unit: 'tkm',
      category: 'transport',
      data_source: 'DEFRA',
      geography: 'UK',
      reference_year: 2023,
      data_quality_rating: 4,
      created_at: '2024-01-01T00:00:00Z',
    },
  ],
  total: 4,
  page: 1,
  per_page: 50,
};

/**
 * MVP Handlers - Original handlers for existing functionality
 */
const mvpHandlers = [
  // GET /api/v1/products - List all products
  http.get(`${API_BASE_URL}/products`, ({ request }) => {
    const limit = new URL(request.url).searchParams.get('limit');
    const offset = new URL(request.url).searchParams.get('offset');
    const isFinished = new URL(request.url).searchParams.get('is_finished_product');

    let filteredProducts = mockProducts.items;

    if (isFinished === 'true') {
      filteredProducts = filteredProducts.filter(p => p.is_finished_product);
    }

    return HttpResponse.json({
      items: filteredProducts,
      total: filteredProducts.length,
      limit: parseInt(limit || '100'),
      offset: parseInt(offset || '0'),
    }, { status: 200 });
  }),

  // GET /api/v1/products/:id - Get product detail
  http.get(`${API_BASE_URL}/products/:id`, ({ params }) => {
    const { id } = params;

    if (id === 'prod-001') {
      return HttpResponse.json(mockProductDetail, { status: 200 });
    }

    return HttpResponse.json({
      error: {
        code: 'RESOURCE_NOT_FOUND',
        message: `Product with id '${id}' not found`,
      },
    }, { status: 404 });
  }),

  // POST /api/v1/calculate - Submit calculation
  http.post(`${API_BASE_URL}/calculate`, async ({ request }) => {
    const body = await request.json();

    if (!body.product_id) {
      return HttpResponse.json({
        error: {
          code: 'VALIDATION_ERROR',
          message: 'product_id is required',
        },
      }, { status: 400 });
    }

    const response: CalculationStartResponse = {
      calculation_id: 'calc-123',
      status: 'pending',
    };

    return HttpResponse.json(response, { status: 202 });
  }),

  // GET /api/v1/calculations/:id - Get calculation status
  http.get(`${API_BASE_URL}/calculations/:id`, ({ params }) => {
    const { id } = params;

    if (id === 'calc-123') {
      // Simulate polling - return completed on subsequent requests
      return HttpResponse.json(mockCalculationResult, { status: 200 });
    }

    return HttpResponse.json({
      error: {
        code: 'RESOURCE_NOT_FOUND',
        message: `Calculation with id '${id}' not found`,
      },
    }, { status: 404 });
  }),

  // GET /api/v1/attributions - Data source attributions
  // DataSourceAttributions requests this on every wizard render. Without a handler the
  // request reached the real localhost port, failed with "Network Error" some time
  // later, and its console.error could land after the test file had finished (Vitest:
  // "Closing rpc while onUserConsoleLog was pending").
  http.get(`${API_BASE_URL}/attributions`, () => {
    return HttpResponse.json({
      attributions: [
        {
          id: 'ds-epa',
          name: 'EPA GHG Emission Factors Hub',
          license_type: 'Public Domain',
          license_url: null,
          attribution_text: 'U.S. Environmental Protection Agency, GHG Emission Factors Hub (2024)',
          attribution_url: 'https://www.epa.gov/climateleadership/ghg-emission-factors-hub',
          allows_commercial_use: true,
          requires_attribution: false,
          requires_share_alike: false,
        },
        {
          id: 'ds-defra',
          name: 'DEFRA Conversion Factors',
          license_type: 'Open Government Licence v3.0',
          license_url: 'https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/',
          attribution_text: 'Contains public sector information licensed under the Open Government Licence v3.0',
          attribution_url: 'https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2024',
          allows_commercial_use: true,
          requires_attribution: true,
          requires_share_alike: false,
        },
      ],
      notice: 'Emission factors from EPA (public domain) and DEFRA (OGL v3.0).',
    }, { status: 200 });
  }),
];

/**
 * Combined handlers - Phase 5 + MVP
 * Phase 5 handlers come first as they are more specific and include
 * enhanced endpoints that should take precedence.
 */
export const handlers = [
  ...phase5Handlers,
  ...mvpHandlers,
];

/**
 * Error scenario handlers - use these to test error handling
 */
export const errorHandlers = {
  // Network error
  networkError: http.get(`${API_BASE_URL}/products`, () => {
    return HttpResponse.error();
  }),

  // 500 Server error
  serverError: http.get(`${API_BASE_URL}/products`, () => {
    return HttpResponse.json({
      error: {
        code: 'INTERNAL_SERVER_ERROR',
        message: 'An unexpected error occurred',
      },
    }, { status: 500 });
  }),

  // Timeout
  timeout: http.get(`${API_BASE_URL}/products`, async () => {
    await delay(35000); // 35 seconds > 30 second timeout
    return new HttpResponse(null, { status: 200 });
  }),

  // Calculation failed
  calculationFailed: http.get(`${API_BASE_URL}/calculations/:id`, () => {
    return HttpResponse.json({
      ...mockCalculationResult,
      status: 'failed',
      error_message: 'Calculation failed due to invalid emission factors',
    }, { status: 200 });
  }),
};
