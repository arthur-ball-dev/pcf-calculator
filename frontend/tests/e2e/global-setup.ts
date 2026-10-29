/**
 * Playwright Global Setup
 *
 * TASK-QA-P7-032: Global authentication setup for E2E tests
 *
 * This file:
 * 1. Authenticates once at the start of the test run
 * 2. Saves the auth token to a JSON file
 * 3. Subsequent tests read the cached token
 *
 * This approach avoids hitting the auth rate limit (5 attempts per 5 minutes)
 * by authenticating only once per test run.
 */

import { chromium, FullConfig } from '@playwright/test';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

// ESM-compatible __dirname
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// E2E Test User Credentials
const E2E_TEST_USER = {
  username: 'e2e-test',
  password: 'E2ETestPassword123!',
};

// API endpoints
const API_BASE_URL = 'http://localhost:8000';
const AUTH_LOGIN_ENDPOINT = `${API_BASE_URL}/api/v1/auth/login`;

// Path to store auth state
const AUTH_STATE_PATH = path.join(__dirname, '.auth-state.json');

async function globalSetup(config: FullConfig) {
  console.log('[Global Setup] Authenticating for E2E tests...');

  // Use Playwright's request context for API calls
  const browser = await chromium.launch();
  const context = await browser.newContext();

  try {
    // Authenticate via API
    const response = await context.request.post(AUTH_LOGIN_ENDPOINT, {
      data: E2E_TEST_USER,
    });

    if (!response.ok()) {
      const errorText = await response.text();
      throw new Error(
        `E2E Auth failed: ${response.status()} - ${errorText}\n` +
        `Ensure test user '${E2E_TEST_USER.username}' exists in database.\n` +
        `Run: .venv/bin/python -c "from backend.database.seeds.e2e_test_user import seed_e2e_test_user_standalone; seed_e2e_test_user_standalone()"`
      );
    }

    const data = await response.json();

    if (!data.access_token) {
      throw new Error('Auth response missing access_token field');
    }

    // Save auth state to file for use by fixtures
    const authState = {
      token: data.access_token,
      expiresAt: Date.now() + 50 * 60 * 1000, // 50 minutes
    };

    fs.writeFileSync(AUTH_STATE_PATH, JSON.stringify(authState, null, 2));
    console.log('[Global Setup] Auth token cached successfully');

  } finally {
    await browser.close();
  }
}

export default globalSetup;
