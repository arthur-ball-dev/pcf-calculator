/**
 * MSW Handlers - API Mock Responses
 * TASK-FE-011: Integration Testing Infrastructure
 *
 * Mock Service Worker handlers for all API endpoints.
 * Provides realistic responses for integration testing.
 */

import { rest } from 'msw';
import type {
  ProductListResponse,
  ProductDetail,
  CalculationStartResponse,
  CalculationStatusResponse,
} from '../src/types/api.types';

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
    },
    {
      id: 'prod-002',
      code: 'BOTTLE-001',
      name: 'Water Bottle (500ml)',
      category: 'Consumer Goods',
      unit: 'unit',
      is_finished_product: true,
    },
    {
      id: 'prod-003',
      code: 'LAPTOP-001',
      name: 'Laptop Computer',
      category: 'Electronics',
      unit: 'unit',
      is_finished_product: true,
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
  category: 'Apparel',
  unit: 'unit',
  is_finished_product: true,
  bom: [
    {
      component_id: 'comp-001',
      component_name: 'Organic Cotton Fabric',
      quantity: 0.5,
      unit: 'kg',
      category: 'material',
      emission_factor_id: 'ef-cotton-001',
    },
    {
      component_id: 'comp-002',
      component_name: 'Polyester Thread',
      quantity: 0.05,
      unit: 'kg',
      category: 'material',
      emission_factor_id: 'ef-polyester-001',
    },
    {
      component_id: 'comp-003',
      component_name: 'Electricity (Manufacturing)',
      quantity: 2.5,
      unit: 'kWh',
      category: 'energy',
      emission_factor_id: 'ef-electricity-001',
    },
    {
      component_id: 'comp-004',
      component_name: 'Transportation (Freight)',
      quantity: 50,
      unit: 'tkm',
      category: 'transport',
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
  product_name: 'Cotton T-Shirt',
  status: 'completed',
  calculation_type: 'cradle_to_gate',
  total_emissions: 12.456,
  created_at: new Date().toISOString(),
  completed_at: new Date().toISOString(),
  breakdown: {
    materials_emissions: 7.5,
    energy_emissions: 2.8,
    transport_emissions: 1.5,
    waste_emissions: 0.656,
  },
  components: [
    {
      component_id: 'comp-001',
      component_name: 'Organic Cotton Fabric',
      quantity: 0.5,
      unit: 'kg',
      category: 'material',
      emission_factor_id: 'ef-cotton-001',
      co2e_value: 7.5,
    },
    {
      component_id: 'comp-002',
      component_name: 'Polyester Thread',
      quantity: 0.05,
      unit: 'kg',
      category: 'material',
      emission_factor_id: 'ef-polyester-001',
      co2e_value: 0.5,
    },
    {
      component_id: 'comp-003',
      component_name: 'Electricity (Manufacturing)',
      quantity: 2.5,
      unit: 'kWh',
      category: 'energy',
      emission_factor_id: 'ef-electricity-001',
      co2e_value: 2.8,
    },
    {
      component_id: 'comp-004',
      component_name: 'Transportation (Freight)',
      quantity: 50,
      unit: 'tkm',
      category: 'transport',
      emission_factor_id: 'ef-transport-001',
      co2e_value: 1.5,
    },
  ],
  sankey_data: {
    nodes: [
      { id: 'Product', name: 'Cotton T-Shirt' },
      { id: 'Materials', name: 'Materials' },
      { id: 'Energy', name: 'Energy' },
      { id: 'Transport', name: 'Transport' },
      { id: 'Waste', name: 'Waste' },
      { id: 'Total', name: 'Total CO₂e' },
    ],
    links: [
      { source: 'Product', target: 'Materials', value: 7.5 },
      { source: 'Product', target: 'Energy', value: 2.8 },
      { source: 'Product', target: 'Transport', value: 1.5 },
      { source: 'Product', target: 'Waste', value: 0.656 },
      { source: 'Materials', target: 'Total', value: 7.5 },
      { source: 'Energy', target: 'Total', value: 2.8 },
      { source: 'Transport', target: 'Total', value: 1.5 },
      { source: 'Waste', target: 'Total', value: 0.656 },
    ],
  },
};

/**
 * MSW Request Handlers
 */
export const handlers = [
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
      message: 'Calculation submitted successfully',
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
