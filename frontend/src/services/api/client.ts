/**
 * Axios Client Configuration
 *
 * Centralized Axios instance with:
 * - Base URL configuration from environment
 * - 30 second timeout
 * - Request/response interceptors
 * - Error transformation to APIError
 * - JWT Authorization header injection
 *
 * TASK-QA-P7-032: Added auth token handling for JWT-protected endpoints
 */

import axios, { type AxiosError } from 'axios';
import { APIError } from './errors';
import type { APIErrorCode, APIErrorResponse } from '@/types/api.types';

// API Configuration from environment variables
// Default to empty string for production (same-origin requests)
// Set VITE_API_BASE_URL in .env for local development (e.g., http://localhost:8000)
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';
const API_TIMEOUT = 30000; // 30 seconds

// Auth token storage key (must match E2E fixture)
const AUTH_TOKEN_KEY = 'auth_token';

/**
 * Get auth token from localStorage
 *
 * @returns JWT token string or null if not set
 */
function getAuthToken(): string | null {
  try {
    return localStorage.getItem(AUTH_TOKEN_KEY);
  } catch {
    // localStorage may be unavailable (e.g., private browsing)
    return null;
  }
}

/**
 * Axios client instance with interceptors configured
 */
const client = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ============================================================================
// Request Interceptor - Auth & Logging
// ============================================================================

client.interceptors.request.use(
  (config) => {
    // Add Authorization header if token exists
    const token = getAuthToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Log API requests in development mode
    if (import.meta.env.DEV) {
      console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`);
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// ============================================================================
// Response Interceptor - Error Transformation
// ============================================================================

/** HTTP status to APIErrorCode; anything 5xx is SERVER_ERROR, the rest UNKNOWN_ERROR. */
const STATUS_CODES: Readonly<Record<number, APIErrorCode>> = {
  400: 'VALIDATION_ERROR',
  401: 'UNAUTHORIZED',
  403: 'FORBIDDEN',
  404: 'NOT_FOUND',
  409: 'CONFLICT',
  422: 'VALIDATION_ERROR',
  429: 'RATE_LIMITED',
};

/** User-facing fallback when the response carries no error envelope. */
const GENERIC_MESSAGES: Readonly<Partial<Record<APIErrorCode, string>>> = {
  VALIDATION_ERROR: 'Invalid request. Please check your input.',
  UNAUTHORIZED: 'Authentication required. Please log in.',
  FORBIDDEN: 'You do not have permission to access this resource.',
  NOT_FOUND: 'Resource not found',
  CONFLICT: 'The request conflicts with existing data.',
  RATE_LIMITED: 'Too many requests. Please try again later.',
  SERVER_ERROR: 'An unexpected server error occurred. Please try again later.',
};

/**
 * Recognize the backend's error envelope
 * ({ error: { code, message, details }, request_id, timestamp }).
 * Anything else (an empty body, a proxy's HTML, a legacy shape) yields null.
 */
function parseErrorEnvelope(data: unknown): APIErrorResponse | null {
  if (typeof data !== 'object' || data === null) return null;
  const { error, request_id, timestamp } = data as Partial<APIErrorResponse>;
  if (typeof error !== 'object' || error === null) return null;
  if (typeof error.code !== 'string' || typeof error.message !== 'string') return null;
  return {
    error: {
      code: error.code,
      message: error.message,
      details: Array.isArray(error.details) ? error.details : [],
    },
    request_id: typeof request_id === 'string' ? request_id : '',
    timestamp: typeof timestamp === 'string' ? timestamp : '',
  };
}

client.interceptors.response.use(
  (response) => {
    // Pass through successful responses
    return response;
  },
  (error: AxiosError) => {
    // Transform Axios errors to APIError for consistent error handling

    if (axios.isAxiosError(error)) {
      // Timeout errors
      if (error.code === 'ECONNABORTED') {
        throw new APIError(
          'TIMEOUT',
          'Request timeout. Please check your connection and try again.',
          error
        );
      }

      // Network errors (no response received)
      if (error.request && !error.response) {
        throw new APIError(
          'NETWORK_ERROR',
          'Unable to connect to server. Please check your network connection.',
          error
        );
      }

      // Server responded with error status
      if (error.response) {
        const status = error.response.status;

        // Log detailed error information for debugging
        if (import.meta.env.DEV) {
          console.error(`[API Error] Status: ${status}, URL: ${error.config?.url}, Data:`, error.response.data);
        }

        const envelope = parseErrorEnvelope(error.response.data);
        const code: APIErrorCode =
          status >= 500 ? 'SERVER_ERROR' : (STATUS_CODES[status] ?? 'UNKNOWN_ERROR');

        // The server's message is shown for client errors; 5xx messages are
        // not written for users, so those keep the generic text.
        const message =
          (status < 500 && envelope?.error.message) ||
          GENERIC_MESSAGES[code] ||
          `Request failed with status ${status}`;

        throw new APIError(code, message, error, {
          details: envelope?.error.details,
          requestId: envelope?.request_id || undefined,
        });
      }
    }

    // Non-Axios errors - pass through
    throw error;
  }
);

export default client;
