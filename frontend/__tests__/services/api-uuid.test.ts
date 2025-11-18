/**
 * API UUID Payload Validation Tests (TASK-FE-020 - Test-First)
 *
 * Tests that API calls send full UUID strings (not truncated) to backend.
 * These tests validate API integration with UUID type system.
 *
 * CRITICAL: These tests are written BEFORE implementation (TDD Phase 1).
 * They will fail initially, proving they are valid tests.
 */

import { describe, test, expect, beforeEach, vi } from 'vitest';
import { calculationsAPI } from '../../src/services/api/calculations';
import { productsAPI } from '../../src/services/api/products';

// Mock the client module
vi.mock('../../src/services/api/client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

// Import mocked client
import client from '../../src/services/api/client';

describe('API UUID Payload Validation', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Calculation API - Submit Calculation', () => {
    test('should send full UUID product_id in POST payload (not truncated)', async () => {
      const productId = '471fe408a2604386bae572d9fc9a6b5c';
      const calculationId = 'calc-uuid-response-123';

      const mockResponse = {
        data: {
          calculation_id: calculationId,
        },
      };

      vi.mocked(client.post).mockResolvedValue(mockResponse);

      await calculationsAPI.submit({ product_id: productId });

      // Verify POST was called with correct endpoint and payload
      expect(client.post).toHaveBeenCalledWith('/api/v1/calculate', {
        product_id: productId,
      });

      // Verify full UUID sent (not truncated)
      const call = vi.mocked(client.post).mock.calls[0];
      expect(call[1].product_id).toBe(productId);
      expect(call[1].product_id.length).toBe(32);
      expect(call[1].product_id).not.toBe('471'); // NOT truncated
      expect(typeof call[1].product_id).toBe('string');
    });

    test('should handle UUIDs starting with numeric characters', async () => {
      const productId = '123abc456def789012345678abcdef12';

      const mockResponse = {
        data: {
          calculation_id: 'calc-123',
        },
      };

      vi.mocked(client.post).mockResolvedValue(mockResponse);

      await calculationsAPI.submit({ product_id: productId });

      const call = vi.mocked(client.post).mock.calls[0];
      expect(call[1].product_id).toBe(productId);
      expect(call[1].product_id).not.toBe('123');
      expect(typeof call[1].product_id).toBe('string');
    });

    test('should preserve different UUID formats', async () => {
      const testUUIDs = [
        'a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6',
        '00000000000000000000000000000001',
        'ffffffffffffffffffffffffffffffff',
      ];

      const mockResponse = {
        data: {
          calculation_id: 'calc-test',
        },
      };

      for (const uuid of testUUIDs) {
        vi.mocked(client.post).mockResolvedValue(mockResponse);

        await calculationsAPI.submit({ product_id: uuid });

        const call = vi.mocked(client.post).mock.calls[
          vi.mocked(client.post).mock.calls.length - 1
        ];
        expect(call[1].product_id).toBe(uuid);
        expect(call[1].product_id.length).toBe(32);
        expect(typeof call[1].product_id).toBe('string');
      }
    });
  });

  describe('Calculation API - Get Calculation Status', () => {
    test('should use full UUID in GET request URL', async () => {
      const calculationId = 'calc-uuid-get-test-123';

      const mockResponse = {
        data: {
          id: calculationId,
          status: 'in_progress',
          product_id: '471fe408a2604386bae572d9fc9a6b5c',
        },
      };

      vi.mocked(client.get).mockResolvedValue(mockResponse);

      await calculationsAPI.getStatus(calculationId);

      // Verify GET was called with full UUID in path
      expect(client.get).toHaveBeenCalledWith(`/api/v1/calculations/${calculationId}`);

      const call = vi.mocked(client.get).mock.calls[0];
      expect(call[0]).toContain(calculationId);
      expect(call[0]).not.toContain('NaN');
      expect(call[0]).not.toContain('undefined');
    });

    test('should handle 32-char hex UUIDs in URL', async () => {
      const calculationId = 'a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6';

      const mockResponse = {
        data: {
          id: calculationId,
          status: 'completed',
          total_co2e_kg: 100.5,
        },
      };

      vi.mocked(client.get).mockResolvedValue(mockResponse);

      await calculationsAPI.getStatus(calculationId);

      const call = vi.mocked(client.get).mock.calls[0];
      expect(call[0]).toBe(`/api/v1/calculations/${calculationId}`);
      expect(call[0].split('/').pop()).toBe(calculationId);
    });
  });

  describe('Products API - Get Product by ID', () => {
    test('should use full UUID in GET request URL', async () => {
      const productId = '471fe408a2604386bae572d9fc9a6b5c';

      const mockResponse = {
        data: {
          id: productId,
          code: 'PROD-001',
          name: 'Test Product',
          unit: 'kg',
          category: 'Materials',
          is_finished_product: true,
          bill_of_materials: [],
        },
      };

      vi.mocked(client.get).mockResolvedValue(mockResponse);

      await productsAPI.getById(productId);

      // Verify GET was called with full UUID in path
      expect(client.get).toHaveBeenCalledWith(`/api/v1/products/${productId}`);

      const call = vi.mocked(client.get).mock.calls[0];
      expect(call[0]).toContain(productId);
      expect(call[0].split('/').pop()).toBe(productId);
    });

    test('should preserve UUID in response data', async () => {
      const productId = 'abc123def456789012345678abcdef12';

      const mockResponse = {
        data: {
          id: productId,
          code: 'PROD-002',
          name: 'Test Product 2',
          unit: 'kg',
          category: 'Materials',
          is_finished_product: true,
          bill_of_materials: [],
        },
      };

      vi.mocked(client.get).mockResolvedValue(mockResponse);

      const result = await productsAPI.getById(productId);

      expect(result.id).toBe(productId);
      expect(typeof result.id).toBe('string');
      expect(result.id.length).toBe(32);
    });
  });

  describe('Type Coercion Prevention', () => {
    test('should NOT use parseInt() on product IDs', async () => {
      const productId = '471fe408a2604386bae572d9fc9a6b5c';

      const mockResponse = {
        data: {
          calculation_id: 'calc-test',
        },
      };

      vi.mocked(client.post).mockResolvedValue(mockResponse);

      await calculationsAPI.submit({ product_id: productId });

      const call = vi.mocked(client.post).mock.calls[0];
      const sentProductId = call[1].product_id;

      // Should be full UUID string
      expect(sentProductId).toBe(productId);

      // Should NOT be result of parseInt (which would be 471)
      expect(sentProductId).not.toBe(parseInt(productId, 10).toString());
      expect(sentProductId).not.toBe('471');
      expect(sentProductId).not.toBe(471);
    });

    test('should NOT use Number() on UUIDs', async () => {
      const productId = 'abc123def456789012345678abcdef12';

      const mockResponse = {
        data: {
          calculation_id: 'calc-test',
        },
      };

      vi.mocked(client.post).mockResolvedValue(mockResponse);

      await calculationsAPI.submit({ product_id: productId });

      const call = vi.mocked(client.post).mock.calls[0];
      const sentProductId = call[1].product_id;

      // Should be full UUID string
      expect(sentProductId).toBe(productId);

      // Should NOT be NaN (result of Number() on non-numeric string)
      expect(sentProductId).not.toBe('NaN');
      expect(Number.isNaN(Number(sentProductId))).toBe(true); // UUID should not be numeric
    });
  });

  describe('API Response UUID Preservation', () => {
    test('should preserve calculation_id UUID from response', async () => {
      const productId = '471fe408a2604386bae572d9fc9a6b5c';
      const calculationId = 'calc-uuid-response-preservation';

      const mockResponse = {
        data: {
          calculation_id: calculationId,
        },
      };

      vi.mocked(client.post).mockResolvedValue(mockResponse);

      const result = await calculationsAPI.submit({ product_id: productId });

      expect(result.calculation_id).toBe(calculationId);
      expect(typeof result.calculation_id).toBe('string');
    });

    test('should preserve all UUID fields in calculation status response', async () => {
      const calculationId = 'calc-uuid-status-test';
      const productId = 'prod-uuid-status-test';

      const mockResponse = {
        data: {
          id: calculationId,
          status: 'completed',
          product_id: productId,
          total_co2e_kg: 100.5,
        },
      };

      vi.mocked(client.get).mockResolvedValue(mockResponse);

      const result = await calculationsAPI.getStatus(calculationId);

      expect(result.id).toBe(calculationId);
      expect(result.product_id).toBe(productId);
      expect(typeof result.id).toBe('string');
      expect(typeof result.product_id).toBe('string');
    });
  });

  describe('BOM Response UUID Preservation', () => {
    test('should preserve emission factor UUIDs in BOM response', async () => {
      const productId = '471fe408a2604386bae572d9fc9a6b5c';
      const bomEmissionFactorId = 'ef-uuid-bom-test-123';

      const mockResponse = {
        data: {
          id: productId,
          code: 'PROD-001',
          name: 'Test Product',
          unit: 'kg',
          category: 'Materials',
          is_finished_product: true,
          bill_of_materials: [
            {
              id: 'bom-uuid-001',
              child_product_name: 'Cotton',
              quantity: 0.5,
              unit: 'kg',
              emission_factor_id: bomEmissionFactorId,
              notes: null,
            },
          ],
        },
      };

      vi.mocked(client.get).mockResolvedValue(mockResponse);

      const result = await productsAPI.getById(productId);

      expect(result.bill_of_materials[0].emission_factor_id).toBe(bomEmissionFactorId);
      expect(typeof result.bill_of_materials[0].emission_factor_id).toBe('string');
    });
  });
});
