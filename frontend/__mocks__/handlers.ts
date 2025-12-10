/**
 * MSW Handlers - API Mock Responses
 * TASK-FE-011: Integration Testing Infrastructure
 * TASK-FE-P5-001: Phase 5 MSW Mock Server Setup
 *
 * Mock Service Worker handlers for all API endpoints.
 * Includes both MVP handlers and Phase 5 handlers.
 * Provides realistic responses for integration testing.
 */

import { rest } from 'msw';
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
    },
    {
      id: 'comp-002',
      child_product_id: 'mat-002',
      child_product_name: 'Polyester Thread',
      quantity: 0.05,
      unit: 'kg',
      notes: null,
    },
    {
      id: 'comp-003',
      child_product_id: 'eng-001',
      child_product_name: 'Electricity (Manufacturing)',
      quantity: 2.5,
      unit: 'kWh',
      notes: null,
    },
    {
      id: 'comp-004',
      child_product_id: 'trn-001',
      child_product_name: 'Transportation (Freight)',
      quantity: 50,
      unit: 'tkm',
      notes: null,
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
      data_source: 'Ecoinvent',
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
      data_source: 'Ecoinvent',
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
  rest.get(`${API_BASE_URL}/products`, (req, res, ctx) => {
    const limit = req.url.searchParams.get('limit');
    const offset = req.url.searchParams.get('offset');
    const isFinished = req.url.searchParams.get('is_finished_product');

    let filteredProducts = mockProducts.items;

    if (isFinished === 'true') {
      filteredProducts = filteredProducts.filter(p => p.is_finished_product);
    }

    return res(
      ctx.status(200),
      ctx.json({
        items: filteredProducts,
        total: filteredProducts.length,
        limit: parseInt(limit || '100'),
        offset: parseInt(offset || '0'),
      })
    );
  }),

  // GET /api/v1/products/:id - Get product detail
  rest.get(`${API_BASE_URL}/products/:id`, (req, res, ctx) => {
    const { id } = req.params;

    if (id === 'prod-001') {
      return res(ctx.status(200), ctx.json(mockProductDetail));
    }

    return res(
      ctx.status(404),
      ctx.json({
        error: {
          code: 'RESOURCE_NOT_FOUND',
          message: `Product with id '${id}' not found`,
        },
      })
    );
  }),

  // POST /api/v1/calculate - Submit calculation
  rest.post(`${API_BASE_URL}/calculate`, async (req, res, ctx) => {
    const body = await req.json();

    if (!body.product_id) {
      return res(
        ctx.status(400),
        ctx.json({
          error: {
            code: 'VALIDATION_ERROR',
            message: 'product_id is required',
          },
        })
      );
    }

    const response: CalculationStartResponse = {
      calculation_id: 'calc-123',
      status: 'pending',
    };

    return res(ctx.status(202), ctx.json(response));
  }),

  // GET /api/v1/calculations/:id - Get calculation status
  rest.get(`${API_BASE_URL}/calculations/:id`, (req, res, ctx) => {
    const { id } = req.params;

    if (id === 'calc-123') {
      // Simulate polling - return completed on subsequent requests
      return res(ctx.status(200), ctx.json(mockCalculationResult));
    }

    return res(
      ctx.status(404),
      ctx.json({
        error: {
          code: 'RESOURCE_NOT_FOUND',
          message: `Calculation with id '${id}' not found`,
        },
      })
    );
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
  networkError: rest.get(`${API_BASE_URL}/products`, (req, res) => {
    return res.networkError('Failed to connect');
  }),

  // 500 Server error
  serverError: rest.get(`${API_BASE_URL}/products`, (req, res, ctx) => {
    return res(
      ctx.status(500),
      ctx.json({
        error: {
          code: 'INTERNAL_SERVER_ERROR',
          message: 'An unexpected error occurred',
        },
      })
    );
  }),

  // Timeout
  timeout: rest.get(`${API_BASE_URL}/products`, (req, res, ctx) => {
    return res(ctx.delay(35000)); // 35 seconds > 30 second timeout
  }),

  // Calculation failed
  calculationFailed: rest.get(`${API_BASE_URL}/calculations/:id`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        ...mockCalculationResult,
        status: 'failed',
        error_message: 'Calculation failed due to invalid emission factors',
      })
    );
  }),
};
