/**
 * API Service Layer Tests
 * TASK-FE-006: Test API client, interceptors, and endpoint integrations
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { APIError } from '../../src/services/api/errors';
import type {
  ProductListResponse,
  ProductDetail,
  CalculationRequest,
  CalculationStartResponse,
  CalculationStatusResponse,
} from '../../src/types/api.types';

// Mock the client module with factory
vi.mock('../../src/services/api/client', () => {
  return {
    default: {
      get: vi.fn(),
      post: vi.fn(),
      interceptors: {
        request: { use: vi.fn() },
        response: { use: vi.fn() },
      },
    },
  };
});

// Import after mocking
import client from '../../src/services/api/client';
import api from '../../src/services/api';

describe('API Service Layer', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Products API - List', () => {
    it('should fetch products list successfully', async () => {
      const mockResponse: ProductListResponse = {
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
      };

      vi.mocked(client.get).mockResolvedValue({ data: mockResponse });

      const result = await api.products.list();

      expect(client.get).toHaveBeenCalledWith('/api/v1/products', {
        params: { limit: 100, offset: 0 },
      });
      expect(result).toEqual(mockResponse.items);
    });

    it('should fetch products with custom pagination', async () => {
      const mockResponse: ProductListResponse = {
        items: [],
        total: 50,
        limit: 20,
        offset: 10,
      };

      vi.mocked(client.get).mockResolvedValue({ data: mockResponse });

      await api.products.list({ limit: 20, offset: 10 });

      expect(client.get).toHaveBeenCalledWith('/api/v1/products', {
        params: { limit: 20, offset: 10 },
      });
    });

    it('should filter by is_finished_product', async () => {
      const mockResponse: ProductListResponse = {
        items: [],
        total: 0,
        limit: 100,
        offset: 0,
      };

      vi.mocked(client.get).mockResolvedValue({ data: mockResponse });

      await api.products.list({ is_finished_product: true });

      expect(client.get).toHaveBeenCalledWith('/api/v1/products', {
        params: { limit: 100, offset: 0, is_finished_product: true },
      });
    });
  });

  describe('Products API - Detail', () => {
    it('should fetch product detail with BOM', async () => {
      const mockProduct: ProductDetail = {
        id: 'prod-123',
        code: 'PROD-001',
        name: 'Test Product',
        description: 'A test product',
        unit: 'kg',
        category: 'Materials',
        is_finished_product: true,
        bill_of_materials: [
          {
            id: 'bom-1',
            child_product_id: 'prod-456',
            child_product_name: 'Component A',
            quantity: 2.5,
            unit: 'kg',
            notes: null,
          },
        ],
        created_at: '2024-11-08T10:00:00Z',
      };

      vi.mocked(client.get).mockResolvedValue({ data: mockProduct });

      const result = await api.products.getById('prod-123');

      expect(client.get).toHaveBeenCalledWith('/api/v1/products/prod-123');
      expect(result).toEqual(mockProduct);
    });
  });

  describe('Calculations API - Submit', () => {
    it('should submit calculation request successfully', async () => {
      const mockRequest: CalculationRequest = {
        product_id: 'prod-123',
        calculation_type: 'cradle_to_gate',
      };

      const mockResponse: CalculationStartResponse = {
        calculation_id: 'calc-abc123',
        status: 'pending',
      };

      vi.mocked(client.post).mockResolvedValue({ data: mockResponse });

      const result = await api.calculations.submit(mockRequest);

      expect(client.post).toHaveBeenCalledWith('/api/v1/calculate', mockRequest);
      expect(result).toEqual(mockResponse);
    });

    it('should use default calculation_type if not provided', async () => {
      const mockRequest: CalculationRequest = {
        product_id: 'prod-123',
      };

      const mockResponse: CalculationStartResponse = {
        calculation_id: 'calc-abc123',
        status: 'pending',
      };

      vi.mocked(client.post).mockResolvedValue({ data: mockResponse });

      await api.calculations.submit(mockRequest);

      expect(client.post).toHaveBeenCalledWith('/api/v1/calculate', {
        product_id: 'prod-123',
      });
    });
  });

  describe('Calculations API - Poll Status', () => {
    it('should fetch calculation status when pending', async () => {
      const mockStatus: CalculationStatusResponse = {
        calculation_id: 'calc-abc123',
        status: 'pending',
        product_id: 'prod-123',
        created_at: '2024-11-08T10:00:00Z',
      };

      vi.mocked(client.get).mockResolvedValue({ data: mockStatus });

      const result = await api.calculations.getStatus('calc-abc123');

      expect(client.get).toHaveBeenCalledWith('/api/v1/calculations/calc-abc123');
      expect(result).toEqual(mockStatus);
      expect(result.status).toBe('pending');
    });

    it('should fetch calculation status when completed', async () => {
      const mockStatus: CalculationStatusResponse = {
        calculation_id: 'calc-abc123',
        status: 'completed',
        product_id: 'prod-123',
        created_at: '2024-11-08T10:00:00Z',
        total_co2e_kg: 2.05,
        materials_co2e: 1.8,
        energy_co2e: 0.15,
        transport_co2e: 0.1,
        calculation_time_ms: 150,
      };

      vi.mocked(client.get).mockResolvedValue({ data: mockStatus });

      const result = await api.calculations.getStatus('calc-abc123');

      expect(result.status).toBe('completed');
      expect(result.total_co2e_kg).toBe(2.05);
      expect(result.materials_co2e).toBe(1.8);
    });

    it('should fetch calculation status when failed', async () => {
      const mockStatus: CalculationStatusResponse = {
        calculation_id: 'calc-abc123',
        status: 'failed',
        product_id: 'prod-123',
        created_at: '2024-11-08T10:00:00Z',
        error_message: 'Missing emission factor for component',
      };

      vi.mocked(client.get).mockResolvedValue({ data: mockStatus});

      const result = await api.calculations.getStatus('calc-abc123');

      expect(result.status).toBe('failed');
      expect(result.error_message).toBe('Missing emission factor for component');
    });
  });

  describe('APIError Class', () => {
    it('should create APIError with code and message', () => {
      const error = new APIError('SERVER_ERROR', 'Something went wrong');

      expect(error).toBeInstanceOf(Error);
      expect(error).toBeInstanceOf(APIError);
      expect(error.code).toBe('SERVER_ERROR');
      expect(error.message).toBe('Something went wrong');
      expect(error.name).toBe('APIError');
    });

    it('should store original error', () => {
      const originalError = new Error('Original error');
      const error = new APIError('NETWORK_ERROR', 'Network failed', originalError);

      expect(error.originalError).toBe(originalError);
    });

    it('should have proper error name for stack traces', () => {
      const error = new APIError('TIMEOUT', 'Request timed out');

      expect(error.name).toBe('APIError');
      expect(error.stack).toBeDefined();
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty products list', async () => {
      const mockResponse: ProductListResponse = {
        items: [],
        total: 0,
        limit: 100,
        offset: 0,
      };

      vi.mocked(client.get).mockResolvedValue({ data: mockResponse });

      const result = await api.products.list();

      expect(result).toEqual([]);
      expect(result).toHaveLength(0);
    });

    it('should handle product with empty BOM', async () => {
      const mockProduct: ProductDetail = {
        id: 'prod-123',
        code: 'PROD-001',
        name: 'Simple Product',
        description: null,
        unit: 'unit',
        category: null,
        is_finished_product: false,
        bill_of_materials: [],
        created_at: '2024-11-08T10:00:00Z',
      };

      vi.mocked(client.get).mockResolvedValue({ data: mockProduct });

      const result = await api.products.getById('prod-123');

      expect(result.bill_of_materials).toEqual([]);
    });

    it('should handle calculation with zero emissions', async () => {
      const mockStatus: CalculationStatusResponse = {
        calculation_id: 'calc-abc123',
        status: 'completed',
        product_id: 'prod-123',
        created_at: '2024-11-08T10:00:00Z',
        total_co2e_kg: 0,
        materials_co2e: 0,
        energy_co2e: 0,
        transport_co2e: 0,
        calculation_time_ms: 50,
      };

      vi.mocked(client.get).mockResolvedValue({ data: mockStatus });

      const result = await api.calculations.getStatus('calc-abc123');

      expect(result.total_co2e_kg).toBe(0);
    });
  });
});
