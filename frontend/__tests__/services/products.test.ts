/**
 * Products API Service Tests
 * TASK-FE-011: Test fetchProducts export for ProductSelector component
 *
 * Test Coverage:
 * 1. fetchProducts export exists and is a function
 * 2. fetchProducts behaves identically to productsAPI.list
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';

// Import the module we're testing
import { productsAPI, fetchProducts } from '../../src/services/api/products';

// Mock the client module
vi.mock('../../src/services/api/client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

// Import mocked client
import client from '../../src/services/api/client';

describe('Products API - fetchProducts Export', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should export fetchProducts function', () => {
    // Verify fetchProducts is exported
    expect(fetchProducts).toBeDefined();
    expect(typeof fetchProducts).toBe('function');
  });

  it('should have fetchProducts be the same reference as productsAPI.list', () => {
    // Verify fetchProducts is exactly the same function as productsAPI.list
    expect(fetchProducts).toBe(productsAPI.list);
  });

  it('should have fetchProducts that behaves like productsAPI.list', async () => {
    // Mock response
    const mockResponse = {
      data: {
        items: [
          {
            id: 'prod-123',
            code: 'PROD-001',
            name: 'Test Product',
            unit: 'kg',
            category: 'Materials',
            is_finished_product: true,
            created_at: '2024-11-08T10:00:00Z',
          },
        ],
        total: 1,
        limit: 100,
        offset: 0,
      },
    };

    vi.mocked(client.get).mockResolvedValue(mockResponse);

    // Call fetchProducts
    const result = await fetchProducts({
      is_finished_product: true,
    });

    // Verify it makes the correct API call
    expect(client.get).toHaveBeenCalledWith('/api/v1/products', {
      params: { limit: 100, offset: 0, is_finished_product: true },
    });

    // Verify it returns the items array
    expect(result).toEqual(mockResponse.data.items);
  });

  it('should support same parameters as productsAPI.list', async () => {
    const mockResponse = {
      data: {
        items: [],
        total: 0,
        limit: 50,
        offset: 10,
      },
    };

    vi.mocked(client.get).mockResolvedValue(mockResponse);

    // Call with custom pagination
    await fetchProducts({
      limit: 50,
      offset: 10,
      is_finished_product: true,
    });

    // Verify parameters are passed through
    expect(client.get).toHaveBeenCalledWith('/api/v1/products', {
      params: { limit: 50, offset: 10, is_finished_product: true },
    });
  });

  it('should work when called without parameters', async () => {
    const mockResponse = {
      data: {
        items: [
          {
            id: 'prod-456',
            code: 'PROD-002',
            name: 'Another Product',
            unit: 'unit',
            category: null,
            is_finished_product: false,
            created_at: '2024-11-08T11:00:00Z',
          },
        ],
        total: 1,
        limit: 100,
        offset: 0,
      },
    };

    vi.mocked(client.get).mockResolvedValue(mockResponse);

    // Call without parameters
    const result = await fetchProducts();

    // Verify default parameters are used
    expect(client.get).toHaveBeenCalledWith('/api/v1/products', {
      params: { limit: 100, offset: 0 },
    });

    expect(result).toEqual(mockResponse.data.items);
  });
});
