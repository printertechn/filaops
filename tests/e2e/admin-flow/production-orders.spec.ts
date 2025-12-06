import { test, expect } from '@playwright/test';
import { ERP_URL, ENDPOINTS } from '../fixtures/test-data';

/**
 * BLB3D ERP - Production Orders API Tests (Phase 5A)
 *
 * Tests for the production orders (Manufacturing Orders) API.
 * These endpoints manage the production workflow for finished goods.
 *
 * Run with: npx playwright test tests/e2e/admin-flow/production-orders.spec.ts
 */

// Helper to login and get auth token
async function getAuthToken(request: any): Promise<string> {
  const response = await request.post(`${ERP_URL}/api/v1/auth/login`, {
    form: {
      username: 'admin@blb3dprinting.com',
      password: 'AdminPass123!',
    },
  });

  if (!response.ok()) {
    throw new Error('Failed to authenticate - check admin credentials');
  }

  const data = await response.json();
  return data.access_token;
}

test.describe('Production Orders API - Authentication', () => {
  test('GET /production-orders requires authentication', async ({ request }) => {
    const response = await request.get(`${ERP_URL}${ENDPOINTS.productionOrders}`);
    expect(response.status()).toBe(401);

    const data = await response.json();
    expect(data.detail).toContain('Not authenticated');
  });

  test('POST /production-orders requires authentication', async ({ request }) => {
    const response = await request.post(`${ERP_URL}${ENDPOINTS.productionOrders}`, {
      data: { product_id: 1, quantity_ordered: 10 },
    });
    expect(response.status()).toBe(401);
  });

  test('GET /schedule/summary requires authentication', async ({ request }) => {
    const response = await request.get(`${ERP_URL}${ENDPOINTS.productionScheduleSummary}`);
    expect(response.status()).toBe(401);
  });

  test('GET /queue/by-work-center requires authentication', async ({ request }) => {
    const response = await request.get(`${ERP_URL}${ENDPOINTS.productionQueueByWorkCenter}`);
    expect(response.status()).toBe(401);
  });
});

test.describe('Production Orders API - List Endpoint', () => {
  let authToken: string;

  test.beforeAll(async ({ request }) => {
    try {
      authToken = await getAuthToken(request);
    } catch {
      // Skip tests if auth fails
    }
  });

  test('GET /production-orders returns list with auth', async ({ request }) => {
    test.skip(!authToken, 'Auth token not available');

    const response = await request.get(`${ERP_URL}${ENDPOINTS.productionOrders}`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });

    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(Array.isArray(data)).toBeTruthy();
  });

  test('list supports status filter', async ({ request }) => {
    test.skip(!authToken, 'Auth token not available');

    const statuses = ['draft', 'released', 'in_progress', 'complete'];

    for (const status of statuses) {
      const response = await request.get(
        `${ERP_URL}${ENDPOINTS.productionOrders}?status=${status}`,
        { headers: { Authorization: `Bearer ${authToken}` } }
      );
      expect(response.ok()).toBeTruthy();

      const data = await response.json();
      if (data.length > 0) {
        data.forEach((order: any) => {
          expect(order.status).toBe(status);
        });
      }
    }
  });

  test('list supports pagination', async ({ request }) => {
    test.skip(!authToken, 'Auth token not available');

    const response = await request.get(
      `${ERP_URL}${ENDPOINTS.productionOrders}?skip=0&limit=5`,
      { headers: { Authorization: `Bearer ${authToken}` } }
    );

    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.length).toBeLessThanOrEqual(5);
  });

  test('list supports priority filter', async ({ request }) => {
    test.skip(!authToken, 'Auth token not available');

    const response = await request.get(
      `${ERP_URL}${ENDPOINTS.productionOrders}?priority=1`,
      { headers: { Authorization: `Bearer ${authToken}` } }
    );

    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    if (data.length > 0) {
      data.forEach((order: any) => {
        expect(order.priority).toBe(1);
      });
    }
  });

  test('list items have required fields', async ({ request }) => {
    test.skip(!authToken, 'Auth token not available');

    const response = await request.get(`${ERP_URL}${ENDPOINTS.productionOrders}`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });

    const data = await response.json();
    if (data.length > 0) {
      const order = data[0];

      // Required fields from ProductionOrderListResponse
      expect(order).toHaveProperty('id');
      expect(order).toHaveProperty('code');
      expect(order).toHaveProperty('product_id');
      expect(order).toHaveProperty('quantity_ordered');
      expect(order).toHaveProperty('quantity_completed');
      expect(order).toHaveProperty('status');
      expect(order).toHaveProperty('priority');
      expect(order).toHaveProperty('created_at');
    }
  });
});

