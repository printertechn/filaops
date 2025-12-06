import { defineConfig, devices } from '@playwright/test';

/**
 * BLB3D ERP - Playwright E2E Test Configuration
 *
 * Tests the complete flow across all three services:
 * - ERP Backend (port 8000)
 * - Quote Portal (port 5173)
 * - ML Dashboard (port 5174)
 */

export default defineConfig({
  testDir: './tests/e2e',

  /* Run tests in files in parallel */
  fullyParallel: false, // Sequential for E2E to avoid conflicts

  /* Fail the build on CI if you accidentally left test.only in the source code */
  forbidOnly: !!process.env.CI,

  /* Retry on CI only */
  retries: process.env.CI ? 2 : 0,

  /* Single worker for E2E tests */
  workers: 1,

  /* Reporter to use */
  reporter: [
    ['html', { outputFolder: 'tests/e2e/reports' }],
    ['json', { outputFile: 'tests/e2e/reports/results.json' }],
    ['list']
  ],

  /* Shared settings for all the projects below */
  use: {
    /* Base URL for tests */
    baseURL: 'http://localhost:5173',

    /* Collect trace on failure */
    trace: 'on-first-retry',

    /* Screenshot on failure */
    screenshot: 'only-on-failure',

    /* Video on failure */
    video: 'on-first-retry',

    /* Timeout for actions */
    actionTimeout: 15000,
  },

  /* Configure projects for major browsers */
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  /* Output folders */
  outputDir: 'tests/e2e/test-results',

  /* Global timeout */
  timeout: 60000,

  /* Expect timeout */
  expect: {
    timeout: 10000,
  },
});
