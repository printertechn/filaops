import { test, expect } from '@playwright/test';

/**
 * Admin Dashboard E2E Tests
 *
 * Tests the ML Dashboard admin interface.
 *
 * Prerequisites:
 * - ERP Backend running on port 8000
 * - ML Dashboard running on port 5174
 */

const ML_DASHBOARD_URL = 'http://localhost:5174';
const ERP_URL = 'http://localhost:8000';

// Helper to save debug info
async function saveDebugInfo(page: any, testName: string, step: string) {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const screenshotPath = `tests/e2e/screenshots/${testName}-${step}-${timestamp}.png`;
  await page.screenshot({ path: screenshotPath, fullPage: true });
  console.log(`Screenshot saved: ${screenshotPath}`);
}

test.describe('ML Dashboard - Admin Interface', () => {
  test('1. Dashboard loads correctly', async ({ page }) => {
    await page.goto(ML_DASHBOARD_URL);
    await saveDebugInfo(page, 'ml-dashboard', '01-initial-load');

    // Wait for React app to render
    await page.waitForTimeout(2000);

    // Check for main dashboard elements
    const mainContent = page.locator('#root, .app, main, [class*="dashboard"]').first();
    await expect(mainContent).toBeVisible();

    await saveDebugInfo(page, 'ml-dashboard', '02-content-loaded');
  });

  test('2. Navigation tabs exist', async ({ page }) => {
    await page.goto(ML_DASHBOARD_URL);
    await page.waitForTimeout(2000);

    // Look for tab navigation (13 tabs expected)
    const tabs = page.locator('[role="tab"], button[class*="tab"], nav button, .tab');
    const tabCount = await tabs.count();
    console.log(`Found ${tabCount} navigation tabs`);

    await saveDebugInfo(page, 'ml-dashboard', '03-tabs');

    // Check for specific tabs
    const expectedTabs = ['MRP', 'Orders', 'Inventory', 'BOM', 'Production', 'Quote'];
    for (const tabName of expectedTabs) {
      const tab = page.locator(`button:has-text("${tabName}"), [role="tab"]:has-text("${tabName}")`).first();
      if (await tab.isVisible()) {
        console.log(`Tab found: ${tabName}`);
      } else {
        console.log(`Tab NOT found: ${tabName}`);
      }
    }
  });

  test('3. Orders tab shows data', async ({ page }) => {
    await page.goto(ML_DASHBOARD_URL);
    await page.waitForTimeout(2000);

    // Click Orders tab
    const ordersTab = page.locator('button:has-text("Orders"), [role="tab"]:has-text("Orders")').first();
    if (await ordersTab.isVisible()) {
      await ordersTab.click();
      await page.waitForTimeout(1000);
      await saveDebugInfo(page, 'ml-dashboard', '04-orders-tab');
    }

    // Look for order list or table
    const orderElements = page.locator('table, [class*="order"], [class*="list"]').first();
    if (await orderElements.isVisible()) {
      console.log('Order list visible');
    }
  });

  test('4. Inventory tab shows categories', async ({ page }) => {
    await page.goto(ML_DASHBOARD_URL);
    await page.waitForTimeout(2000);

    // Click Inventory tab
    const inventoryTab = page.locator('button:has-text("Inventory"), [role="tab"]:has-text("Inventory")').first();
    if (await inventoryTab.isVisible()) {
      await inventoryTab.click();
      await page.waitForTimeout(1000);
      await saveDebugInfo(page, 'ml-dashboard', '05-inventory-tab');
    }

    // Check for inventory categories
    const categories = ['Materials', 'Components', 'Packaging', 'Finished Goods'];
    for (const category of categories) {
      const categoryElement = page.locator(`button:has-text("${category}"), :text("${category}")`).first();
      if (await categoryElement.isVisible()) {
        console.log(`Category found: ${category}`);
      }
    }
  });

  test('5. Quote Generator tab works', async ({ page }) => {
    await page.goto(ML_DASHBOARD_URL);
    await page.waitForTimeout(2000);

    // Click Quote Generator tab
    const quoteTab = page.locator('button:has-text("Quote"), [role="tab"]:has-text("Quote")').first();
    if (await quoteTab.isVisible()) {
      await quoteTab.click();
      await page.waitForTimeout(1000);
      await saveDebugInfo(page, 'ml-dashboard', '06-quote-generator');

      // Look for file upload
      const fileInput = page.locator('input[type="file"]');
      if (await fileInput.count() > 0) {
        console.log('File upload found in Quote Generator');
      }
    }
  });

  test('6. Live printer status tab', async ({ page }) => {
    await page.goto(ML_DASHBOARD_URL);
    await page.waitForTimeout(2000);

    // Click Live Status tab
    const liveTab = page.locator('button:has-text("Live"), [role="tab"]:has-text("Live"), button:has-text("Status")').first();
    if (await liveTab.isVisible()) {
      await liveTab.click();
      await page.waitForTimeout(1000);
      await saveDebugInfo(page, 'ml-dashboard', '07-live-status');

      // Look for printer status elements
      const printerElements = page.locator('[class*="printer"], [class*="status"]');
      const printerCount = await printerElements.count();
      console.log(`Found ${printerCount} printer-related elements`);
    }
  });
});

test.describe('ERP Admin API Endpoints', () => {
  test('Admin dashboard endpoint', async ({ request }) => {
    const dashboard = await request.get(`${ERP_URL}/api/v1/admin/dashboard`);
    console.log('Admin dashboard status:', dashboard.status());

    if (dashboard.ok()) {
      const data = await dashboard.json();
      console.log('Dashboard summary:', JSON.stringify(data.summary, null, 2));
    }
  });

  test('Internal sales orders endpoint', async ({ request }) => {
    const orders = await request.get(`${ERP_URL}/api/v1/internal/sales-orders`);
    expect(orders.ok()).toBeTruthy();

    const data = await orders.json();
    console.log(`Found ${data.length || 0} orders`);
  });

  test('Internal inventory endpoint', async ({ request }) => {
    const inventory = await request.get(`${ERP_URL}/api/v1/internal/inventory/items`);
    expect(inventory.ok()).toBeTruthy();

    const data = await inventory.json();
    console.log('Inventory categories:', Object.keys(data));
  });

  test('Fulfillment stats endpoint', async ({ request }) => {
    const stats = await request.get(`${ERP_URL}/api/v1/admin/fulfillment/stats`);
    console.log('Fulfillment stats status:', stats.status());

    if (stats.ok()) {
      const data = await stats.json();
      console.log('Fulfillment stats:', JSON.stringify(data, null, 2));
    }
  });

  test('Production queue endpoint', async ({ request }) => {
    const queue = await request.get(`${ERP_URL}/api/v1/admin/fulfillment/queue`);
    console.log('Production queue status:', queue.status());

    if (queue.ok()) {
      const data = await queue.json();
      console.log(`Queue items: ${data.items?.length || 0}`);
    }
  });
});