test.describe('Production Orders API - CRUD Operations', () => {
  let authToken: string;

  test.beforeAll(async ({ request }) => {
    try {
      authToken = await getAuthToken(request);
    } catch {
      // Skip tests if auth fails
    }
  });

  test('GET /production-orders/{id} returns 404 for non-existent', async ({ request }) => {
    test.skip(!authToken, 'Auth token not available');

    const response = await request.get(`${ERP_URL}${ENDPOINTS.productionOrder(999999)}`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });

    expect(response.status()).toBe(404);
  });

  test('DELETE /production-orders/{id} returns 404 for non-existent', async ({ request }) => {
    test.skip(!authToken, 'Auth token not available');

    const response = await request.delete(`${ERP_URL}${ENDPOINTS.productionOrder(999999)}`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });

    expect(response.status()).toBe(404);
  });

  test('POST /production-orders validates required fields', async ({ request }) => {
    test.skip(!authToken, 'Auth token not available');

    // Missing product_id
    const response = await request.post(`${ERP_URL}${ENDPOINTS.productionOrders}`, {
      headers: { Authorization: `Bearer ${authToken}` },
      data: { quantity_ordered: 10 },
    });

    expect(response.status()).toBe(422);
  });

  test('POST /production-orders validates product exists', async ({ request }) => {
    test.skip(!authToken, 'Auth token not available');

    const response = await request.post(`${ERP_URL}${ENDPOINTS.productionOrders}`, {
      headers: { Authorization: `Bearer ${authToken}` },
      data: {
        product_id: 999999,
        quantity_ordered: 10,
      },
    });

    expect(response.status()).toBe(404);
    const data = await response.json();
    expect(data.detail).toContain('Product not found');
  });
});

test.describe('Production Orders API - Status Transitions', () => {
  let authToken: string;

  test.beforeAll(async ({ request }) => {
    try {
      authToken = await getAuthToken(request);
    } catch {
      // Skip tests if auth fails
    }
  });

  test('POST /release returns 404 for non-existent order', async ({ request }) => {
    test.skip(!authToken, 'Auth token not available');

    const response = await request.post(`${ERP_URL}${ENDPOINTS.productionOrderRelease(999999)}`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });

    expect(response.status()).toBe(404);
  });

  test('POST /start returns 404 for non-existent order', async ({ request }) => {
    test.skip(!authToken, 'Auth token not available');

    const response = await request.post(`${ERP_URL}${ENDPOINTS.productionOrderStart(999999)}`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });

    expect(response.status()).toBe(404);
  });

  test('POST /complete returns 404 for non-existent order', async ({ request }) => {
    test.skip(!authToken, 'Auth token not available');

    const response = await request.post(`${ERP_URL}${ENDPOINTS.productionOrderComplete(999999)}`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });

    expect(response.status()).toBe(404);
  });

  test('POST /cancel returns 404 for non-existent order', async ({ request }) => {
    test.skip(!authToken, 'Auth token not available');

    const response = await request.post(`${ERP_URL}${ENDPOINTS.productionOrderCancel(999999)}`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });

    expect(response.status()).toBe(404);
  });

  test('POST /hold returns 404 for non-existent order', async ({ request }) => {
    test.skip(!authToken, 'Auth token not available');

    const response = await request.post(`${ERP_URL}${ENDPOINTS.productionOrderHold(999999)}`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });

    expect(response.status()).toBe(404);
  });
});

