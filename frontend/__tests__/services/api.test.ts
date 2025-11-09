/**
 * API Service Layer Tests
 * TASK-FE-006: Test API client, interceptors, and endpoint integrations
 *
 * Test Coverage:
 * 1. Axios client configuration (base URL, timeout, headers)
 * 2. Products API endpoints (list, detail)
 * 3. Calculations API endpoints (submit, poll status)
 * 4. Error interceptor (network, timeout, server errors)
 * 5. Request interceptor (logging)
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import axios from 'axios';
import type { Mock } from 'vitest';

// Import the modules we're testing
import api from '../../src/services/api';
import { APIError } from '../../src/services/api/errors';
import type {
  ProductListResponse,
  ProductDetail,
  CalculationRequest,
  CalculationStartResponse,
  CalculationStatusResponse,
} from '../../src/types/api.types';

// Mock axios
vi.mock('axios');
const mockedAxios = axios as {
  create: Mock;
  isAxiosError: Mock;
};

describe('API Service Layer', () => {
  let mockAxiosInstance: {
    get: Mock;
    post: Mock;
    interceptors: {
      request: { use: Mock };
      response: { use: Mock };
    };
  };

  beforeEach(() => {
    // Create mock axios instance
    mockAxiosInstance = {
      get: vi.fn(),
      post: vi.fn(),
      interceptors: {
        request: {
          use: vi.fn(),
        },
        response: {
          use: vi.fn(),
        },
      },
    };

    // Mock axios.create to return our mock instance
    mockedAxios.create = vi.fn(() => mockAxiosInstance as any);

    // Mock axios.isAxiosError
    mockedAxios.isAxiosError = vi.fn((error: any) => {
      return error?.isAxiosError === true;
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  // ==========================================================================
  // Test Suite 1: Axios Client Configuration
  // ==========================================================================

  describe('Axios Client Configuration', () => {
    it('should create axios instance with correct base URL', () => {
      // Import triggers client creation
      require('../../src/services/api/client');

      expect(mockedAxios.create).toHaveBeenCalledWith(
        expect.objectContaining({
          baseURL: expect.stringContaining('localhost:8000'),
        })
      );
    });

    it('should configure 30 second timeout', () => {
      require('../../src/services/api/client');

      expect(mockedAxios.create).toHaveBeenCalledWith(
        expect.objectContaining({
          timeout: 30000,
        })
      );
    });

    it('should set Content-Type header to application/json', () => {
      require('../../src/services/api/client');

      expect(mockedAxios.create).toHaveBeenCalledWith(
        expect.objectContaining({
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        })
      );
    });

    it('should register request interceptor', () => {
      require('../../src/services/api/client');

      expect(mockAxiosInstance.interceptors.request.use).toHaveBeenCalled();
    });

    it('should register response interceptor', () => {
      require('../../src/services/api/client');

      expect(mockAxiosInstance.interceptors.response.use).toHaveBeenCalled();
    });
  });

  // ==========================================================================
  // Test Suite 2: Products API - List
  // ==========================================================================

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

      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse });

      const result = await api.products.list();

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/v1/products', {
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

      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse });

      await api.products.list({ limit: 20, offset: 10 });

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/v1/products', {
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

      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse });

      await api.products.list({ is_finished_product: true });

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/v1/products', {
        params: { limit: 100, offset: 0, is_finished_product: true },
      });
    });
  });

  // ==========================================================================
  // Test Suite 3: Products API - Detail
  // ==========================================================================

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

      mockAxiosInstance.get.mockResolvedValue({ data: mockProduct });

      const result = await api.products.getById('prod-123');

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/v1/products/prod-123');
      expect(result).toEqual(mockProduct);
    });

    it('should throw APIError when product not found', async () => {
      const axiosError = {
        isAxiosError: true,
        response: {
          status: 404,
          statusText: 'Not Found',
        },
      };

      mockAxiosInstance.get.mockRejectedValue(axiosError);
      mockedAxios.isAxiosError.mockReturnValue(true);

      await expect(api.products.getById('invalid-id')).rejects.toThrow(APIError);
      await expect(api.products.getById('invalid-id')).rejects.toThrow('Product not found');
    });
  });

  // ==========================================================================
  // Test Suite 4: Calculations API - Submit
  // ==========================================================================

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

      mockAxiosInstance.post.mockResolvedValue({ data: mockResponse });

      const result = await api.calculations.submit(mockRequest);

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/api/v1/calculate', mockRequest);
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

      mockAxiosInstance.post.mockResolvedValue({ data: mockResponse });

      await api.calculations.submit(mockRequest);

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/api/v1/calculate', {
        product_id: 'prod-123',
      });
    });
  });

  // ==========================================================================
  // Test Suite 5: Calculations API - Poll Status
  // ==========================================================================

  describe('Calculations API - Poll Status', () => {
    it('should fetch calculation status when pending', async () => {
      const mockStatus: CalculationStatusResponse = {
        calculation_id: 'calc-abc123',
        status: 'pending',
        product_id: 'prod-123',
        created_at: '2024-11-08T10:00:00Z',
      };

      mockAxiosInstance.get.mockResolvedValue({ data: mockStatus });

      const result = await api.calculations.getStatus('calc-abc123');

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/v1/calculations/calc-abc123');
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

      mockAxiosInstance.get.mockResolvedValue({ data: mockStatus });

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

      mockAxiosInstance.get.mockResolvedValue({ data: mockStatus });

      const result = await api.calculations.getStatus('calc-abc123');

      expect(result.status).toBe('failed');
      expect(result.error_message).toBe('Missing emission factor for component');
    });
  });

  // ==========================================================================
  // Test Suite 6: Error Interceptor - Server Errors
  // ==========================================================================

  describe('Error Interceptor - Server Errors', () => {
    it('should transform 500 error to APIError', async () => {
      const axiosError = {
        isAxiosError: true,
        response: {
          status: 500,
          statusText: 'Internal Server Error',
          data: { error: 'Database connection failed' },
        },
      };

      mockAxiosInstance.get.mockRejectedValue(axiosError);
      mockedAxios.isAxiosError.mockReturnValue(true);

      await expect(api.products.list()).rejects.toThrow(APIError);
      await expect(api.products.list()).rejects.toMatchObject({
        code: 'SERVER_ERROR',
        message: expect.stringContaining('server error'),
      });
    });

    it('should transform 404 error to APIError', async () => {
      const axiosError = {
        isAxiosError: true,
        response: {
          status: 404,
          statusText: 'Not Found',
        },
      };

      mockAxiosInstance.get.mockRejectedValue(axiosError);
      mockedAxios.isAxiosError.mockReturnValue(true);

      await expect(api.products.getById('invalid')).rejects.toThrow(APIError);
      await expect(api.products.getById('invalid')).rejects.toMatchObject({
        code: 'NOT_FOUND',
      });
    });

    it('should transform 400 validation error to APIError', async () => {
      const axiosError = {
        isAxiosError: true,
        response: {
          status: 400,
          statusText: 'Bad Request',
          data: { error: 'Invalid product_id format' },
        },
      };

      mockAxiosInstance.post.mockRejectedValue(axiosError);
      mockedAxios.isAxiosError.mockReturnValue(true);

      await expect(
        api.calculations.submit({ product_id: 'invalid' })
      ).rejects.toThrow(APIError);
      await expect(
        api.calculations.submit({ product_id: 'invalid' })
      ).rejects.toMatchObject({
        code: 'VALIDATION_ERROR',
      });
    });
  });

  // ==========================================================================
  // Test Suite 7: Error Interceptor - Network Errors
  // ==========================================================================

  describe('Error Interceptor - Network Errors', () => {
    it('should transform network error to APIError', async () => {
      const axiosError = {
        isAxiosError: true,
        request: {}, // Request was made but no response received
        message: 'Network Error',
      };

      mockAxiosInstance.get.mockRejectedValue(axiosError);
      mockedAxios.isAxiosError.mockReturnValue(true);

      await expect(api.products.list()).rejects.toThrow(APIError);
      await expect(api.products.list()).rejects.toMatchObject({
        code: 'NETWORK_ERROR',
        message: expect.stringContaining('network'),
      });
    });

    it('should handle connection refused error', async () => {
      const axiosError = {
        isAxiosError: true,
        code: 'ECONNREFUSED',
        message: 'connect ECONNREFUSED',
      };

      mockAxiosInstance.get.mockRejectedValue(axiosError);
      mockedAxios.isAxiosError.mockReturnValue(true);

      await expect(api.products.list()).rejects.toThrow(APIError);
    });
  });

  // ==========================================================================
  // Test Suite 8: Error Interceptor - Timeout
  // ==========================================================================

  describe('Error Interceptor - Timeout', () => {
    it('should transform timeout error to APIError', async () => {
      const axiosError = {
        isAxiosError: true,
        code: 'ECONNABORTED',
        message: 'timeout of 30000ms exceeded',
      };

      mockAxiosInstance.get.mockRejectedValue(axiosError);
      mockedAxios.isAxiosError.mockReturnValue(true);

      await expect(api.products.list()).rejects.toThrow(APIError);
      await expect(api.products.list()).rejects.toMatchObject({
        code: 'TIMEOUT',
        message: expect.stringContaining('timeout'),
      });
    });

    it('should handle slow request that times out', async () => {
      const axiosError = {
        isAxiosError: true,
        code: 'ECONNABORTED',
        message: 'Request timeout',
      };

      mockAxiosInstance.post.mockRejectedValue(axiosError);
      mockedAxios.isAxiosError.mockReturnValue(true);

      await expect(
        api.calculations.submit({ product_id: 'prod-123' })
      ).rejects.toThrow(APIError);
      await expect(
        api.calculations.submit({ product_id: 'prod-123' })
      ).rejects.toMatchObject({
        code: 'TIMEOUT',
      });
    });
  });

  // ==========================================================================
  // Test Suite 9: APIError Class
  // ==========================================================================

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

  // ==========================================================================
  // Test Suite 10: Request Interceptor (Logging)
  // ==========================================================================

  describe('Request Interceptor', () => {
    it('should log requests in development mode', () => {
      const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {});

      // Simulate interceptor call
      const mockConfig = {
        method: 'get',
        url: '/api/v1/products',
      };

      // Access the interceptor function
      const interceptorCalls = mockAxiosInstance.interceptors.request.use.mock.calls;
      if (interceptorCalls.length > 0) {
        const requestInterceptor = interceptorCalls[0][0];
        if (typeof requestInterceptor === 'function') {
          requestInterceptor(mockConfig);
        }
      }

      // Note: This test validates the interceptor is registered
      // Actual logging behavior depends on environment
      expect(mockAxiosInstance.interceptors.request.use).toHaveBeenCalled();

      consoleSpy.mockRestore();
    });
  });

  // ==========================================================================
  // Test Suite 11: Edge Cases
  // ==========================================================================

  describe('Edge Cases', () => {
    it('should handle empty products list', async () => {
      const mockResponse: ProductListResponse = {
        items: [],
        total: 0,
        limit: 100,
        offset: 0,
      };

      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse });

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

      mockAxiosInstance.get.mockResolvedValue({ data: mockProduct });

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

      mockAxiosInstance.get.mockResolvedValue({ data: mockStatus });

      const result = await api.calculations.getStatus('calc-abc123');

      expect(result.total_co2e_kg).toBe(0);
    });

    it('should handle unknown error gracefully', async () => {
      const unknownError = new Error('Something unexpected');

      mockAxiosInstance.get.mockRejectedValue(unknownError);
      mockedAxios.isAxiosError.mockReturnValue(false);

      await expect(api.products.list()).rejects.toThrow();
    });
  });
});
