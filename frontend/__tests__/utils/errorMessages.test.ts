/**
 * Error Message Mapping Tests
 *
 * Tests for getUserFriendlyError utility function that maps
 * technical API errors to user-friendly messages.
 *
 * TASK-FE-007: Calculate Flow with Polling (Error Message User-Friendliness)
 */

import { describe, it, expect } from 'vitest';
import { getUserFriendlyError } from '@/utils/errorMessages';

describe('getUserFriendlyError', () => {
  describe('Timeout Errors', () => {
    it('should map timeout error to user-friendly message', () => {
      const result = getUserFriendlyError('Request timeout');
      expect(result).toBe(
        'The calculation is taking longer than expected. The server may be busy. Please try again in a few moments.'
      );
    });

    it('should map TIMEOUT (uppercase) to user-friendly message', () => {
      const result = getUserFriendlyError('TIMEOUT');
      expect(result).toBe(
        'The calculation is taking longer than expected. The server may be busy. Please try again in a few moments.'
      );
    });

    it('should map "connection timeout" to user-friendly message', () => {
      const result = getUserFriendlyError('Connection timeout after 60 seconds');
      expect(result).toBe(
        'The calculation is taking longer than expected. The server may be busy. Please try again in a few moments.'
      );
    });
  });

  describe('Invalid Emission Factor Errors', () => {
    it('should map invalid emission factor error with component name', () => {
      const result = getUserFriendlyError('Invalid emission factor for component: Cotton');
      expect(result).toBe(
        "Unable to calculate emissions. The component 'Cotton' is missing emission data. Please contact support."
      );
    });

    it('should map invalid emission factor error with quoted component', () => {
      const result = getUserFriendlyError('Invalid emission factor for component: "Steel"');
      expect(result).toBe(
        "Unable to calculate emissions. The component 'Steel' is missing emission data. Please contact support."
      );
    });

    it('should map invalid emission factor error without component name', () => {
      const result = getUserFriendlyError('Invalid emission factor');
      expect(result).toBe(
        'Unable to calculate emissions. A component is missing emission data. Please contact support.'
      );
    });

    it('should handle case-insensitive matching', () => {
      const result = getUserFriendlyError('INVALID EMISSION FACTOR FOR COMPONENT: Plastic');
      expect(result).toBe(
        "Unable to calculate emissions. The component 'Plastic' is missing emission data. Please contact support."
      );
    });
  });

  describe('Missing Emission Factor Errors', () => {
    it('should map missing emission factor error with component', () => {
      const result = getUserFriendlyError('Missing emission factor for: Aluminum');
      expect(result).toBe(
        "Unable to calculate emissions. No emission factor found for 'Aluminum'. Please contact support."
      );
    });

    it('should map missing emission factor error without component', () => {
      const result = getUserFriendlyError('Missing emission factor');
      expect(result).toBe(
        'Unable to calculate emissions. Missing emission factor data. Please contact support.'
      );
    });

    it('should map "no emission factor found" variant', () => {
      const result = getUserFriendlyError('No missing emission factor for Glass');
      expect(result).toBe(
        "Unable to calculate emissions. No emission factor found for 'Glass'. Please contact support."
      );
    });
  });

  describe('Network Errors', () => {
    it('should map "network error" to user-friendly message', () => {
      const result = getUserFriendlyError('Network error');
      expect(result).toBe(
        'Unable to connect to the server. Please check your internet connection and try again.'
      );
    });

    it('should map "failed to fetch" to user-friendly message', () => {
      const result = getUserFriendlyError('Failed to fetch');
      expect(result).toBe(
        'Unable to connect to the server. Please check your internet connection and try again.'
      );
    });

    it('should map "network request failed" to user-friendly message', () => {
      const result = getUserFriendlyError('Network request failed');
      expect(result).toBe(
        'Unable to connect to the server. Please check your internet connection and try again.'
      );
    });
  });

  describe('Product Not Found Errors', () => {
    it('should map product not found error', () => {
      const result = getUserFriendlyError('Product not found');
      expect(result).toBe(
        'The selected product could not be found. Please select a valid product and try again.'
      );
    });

    it('should handle case variations', () => {
      const result = getUserFriendlyError('PRODUCT NOT FOUND');
      expect(result).toBe(
        'The selected product could not be found. Please select a valid product and try again.'
      );
    });
  });

  describe('Invalid BOM Errors', () => {
    it('should map "invalid bom" error', () => {
      const result = getUserFriendlyError('Invalid BOM');
      expect(result).toBe(
        'The Bill of Materials contains invalid data. Please review your component selections and quantities.'
      );
    });

    it('should map "invalid bill of materials" error', () => {
      const result = getUserFriendlyError('Invalid Bill of Materials');
      expect(result).toBe(
        'The Bill of Materials contains invalid data. Please review your component selections and quantities.'
      );
    });
  });

  describe('Empty BOM Errors', () => {
    it('should map "empty bom" error', () => {
      const result = getUserFriendlyError('Empty BOM');
      expect(result).toBe(
        'The Bill of Materials is empty. Please add at least one component before calculating.'
      );
    });

    it('should map "no components" error', () => {
      const result = getUserFriendlyError('No components in BOM');
      expect(result).toBe(
        'The Bill of Materials is empty. Please add at least one component before calculating.'
      );
    });
  });

  describe('Validation Errors', () => {
    it('should map validation error to user-friendly message', () => {
      const result = getUserFriendlyError('Validation error: quantity must be positive');
      expect(result).toBe(
        'The request contains invalid data. Please review your inputs and try again.'
      );
    });
  });

  describe('Server Errors', () => {
    it('should map "internal server error" to user-friendly message', () => {
      const result = getUserFriendlyError('Internal server error');
      expect(result).toBe(
        'The server encountered an error. Please try again later or contact support if the problem persists.'
      );
    });

    it('should map "500" error to user-friendly message', () => {
      const result = getUserFriendlyError('HTTP 500 Internal Server Error');
      expect(result).toBe(
        'The server encountered an error. Please try again later or contact support if the problem persists.'
      );
    });

    it('should map "503" service unavailable to user-friendly message', () => {
      const result = getUserFriendlyError('503 Service Unavailable');
      expect(result).toBe(
        'The server encountered an error. Please try again later or contact support if the problem persists.'
      );
    });
  });

  describe('Authorization Errors', () => {
    it('should map "unauthorized" error', () => {
      const result = getUserFriendlyError('Unauthorized');
      expect(result).toBe(
        'You do not have permission to perform this action. Please contact support.'
      );
    });

    it('should map "401" error', () => {
      const result = getUserFriendlyError('HTTP 401 Unauthorized');
      expect(result).toBe(
        'You do not have permission to perform this action. Please contact support.'
      );
    });

    it('should map "forbidden" error', () => {
      const result = getUserFriendlyError('Forbidden');
      expect(result).toBe(
        'You do not have permission to perform this action. Please contact support.'
      );
    });

    it('should map "403" error', () => {
      const result = getUserFriendlyError('HTTP 403 Forbidden');
      expect(result).toBe(
        'You do not have permission to perform this action. Please contact support.'
      );
    });
  });

  describe('Rate Limiting Errors', () => {
    it('should map "rate limit" error', () => {
      const result = getUserFriendlyError('Rate limit exceeded');
      expect(result).toBe('Too many requests. Please wait a moment and try again.');
    });

    it('should map "429" error', () => {
      const result = getUserFriendlyError('HTTP 429 Too Many Requests');
      expect(result).toBe('Too many requests. Please wait a moment and try again.');
    });
  });

  describe('Calculation Failed Errors', () => {
    it('should map generic "calculation failed" error', () => {
      const result = getUserFriendlyError('Calculation failed');
      expect(result).toBe(
        'The calculation could not be completed. Please verify your data and try again, or contact support if the problem persists.'
      );
    });

    it('should map "calculation failed" with details', () => {
      const result = getUserFriendlyError('Calculation failed: unknown error');
      expect(result).toBe(
        'The calculation could not be completed. Please verify your data and try again, or contact support if the problem persists.'
      );
    });
  });

  describe('Database Errors', () => {
    it('should map database error to user-friendly message', () => {
      const result = getUserFriendlyError('Database error: connection lost');
      expect(result).toBe(
        'A database error occurred. Please try again later or contact support.'
      );
    });
  });

  describe('Unknown Errors', () => {
    it('should return default message for unknown error', () => {
      const result = getUserFriendlyError('Something completely unexpected happened');
      expect(result).toBe(
        'An unexpected error occurred during calculation. Please try again or contact support if the problem persists.'
      );
    });

    it('should return default message for empty string', () => {
      const result = getUserFriendlyError('');
      expect(result).toBe(
        'An unexpected error occurred during calculation. Please try again or contact support if the problem persists.'
      );
    });

    it('should return default message for random text', () => {
      const result = getUserFriendlyError('xyz123abc');
      expect(result).toBe(
        'An unexpected error occurred during calculation. Please try again or contact support if the problem persists.'
      );
    });
  });

  describe('Edge Cases', () => {
    it('should handle multi-line error messages', () => {
      const result = getUserFriendlyError('Network error\nFailed to connect\nTimeout');
      expect(result).toBe(
        'Unable to connect to the server. Please check your internet connection and try again.'
      );
    });

    it('should handle error messages with special characters', () => {
      const result = getUserFriendlyError(
        'Invalid emission factor for component: "Cotton (100%)"'
      );
      expect(result).toContain('Cotton (100%)');
    });

    it('should handle very long error messages', () => {
      const longError =
        'This is a very long error message that contains the word timeout somewhere in the middle of a lot of other text that might come from the server';
      const result = getUserFriendlyError(longError);
      expect(result).toBe(
        'The calculation is taking longer than expected. The server may be busy. Please try again in a few moments.'
      );
    });

    it('should prioritize more specific errors over generic ones', () => {
      const result = getUserFriendlyError('Invalid emission factor for component: Wood - timeout');
      // Should match "invalid emission factor" first since it's more specific
      expect(result).toContain('emission data');
    });
  });
});