test.describe('Production Orders API - Schedule Views', () => {
  let authToken: string;

  test.beforeAll(async ({ request }) => {
    try {
      authToken = await getAuthToken(request);
    } catch {
      // Skip tests if auth fails
    }
  });

  test('GET /schedule/summary returns stats object', async ({ request }) => {
    test.skip(!authToken, 'Auth token not available');

    const response = await request.get(`${ERP_URL}${ENDPOINTS.productionScheduleSummary}`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });

    expect(response.ok()).toBeTruthy();
    const data = await response.json();

    // Required fields from ProductionScheduleSummary
    expect(data).toHaveProperty('total_orders');
    expect(data).toHaveProperty('orders_by_status');
    expect(data).toHaveProperty('orders_due_today');
    expect(data).toHaveProperty('orders_overdue');
    expect(data).toHaveProperty('orders_in_progress');
    expect(data).toHaveProperty('total_quantity_to_produce');

    // All values should be numbers >= 0
    expect(data.total_orders).toBeGreaterThanOrEqual(0);
    expect(data.orders_due_today).toBeGreaterThanOrEqual(0);
    expect(data.orders_overdue).toBeGreaterThanOrEqual(0);
    expect(data.orders_in_progress).toBeGreaterThanOrEqual(0);
    expect(data.total_quantity_to_produce).toBeGreaterThanOrEqual(0);
  });

  test('GET /queue/by-work-center returns work center queues', async ({ request }) => {
    test.skip(!authToken, 'Auth token not available');

    const response = await request.get(`${ERP_URL}${ENDPOINTS.productionQueueByWorkCenter}`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });

    expect(response.ok()).toBeTruthy();
    const data = await response.json();

    expect(Array.isArray(data)).toBeTruthy();

    if (data.length > 0) {
      const workCenter = data[0];

      // Required fields from WorkCenterQueue
      expect(workCenter).toHaveProperty('work_center_id');
      expect(workCenter).toHaveProperty('work_center_code');
      expect(workCenter).toHaveProperty('work_center_name');
      expect(workCenter).toHaveProperty('queued_operations');
      expect(workCenter).toHaveProperty('running_operations');
      expect(workCenter).toHaveProperty('total_queued_minutes');

      expect(Array.isArray(workCenter.queued_operations)).toBeTruthy();
      expect(Array.isArray(workCenter.running_operations)).toBeTruthy();
      expect(workCenter.total_queued_minutes).toBeGreaterThanOrEqual(0);
    }
  });
});

test.describe('Production Orders API - Operation Management', () => {
  let authToken: string;

  test.beforeAll(async ({ request }) => {
    try {
      authToken = await getAuthToken(request);
    } catch {
      // Skip tests if auth fails
    }
  });

  test('PUT /operations/{op_id} returns 404 for non-existent', async ({ request }) => {
    test.skip(!authToken, 'Auth token not available');

    const response = await request.put(
      `${ERP_URL}${ENDPOINTS.productionOrderOperation(999999, 999999)}`,
      {
        headers: { Authorization: `Bearer ${authToken}` },
        data: { notes: 'test' },
      }
    );

    expect(response.status()).toBe(404);
  });

  test('POST /operations/{op_id}/start returns 404 for non-existent', async ({ request }) => {
    test.skip(!authToken, 'Auth token not available');

    const response = await request.post(
      `${ERP_URL}${ENDPOINTS.productionOrderOperationStart(999999, 999999)}`,
      {
        headers: { Authorization: `Bearer ${authToken}` },
      }
    );

    expect(response.status()).toBe(404);
  });

  test('POST /operations/{op_id}/complete returns 404 for non-existent', async ({ request }) => {
    test.skip(!authToken, 'Auth token not available');

    const response = await request.post(
      `${ERP_URL}${ENDPOINTS.productionOrderOperationComplete(999999, 999999)}?quantity_completed=1`,
      {
        headers: { Authorization: `Bearer ${authToken}` },
      }
    );

    expect(response.status()).toBe(404);
  });
});

