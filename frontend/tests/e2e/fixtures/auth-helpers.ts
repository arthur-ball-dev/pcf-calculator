/**
 * E2E Authentication Helpers
 *
 * TASK-QA-P7-032: Helper functions for auth token management
 *
 * This module provides utilities for:
 * - Reading cached auth tokens from global setup
 * - Fallback to API authentication if cache is unavailable
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import type { APIRequestContext } from '@playwright/test';

// ESM-compatible __dirname
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// E2E Test User Credentials
export const E2E_TEST_USER = {
  username: 'e2e-test',
  password: 'E2ETestPassword123!',
};

// API endpoints
export const API_BASE_URL = 'http://localhost:8000';
export const AUTH_LOGIN_ENDPOINT = `${API_BASE_URL}/api/v1/auth/login`;
export const FRONTEND_URL = 'http://localhost:5173';

// localStorage key for auth token (must match frontend client.ts usage)
export const AUTH_TOKEN_KEY = 'auth_token';

// Path to cached auth state from global setup
const AUTH_STATE_PATH = path.join(__dirname, '..', '.auth-state.json');

/**
 * Read cached auth token from global setup
 *
 * @returns Cached token or null if not available
 */
export function getCachedToken(): string | null {
  try {
    if (fs.existsSync(AUTH_STATE_PATH)) {
      const data = JSON.parse(fs.readFileSync(AUTH_STATE_PATH, 'utf-8'));
      if (data.token && data.expiresAt > Date.now()) {
        return data.token;
      }
    }
  } catch {
    // Cache read failed, will fall back to API call
  }
  return null;
}

/**
 * Get JWT access token (from cache or API)
 *
 * @param request - Playwright's APIRequestContext
 * @returns JWT access token string
 * @throws Error if authentication fails
 */
export async function getAuthToken(request: APIRequestContext): Promise<string> {
  // Try to use cached token first
  const cachedToken = getCachedToken();
  if (cachedToken) {
    return cachedToken;
  }

  // Fall back to API call if cache is not available
  const response = await request.post(AUTH_LOGIN_ENDPOINT, {
    data: E2E_TEST_USER,
  });

  if (!response.ok()) {
    const errorText = await response.text();
    throw new Error(
      `E2E Auth failed: ${response.status()} - ${errorText}\n` +
        `Ensure test user '${E2E_TEST_USER.username}' exists in database.\n` +
        `Run: python -c "from backend.database.seeds.e2e_test_user import seed_test_user; seed_test_user()"`
    );
  }

  const data = await response.json();

  if (!data.access_token) {
    throw new Error('Auth response missing access_token field');
  }

  return data.access_token;
}
