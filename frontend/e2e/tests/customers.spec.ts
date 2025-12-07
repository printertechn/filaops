import { test, expect } from '../fixtures/auth';

/**
 * Customer Management Tests
 * Run: npm run test:e2e -- --grep "customers"
 */
test.describe('Customer Management', () => {
  test('should navigate to customers page', async ({ authenticatedPage: page }) => {
    await page.click('text=Customers');
    await expect(page).toHaveURL('/admin/customers');
    await expect(page.locator('h1:has-text("Customers")')).toBeVisible();
  });

  test('should show customer table', async ({ authenticatedPage: page }) => {
    await page.click('text=Customers');
    await expect(page).toHaveURL('/admin/customers');
    await expect(page.locator('table')).toBeVisible({ timeout: 10000 });
  });

  test('should create a new customer', async ({ authenticatedPage: page }) => {
    await page.click('text=Customers');
    await expect(page).toHaveURL('/admin/customers');
    await page.waitForLoadState('networkidle');

    // Click Add Customer button
    await page.click('button:has-text("Add Customer")');
    await expect(page.locator('.fixed h2:has-text("Add New Customer")')).toBeVisible({ timeout: 5000 });

    // Fill in customer details - email is required
    const testEmail = `test-${Date.now()}@example.com`;
    await page.locator('.fixed input[type="email"]').fill(testEmail);

    // Submit the form
    await page.click('.fixed button[type="submit"]');

    // Wait for modal to close (longer timeout for API call)
    await expect(page.locator('.fixed h2:has-text("Add New Customer")')).not.toBeVisible({ timeout: 10000 });

    // Verify the new customer appears in the table
    await page.waitForLoadState('networkidle');
    await expect(page.locator(`text=${testEmail}`)).toBeVisible({ timeout: 5000 });
  });

  test('should view customer details', async ({ authenticatedPage: page }) => {
    await page.click('text=Customers');
    await expect(page).toHaveURL('/admin/customers');
    await page.waitForLoadState('networkidle');

    // Click View on first customer
    const viewButtons = page.locator('tbody button:has-text("View")');
    const count = await viewButtons.count();

    if (count > 0) {
      await viewButtons.first().click();
      // Modal should appear with Close button
      await expect(page.locator('.fixed button:has-text("Close")')).toBeVisible({ timeout: 5000 });
      // Should show customer stats
      await expect(page.locator('.fixed:has-text("Total Orders")')).toBeVisible();
    }
  });

  test('should edit a customer', async ({ authenticatedPage: page }) => {
    await page.click('text=Customers');
    await expect(page).toHaveURL('/admin/customers');
    await page.waitForLoadState('networkidle');

    // Click Edit on first customer
    const editButtons = page.locator('tbody button:has-text("Edit")');
    const count = await editButtons.count();

    if (count > 0) {
      await editButtons.first().click();
      // Edit modal should appear
      await expect(page.locator('.fixed h2:has-text("Edit Customer")')).toBeVisible({ timeout: 5000 });

      // Save changes without modification
      await page.click('.fixed button[type="submit"]');

      // Modal should close (longer timeout for API)
      await expect(page.locator('.fixed h2:has-text("Edit Customer")')).not.toBeVisible({ timeout: 10000 });
    }
  });
});
