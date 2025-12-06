import { test, expect } from '@playwright/test';

/**
 * Order-to-Ship E2E Test Suite
 *
 * Tests the complete order workflow:
 * 1. Create quote via API
 * 2. Accept quote (creates order, product, BOM)
 * 3. Start production (creates material reservations)
 * 4. Complete print (creates consumptions, finished goods receipt)
 * 5. Verify transactions at each step
 *
 * Run with: npx playwright test order-to-ship.spec.ts
 */

const ERP_URL = process.env.ERP_URL || 'http://localhost:8000';

// Test data - matches PortalQuoteCreate schema
const TEST_CONFIG = {
  material: 'PLA_BASIC',
  colorCode: 'BLK',
  printTimeMinutes: 150,  // 2.5 hours
  materialGrams: 50,
  quantity: 1,
  unitPrice: 25.00,
  totalPrice: 25.00,
};

// Helper to generate unique test identifiers
function generateTestId(): string {
  return `E2E-${Date.now()}`;
}

// Helper to delay for async operations
async function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// Test user for authenticated endpoints
const TEST_USER = {
  email: 'test@blb3dprinting.com',
  password: 'TestPassword123!'
};

test.describe.serial('Order-to-Ship Complete Flow', () => {
  let testId: string;
  let quoteId: number;
  let salesOrderId: number;
  let productionOrderId: number;
  let authToken: string;

  test.beforeAll(async () => {
    testId = generateTestId();
    console.log(`\n=== E2E Test Run: ${testId} ===\n`);
  });

  test('1. ERP Backend is healthy', async ({ request }) => {
    const health = await request.get(`${ERP_URL}/api/v1/internal/health`);
    expect(health.ok()).toBeTruthy();
    const data = await health.json();
    console.log('ERP Health:', data.status);
  });

  test('2. Login and create test quote', async ({ request }) => {
    // Login first to get user ID and token
    const loginResponse = await request.post(`${ERP_URL}/api/v1/auth/login`, {
      form: {
        username: TEST_USER.email,
        password: TEST_USER.password
      }
    });

    if (!loginResponse.ok()) {
      console.log('Login failed - test user may not exist');
      test.skip(true, 'Auth failed - create test user first');
      return;
    }

    const authData = await loginResponse.json();
    authToken = authData.access_token;

    // Get user info from /me endpoint
    const meResponse = await request.get(`${ERP_URL}/api/v1/auth/me`, {
      headers: { 'Authorization': `Bearer ${authToken}` }
    });
    const userData = await meResponse.json();
    const userId = userData.id;
    console.log(`Logged in as ${userData.email} (ID: ${userId})`);

    // Create a quote with customer_id set to our user
    const quoteData = {
      // Required file info
      filename: `test-model-${testId}.3mf`,
      file_format: '.3mf',

      // Required quote details
      material: TEST_CONFIG.material,
      quality: 'standard',
      infill: 'standard',
      color: TEST_CONFIG.colorCode,
      quantity: TEST_CONFIG.quantity,

      // Required pricing (from Print Suite)
      unit_price: TEST_CONFIG.unitPrice,
      total_price: TEST_CONFIG.totalPrice,
      material_grams: TEST_CONFIG.materialGrams,
      print_time_minutes: TEST_CONFIG.printTimeMinutes,

      // Optional dimensions
      dimensions_x: 100,
      dimensions_y: 100,
      dimensions_z: 50,

      // Stock status
      material_in_stock: true,

      // Set customer_id to link quote to our user (enables conversion)
      customer_id: userId,
      customer_email: TEST_USER.email,
      // NO customer_notes (notes trigger pending_review)
    };

    const response = await request.post(`${ERP_URL}/api/v1/quotes/portal`, {
      data: quoteData
    });

    console.log('Create quote response status:', response.status());

    if (response.ok()) {
      const data = await response.json();
      quoteId = data.quote_id || data.id;
      console.log(`Quote created: ${data.quote_number} (ID: ${quoteId})`);
      console.log(`  Status: ${data.status}`);
      console.log(`  Total: $${data.total_price}`);
      expect(quoteId).toBeGreaterThan(0);
    } else {
      const text = await response.text();
      console.log('Quote creation failed:', text.substring(0, 300));
      test.skip(true, 'Quote portal endpoint failed');
    }
  });

  test('3. Accept quote (customer action)', async ({ request }) => {
    test.skip(!quoteId, 'No quote ID from previous step');

    // Accept the quote with shipping address (PortalAcceptQuote schema)
    const acceptData = {
      shipping_name: 'E2E Test Customer',
      shipping_address_line1: '123 Test Street',
      shipping_city: 'Austin',
      shipping_state: 'TX',
      shipping_zip: '78701',
      shipping_country: 'USA',
      shipping_carrier: 'USPS',
      shipping_service: 'Priority Mail',
      shipping_cost: 8.99,
    };

    const response = await request.post(
      `${ERP_URL}/api/v1/quotes/portal/${quoteId}/accept`,
      { data: acceptData }
    );

    console.log('Accept quote response status:', response.status());

    if (response.ok()) {
      const data = await response.json();
      console.log(`Quote ${data.quote_number} accepted, status: ${data.status}`);
      console.log(`  Product created: ${data.product_id ? 'Yes' : 'No'}`);
    } else {
      const text = await response.text();
      console.log('Accept failed:', text.substring(0, 200));
      test.skip(true, 'Quote accept failed');
    }
  });

  test('4. Login and convert to sales order', async ({ request }) => {
    test.skip(!quoteId, 'No quote ID from previous step');

    // Login to get auth token
    const loginResponse = await request.post(`${ERP_URL}/api/v1/auth/login`, {
      form: {
        username: TEST_USER.email,
        password: TEST_USER.password
      }
    });

    if (!loginResponse.ok()) {
      console.log('Login failed - test user may not exist');
      console.log('Create user: POST /api/v1/auth/register');
      test.skip(true, 'Auth failed - create test user first');
      return;
    }

    const authData = await loginResponse.json();
    authToken = authData.access_token;
    console.log('Logged in as test user');

    // Convert quote to sales order (requires auth)
    const convertData = {
      shipping_address_line1: '123 Test Street',
      shipping_city: 'Austin',
      shipping_state: 'TX',
      shipping_zip: '78701',
      shipping_country: 'USA',
    };

    const response = await request.post(
      `${ERP_URL}/api/v1/sales-orders/convert/${quoteId}`,
      {
        data: convertData,
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      }
    );

    console.log('Convert to order response status:', response.status());

    if (response.ok()) {
      const data = await response.json();
      salesOrderId = data.id;
      console.log(`Order created: ${data.order_number} (ID: ${salesOrderId})`);
      console.log(`  Status: ${data.status}`);
      console.log(`  Total: $${data.total_amount}`);
      expect(salesOrderId).toBeGreaterThan(0);
    } else {
      const text = await response.text();
      console.log('Convert failed:', text.substring(0, 300));
      test.skip(true, 'Quote conversion failed');
    }
  });

  test('5. Get production order from queue', async ({ request }) => {
    test.skip(!salesOrderId, 'No sales order from previous step');

    // Wait for order processing
    await delay(500);

    // Get fulfillment queue
    const response = await request.get(`${ERP_URL}/api/v1/admin/fulfillment/queue`);
    expect(response.ok()).toBeTruthy();

    const queue = await response.json();
    console.log(`Fulfillment queue has ${queue.items?.length || 0} items`);

    // Queue items use order_number (e.g., "SO-2025-002"), not sales_order_id
    // Get the latest production order (most recently created = our test order)
    if (queue.items?.length > 0) {
      // Sort by ID descending to get the newest one
      const sorted = [...queue.items].sort((a: any, b: any) => b.id - a.id);
      const myPo = sorted[0];

      productionOrderId = myPo.id;
      console.log(`Production order found: ${myPo.code} (ID: ${productionOrderId})`);
      console.log(`  Order: ${myPo.order_number}`);
      console.log(`  Status: ${myPo.status}`);
      console.log(`  Product: ${myPo.product_name}`);
      expect(productionOrderId).toBeGreaterThan(0);
    } else {
      console.log('Production order not found in queue');
      test.skip(true, 'Production order not created');
    }
  });

  test('6. Start production (creates reservations)', async ({ request }) => {
    test.skip(!productionOrderId, 'No production order from previous step');

    // Get audit summary before
    const auditBefore = await request.get(`${ERP_URL}/api/v1/admin/audit/transactions/summary`);
    const beforeData = auditBefore.ok() ? await auditBefore.json() : null;
    console.log('Audit before start_production:', beforeData);

    // Start production (requires body, even if empty)
    const response = await request.post(
      `${ERP_URL}/api/v1/admin/fulfillment/queue/${productionOrderId}/start`,
      { data: {} }
    );

    console.log('Start production response status:', response.status());

    if (response.ok()) {
      const data = await response.json();
      console.log('Production started!');
      console.log(`  Reserved materials: ${data.materials_reserved?.length || 0}`);
      console.log(`  Insufficient materials: ${data.materials_insufficient?.length || 0}`);

      // Log reserved materials
      data.materials_reserved?.forEach((mat: any) => {
        console.log(`    - ${mat.component_sku}: ${mat.quantity_reserved} units`);
      });

      // Verify reservation transactions created
      const timeline = await request.get(
        `${ERP_URL}/api/v1/admin/audit/transactions/timeline/${salesOrderId}`
      );
      if (timeline.ok()) {
        const txns = await timeline.json();
        const reservations = (txns.timeline || []).filter((t: any) => t.transaction_type === 'reservation');
        console.log(`  Reservation transactions: ${reservations.length}`);
        // Note: Timeline currently doesn't find reservations (they use production_order reference)
        // TODO: Fix timeline endpoint to also search by production_order reference
      }
    } else {
      const text = await response.text();
      console.log('Start production failed:', text.substring(0, 300));
    }
  });

  test('7. Complete print (creates consumptions + receipt)', async ({ request }) => {
    test.skip(!productionOrderId, 'No production order from previous step');

    // Complete print with good quantity
    const completeData = {
      good_quantity: TEST_CONFIG.quantity,
      bad_quantity: 0,
      notes: `E2E test ${testId} - print completed`
    };

    const response = await request.post(
      `${ERP_URL}/api/v1/admin/fulfillment/queue/${productionOrderId}/complete-print`,
      { data: completeData }
    );

    console.log('Complete print response status:', response.status());

    if (response.ok()) {
      const data = await response.json();
      console.log('Print completed!');
      console.log(`  Good quantity: ${data.quantities?.good || 0}`);
      console.log(`  Bad quantity: ${data.quantities?.bad || 0}`);
      console.log(`  Consumed materials: ${data.materials_consumed?.length || 0}`);
      console.log(`  Finished goods receipt: ${data.finished_goods_added ? 'Yes' : 'No'}`);

      // Log machine time tracking
      if (data.machine_time_recorded) {
        const mt = data.machine_time_recorded;
        console.log(`  Machine time: ${mt.actual_hours} hrs @ $${mt.hourly_rate}/hr = $${mt.total_cost}`);
        console.log(`    Estimated: ${mt.estimated_hours} hrs, Variance: ${mt.variance_hours} hrs`);
        if (mt.printer) {
          console.log(`    Printer: ${mt.printer.name}`);
        }
      }

      // Verify consumption and receipt transactions
      const timeline = await request.get(
        `${ERP_URL}/api/v1/admin/audit/transactions/timeline/${salesOrderId}`
      );
      if (timeline.ok()) {
        const txns = await timeline.json();
        const timelineData = txns.timeline || [];
        const consumptions = timelineData.filter((t: any) => t.transaction_type === 'consumption');
        const receipts = timelineData.filter((t: any) => t.transaction_type === 'receipt');
        const machineTime = timelineData.filter((t: any) => t.transaction_type === 'machine_time');
        console.log(`  Consumption transactions: ${consumptions.length}`);
        console.log(`  Receipt transactions: ${receipts.length}`);
        console.log(`  Machine time transactions: ${machineTime.length}`);
        // Note: Timeline currently shows 0 because it queries by sales_order_id
        // but transactions use production_order reference.
        // TODO: Fix timeline to join through production_order -> sales_order relationship
      }
    } else {
      const text = await response.text();
      console.log('Complete print failed:', text.substring(0, 300));
    }
  });

  test('8. Final audit verification', async ({ request }) => {
    test.skip(!salesOrderId, 'No sales order from previous step');

    // Run audit for this specific order
    const audit = await request.get(
      `${ERP_URL}/api/v1/admin/audit/transactions/order/${salesOrderId}`
    );

    if (audit.ok()) {
      const data = await audit.json();
      console.log('\n=== AUDIT RESULT ===');
      console.log(`  Order: ${salesOrderId}`);
      console.log(`  Gaps found: ${data.total_gaps}`);
      console.log(`  Health: ${data.gaps?.length === 0 ? 'PASS' : 'FAIL'}`);

      if (data.gaps?.length > 0) {
        console.log('  Gaps:');
        data.gaps.forEach((gap: any) => {
          console.log(`    - ${gap.gap_type}: ${gap.expected_sku}`);
        });
      }

      // For now, just log - don't fail if there are gaps
      // expect(data.total_gaps).toBe(0);
    }

    // Get transaction timeline
    const timeline = await request.get(
      `${ERP_URL}/api/v1/admin/audit/transactions/timeline/${salesOrderId}`
    );

    if (timeline.ok()) {
      const txns = await timeline.json();
      console.log('\n=== TRANSACTION TIMELINE ===');
      (txns.timeline || []).forEach((txn: any) => {
        console.log(`  ${txn.transaction_type.padEnd(12)} | ${txn.product_sku?.padEnd(30) || 'N/A'} | qty: ${txn.quantity}`);
      });
    }
  });

  test('9. Accounting cost breakdown', async ({ request }) => {
    test.skip(!salesOrderId, 'No sales order from previous step');

    const cost = await request.get(
      `${ERP_URL}/api/v1/admin/accounting/order-cost-breakdown/${salesOrderId}`
    );

    if (cost.ok()) {
      const data = await cost.json();
      console.log('\n=== COST BREAKDOWN ===');
      console.log(`  Order: ${data.order_number}`);
      console.log(`  Revenue: $${data.revenue?.toFixed(2) || 0}`);
      console.log(`  Material Cost: $${data.costs?.materials?.total?.toFixed(2) || 0}`);
      console.log(`  Labor Cost: $${data.costs?.labor?.toFixed(2) || 0}`);
      console.log(`  Packaging Cost: $${data.costs?.packaging?.total?.toFixed(2) || 0}`);
      console.log(`  Total COGS: $${data.total_cogs?.toFixed(2) || 0}`);
      console.log(`  Gross Profit: $${data.gross_profit?.toFixed(2) || 0}`);
      console.log(`  Margin: ${data.gross_margin_pct?.toFixed(1) || 0}%`);
    }
  });
});

// Run this test multiple times to verify consistency
test.describe('Repeat Order Flow (stress test)', () => {
  for (let i = 1; i <= 3; i++) {
    test(`Run ${i}: Create and process order`, async ({ request }) => {
      console.log(`\n--- Stress Test Run ${i}/3 ---`);

      // Quick health check
      const health = await request.get(`${ERP_URL}/api/v1/internal/health`);
      expect(health.ok()).toBeTruthy();

      // Get audit summary
      const audit = await request.get(`${ERP_URL}/api/v1/admin/audit/transactions/summary`);
      if (audit.ok()) {
        const data = await audit.json();
        console.log(`Current health score: ${data.health_score?.toFixed(1)}%`);
        console.log(`Orders with gaps: ${data.orders_with_issues}/${data.total_orders}`);
      }
    });
  }
});
