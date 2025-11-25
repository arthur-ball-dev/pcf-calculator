/**
 * Axios Client Configuration
 *
 * Centralized Axios instance with:
 * - Base URL configuration from environment
 * - 30 second timeout
 * - Request/response interceptors
 * - Error transformation to APIError
 */

import axios, { type AxiosError } from 'axios';
import { APIError } from './errors';

// API Configuration from environment variables
// Default to empty string for production (same-origin requests)
// Set VITE_API_BASE_URL in .env for local development (e.g., http://localhost:8000)
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';
const API_TIMEOUT = 30000; // 30 seconds

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
// Request Interceptor - Logging
// ============================================================================

client.interceptors.request.use(
  (config) => {
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

        // 404 Not Found
        if (status === 404) {
          throw new APIError('NOT_FOUND', 'Resource not found', error);
        }

        // 400 Bad Request / Validation Error
        if (status === 400) {
          const message =
            (error.response.data as any)?.error ||
            'Invalid request. Please check your input.';
          throw new APIError('VALIDATION_ERROR', message, error);
        }

        // 500 Server Error
        if (status >= 500) {
          throw new APIError(
            'SERVER_ERROR',
            'An unexpected server error occurred. Please try again later.',
            error
          );
        }

        // Other HTTP errors
        throw new APIError(
          'UNKNOWN_ERROR',
          `Request failed with status ${status}`,
          error
        );
      }
    }

    // Non-Axios errors - pass through
    throw error;
  }
);

export default client;
