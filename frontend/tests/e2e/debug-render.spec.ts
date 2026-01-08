/**
 * Debug test to understand why page isn't rendering
 */
import { test, expect } from '@playwright/test';

test('Debug: Page rendering investigation', async ({ page, request }) => {
  const consoleMessages: string[] = [];
  const consoleErrors: string[] = [];
  // TASK-QA-P7-032: Get auth token from API for JWT-protected endpoints
  const authResponse = await request.post('http://localhost:8000/api/v1/auth/login', {
    data: { username: 'e2e-test', password: 'E2ETestPassword123!' },
  });

  let authToken = '';
  if (authResponse.ok()) {
    const authData = await authResponse.json();
    authToken = authData.access_token;
  }

  // Set up localStorage with auth token before navigating
  await page.addInitScript((token) => {
    window.localStorage.setItem('auth_token', token);
    window.localStorage.setItem('pcf-calculator-tour-completed', 'true');
  }, authToken);

  page.on('console', (msg) => {
    const text = msg.text();
    consoleMessages.push(`[${msg.type()}] ${text}`);
    if (msg.type() === 'error') {
      consoleErrors.push(text);
    }
  });

  page.on('pageerror', (error) => {
    consoleErrors.push(`PageError: ${error.message}`);
  });

  // Navigate to page
  await page.goto('/');

  // Wait for network to be idle
  await page.waitForLoadState('networkidle');

  // Additional wait for React hydration
  await page.waitForTimeout(3000);

  // Get HTML content
  const bodyHTML = await page.content();
  console.log('Page HTML length:', bodyHTML.length);
  console.log('Body text content:', await page.textContent('body'));

  // Check if there's a root element
  const rootDiv = page.locator('#root');
  const rootExists = await rootDiv.count();
  console.log('Root div exists:', rootExists > 0);

  if (rootExists > 0) {
    const rootContent = await rootDiv.textContent();
    console.log('Root content:', rootContent);
    const rootHTML = await rootDiv.innerHTML();
    console.log('Root HTML length:', rootHTML.length);
  }

  // Check for specific elements
  const h1Count = await page.locator('h1').count();
  console.log('H1 elements found:', h1Count);

  // Print console messages
  console.log('\n=== Console Messages ===');
  consoleMessages.forEach(msg => console.log(msg));

  console.log('\n=== Console Errors ===');
  consoleErrors.forEach(err => console.log(err));

  // Screenshot
  await page.screenshot({ path: 'screenshots/debug-render.png', fullPage: true });

  // If errors exist, list them
  if (consoleErrors.length > 0) {
    console.log('\nERRORS FOUND:', consoleErrors.length);
  }
});
