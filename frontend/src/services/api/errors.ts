/**
 * API Error Class
 *
 * Custom error class for API-related errors.
 * Provides structured error information for better error handling.
 *
 * When the backend answered with its error envelope
 * ({ error: { code, message, details }, request_id, timestamp }), the
 * field-level details and the request id are carried along so forms can
 * highlight fields and support can trace the request.
 */

import type { APIErrorCode, APIErrorDetail } from '@/types/api.types';

export interface APIErrorOptions {
  details?: ReadonlyArray<APIErrorDetail>;
  requestId?: string;
}

/**
 * APIError - Custom error class for API failures
 *
 * @example
 * throw new APIError('NETWORK_ERROR', 'Unable to connect to server');
 */
export class APIError extends Error {
  public readonly code: APIErrorCode;
  public readonly originalError?: unknown;
  public readonly details: ReadonlyArray<APIErrorDetail>;
  public readonly requestId?: string;

  constructor(
    code: APIErrorCode,
    message: string,
    originalError?: unknown,
    options: APIErrorOptions = {}
  ) {
    super(message);
    this.name = 'APIError';
    this.code = code;
    this.originalError = originalError;
    this.details = options.details ?? [];
    this.requestId = options.requestId;

    // Maintains proper stack trace for where our error was thrown (only available on V8)
    const ErrorWithStackTrace = Error as typeof Error & {
      captureStackTrace?: (target: object, constructor?: new (...args: never[]) => unknown) => void;
    };
    if (typeof ErrorWithStackTrace.captureStackTrace === 'function') {
      ErrorWithStackTrace.captureStackTrace(this, APIError);
    }
  }
}