test.describe('Production Orders API - Full Lifecycle Test', () => {
  let authToken: string;
  let testProductId: number | null = null;
  let testOrderId: number | null = null;

  test.beforeAll(async ({ request }) => {
    try {
      authToken = await getAuthToken(request);

      // Get a product to use for testing
      const productsResponse = await request.get(`${ERP_URL}/api/v1/products?limit=1`, {
        headers: { Authorization: `Bearer ${authToken}` },
      });

      if (productsResponse.ok()) {
        const products = await productsResponse.json();
        if (products.length > 0) {
          testProductId = products[0].id;
        }
      }
    } catch {
      // Skip tests if setup fails
    }
  });

  test.afterAll(async ({ request }) => {
    // Cleanup: delete test order if created
    if (testOrderId && authToken) {
      try {
        await request.delete(`${ERP_URL}${ENDPOINTS.productionOrder(testOrderId)}`, {
          headers: { Authorization: `Bearer ${authToken}` },
        });
      } catch {
        // Order might not be in draft status, ignore cleanup errors
      }
    }
  });

  test('create production order', async ({ request }) => {
    test.skip(!authToken || !testProductId, 'Auth or product not available');

    const response = await request.post(`${ERP_URL}${ENDPOINTS.productionOrders}`, {
      headers: { Authorization: `Bearer ${authToken}` },
      data: {
        product_id: testProductId,
        quantity_ordered: 5,
        priority: 2,
        notes: 'Playwright test order',
      },
    });

    expect(response.ok()).toBeTruthy();
    const data = await response.json();

    expect(data).toHaveProperty('id');
    expect(data).toHaveProperty('code');
    expect(data.code).toMatch(/^MO-\d{4}-\d{4}$/);
    expect(data.status).toBe('draft');
    expect(data.quantity_ordered).toBe(5);
    expect(data.priority).toBe(2);

    testOrderId = data.id;
  });

  test('get created production order', async ({ request }) => {
    test.skip(!authToken || !testOrderId, 'Prerequisites not met');

    const response = await request.get(`${ERP_URL}${ENDPOINTS.productionOrder(testOrderId!)}`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });

    expect(response.ok()).toBeTruthy();
    const data = await response.json();

    expect(data.id).toBe(testOrderId);
    expect(data.status).toBe('draft');
    expect(data).toHaveProperty('operations');
    expect(Array.isArray(data.operations)).toBeTruthy();
  });

  test('update production order', async ({ request }) => {
    test.skip(!authToken || !testOrderId, 'Prerequisites not met');

    const response = await request.put(`${ERP_URL}${ENDPOINTS.productionOrder(testOrderId!)}`, {
      headers: { Authorization: `Bearer ${authToken}` },
      data: {
        priority: 1,
        notes: 'Updated by Playwright test',
      },
    });

    expect(response.ok()).toBeTruthy();
    const data = await response.json();

    expect(data.priority).toBe(1);
    expect(data.notes).toContain('Updated by Playwright test');
  });

  test('release production order', async ({ request }) => {
    test.skip(!authToken || !testOrderId, 'Prerequisites not met');

    const response = await request.post(
      `${ERP_URL}${ENDPOINTS.productionOrderRelease(testOrderId!)}`,
      {
        headers: { Authorization: `Bearer ${authToken}` },
      }
    );

    expect(response.ok()).toBeTruthy();
    const data = await response.json();

    expect(data.status).toBe('released');
    expect(data).toHaveProperty('released_at');
    expect(data.released_at).not.toBeNull();
  });

  test('cannot delete released order', async ({ request }) => {
    test.skip(!authToken || !testOrderId, 'Prerequisites not met');

    const response = await request.delete(`${ERP_URL}${ENDPOINTS.productionOrder(testOrderId!)}`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });

    expect(response.status()).toBe(400);
    const data = await response.json();
    expect(data.detail).toContain('Only draft orders can be deleted');
  });

  test('cancel released order', async ({ request }) => {
    test.skip(!authToken || !testOrderId, 'Prerequisites not met');

    const response = await request.post(
      `${ERP_URL}${ENDPOINTS.productionOrderCancel(testOrderId!)}?notes=Cancelled%20by%20test`,
      {
        headers: { Authorization: `Bearer ${authToken}` },
      }
    );

    expect(response.ok()).toBeTruthy();
    const data = await response.json();

    expect(data.status).toBe('cancelled');
    expect(data.notes).toContain('Cancelled');
  });
});
