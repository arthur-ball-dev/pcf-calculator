/**
 * API Error Class
 *
 * Custom error class for API-related errors.
 * Provides structured error information for better error handling.
 */

import type { APIErrorCode } from '@/types/api.types';

/**
 * APIError - Custom error class for API failures
 *
 * @example
 * throw new APIError('NETWORK_ERROR', 'Unable to connect to server');
 */
export class APIError extends Error {
  public readonly code: APIErrorCode;
  public readonly originalError?: unknown;

  constructor(code: APIErrorCode, message: string, originalError?: unknown) {
    super(message);
    this.name = 'APIError';
    this.code = code;
    this.originalError = originalError;

    // Maintains proper stack trace for where our error was thrown (only available on V8)
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, APIError);
    }
  }
}
