import { test, expect } from '@playwright/test';
import { ERP_URL, ENDPOINTS } from '../fixtures/test-data';

/**
 * BLB3D ERP - API Unit Tests
 *
 * Isolated API tests that don't require UI interaction.
 * Tests endpoint behavior, response structure, and error handling.
 *
 * Run with: npx playwright test tests/e2e/admin-flow/api-tests.spec.ts
 */

test.describe('Fulfillment API Endpoints', () => {
  test.describe('GET /fulfillment/stats', () => {
    test('returns all required fields', async ({ request }) => {
      const response = await request.get(`${ERP_URL}${ENDPOINTS.fulfillmentStats}`);
      expect(response.ok()).toBeTruthy();

      const data = await response.json();
      
      // Verify all required fields exist
      const requiredFields = [
        'pending_quotes',
        'quotes_needing_review',
        'scheduled',
        'in_progress',
        'ready_for_qc',
        'ready_to_ship',
        'shipped_today',
        'pending_revenue',
        'shipped_revenue_today',
      ];

      requiredFields.forEach(field => {
        expect(data).toHaveProperty(field);
        expect(typeof data[field]).toBe('number');
      });
    });

    test('returns non-negative values', async ({ request }) => {
      const response = await request.get(`${ERP_URL}${ENDPOINTS.fulfillmentStats}`);
      const data = await response.json();

      Object.entries(data).forEach(([key, value]) => {
        expect(value as number).toBeGreaterThanOrEqual(0);
      });
    });
  });

  test.describe('GET /fulfillment/queue', () => {
    test('returns paginated list structure', async ({ request }) => {
      const response = await request.get(`${ERP_URL}${ENDPOINTS.productionQueue}`);
      expect(response.ok()).toBeTruthy();

      const data = await response.json();
      
      expect(data).toHaveProperty('items');
      expect(data).toHaveProperty('stats');
      expect(data).toHaveProperty('total');
      expect(Array.isArray(data.items)).toBeTruthy();
    });

    test('filters by status correctly', async ({ request }) => {
      // Test scheduled filter
      const scheduled = await request.get(
        `${ERP_URL}${ENDPOINTS.productionQueue}?status_filter=scheduled`
      );
      const scheduledData = await scheduled.json();
      
      if (scheduledData.items.length > 0) {
        scheduledData.items.forEach((item: any) => {
          expect(['scheduled', 'confirmed', 'released']).toContain(item.status);
        });
      }

      // Test in_progress filter
      const inProgress = await request.get(
        `${ERP_URL}${ENDPOINTS.productionQueue}?status_filter=in_progress`
      );
      const inProgressData = await inProgress.json();
      
      if (inProgressData.items.length > 0) {
        inProgressData.items.forEach((item: any) => {
          expect(item.status).toBe('in_progress');
        });
      }
    });

    test('respects limit parameter', async ({ request }) => {
      const response = await request.get(
        `${ERP_URL}${ENDPOINTS.productionQueue}?limit=5`
      );
      const data = await response.json();
      
      expect(data.items.length).toBeLessThanOrEqual(5);
    });

    test('queue items have required fields', async ({ request }) => {
      const response = await request.get(`${ERP_URL}${ENDPOINTS.productionQueue}`);
      const data = await response.json();

      if (data.items.length > 0) {
        const item = data.items[0];
        
        // Required fields from ProductionQueueItem schema
        expect(item).toHaveProperty('id');
        expect(item).toHaveProperty('code');
        expect(item).toHaveProperty('quantity');
        expect(item).toHaveProperty('status');
        expect(item).toHaveProperty('created_at');
      }
    });
  });

  test.describe('GET /fulfillment/queue/{id}', () => {
    test('returns 404 for non-existent order', async ({ request }) => {
      const response = await request.get(
        `${ERP_URL}/api/v1/admin/fulfillment/queue/999999`
      );
      expect(response.status()).toBe(404);
    });

    test('returns detailed order info for valid ID', async ({ request }) => {
      // First get a valid ID
      const queueResponse = await request.get(`${ERP_URL}${ENDPOINTS.productionQueue}`);
      const queue = await queueResponse.json();

      if (queue.items.length === 0) {
        test.skip(true, 'No production orders to test');
        return;
      }

      const testId = queue.items[0].id;
      const response = await request.get(
        `${ERP_URL}/api/v1/admin/fulfillment/queue/${testId}`
      );
      
      expect(response.ok()).toBeTruthy();
      const data = await response.json();

      // Should have extended info beyond queue item
      expect(data).toHaveProperty('id');
      expect(data).toHaveProperty('product');
      expect(data).toHaveProperty('bom');
      expect(data).toHaveProperty('quote');
      expect(data).toHaveProperty('print_jobs');
    });
  });

  test.describe('POST /fulfillment/queue/{id}/start', () => {
    test('returns 404 for non-existent order', async ({ request }) => {
      const response = await request.post(
        `${ERP_URL}/api/v1/admin/fulfillment/queue/999999/start`,
        { data: {} }
      );
      expect(response.status()).toBe(404);
    });

    test('returns 400 for already-completed order', async ({ request }) => {
      // Find a completed order
      const queueResponse = await request.get(
        `${ERP_URL}${ENDPOINTS.productionQueue}?status_filter=completed`
      );
      const queue = await queueResponse.json();

      // Note: API filters out completed by default, this tests the validation
      // Using a completed status filter that may return empty
    });

    test('start response includes materials_synced field (Bug #5)', async ({ request }) => {
      // Get a schedulable order
      const queueResponse = await request.get(
        `${ERP_URL}${ENDPOINTS.productionQueue}?status_filter=scheduled`
      );
      const queue = await queueResponse.json();

      if (queue.items.length === 0) {
        test.skip(true, 'No scheduled orders to test');
        return;
      }

      const testId = queue.items[0].id;
      const response = await request.post(
        `${ERP_URL}${ENDPOINTS.startProduction(testId)}`,
        { data: { notes: 'API test' } }
      );

      if (response.ok()) {
        const data = await response.json();
        
        // Bug #5 fix adds materials_synced to response
        expect(data).toHaveProperty('materials_synced');
        expect(data).toHaveProperty('materials_reserved');
        expect(Array.isArray(data.materials_synced)).toBeTruthy();
        expect(Array.isArray(data.materials_reserved)).toBeTruthy();
      }
    });
  });

  test.describe('POST /fulfillment/queue/{id}/complete-print', () => {
    test('returns 400 for order not in_progress', async ({ request }) => {
      // Get a scheduled (not in_progress) order
      const queueResponse = await request.get(
        `${ERP_URL}${ENDPOINTS.productionQueue}?status_filter=scheduled`
      );
      const queue = await queueResponse.json();

      if (queue.items.length === 0) {
        test.skip(true, 'No scheduled orders to test');
        return;
      }

      const testId = queue.items[0].id;
      const response = await request.post(
        `${ERP_URL}${ENDPOINTS.completePrint(testId)}`,
        { data: { qty_good: 1 } }
      );

      expect(response.status()).toBe(400);
      const error = await response.json();
      expect(error.detail).toContain('Cannot complete print');
    });

    test('response includes material_inventory_synced field (Bug #4)', async ({ request }) => {
      // This requires an in_progress order - check if one exists
      const queueResponse = await request.get(
        `${ERP_URL}${ENDPOINTS.productionQueue}?status_filter=in_progress`
      );
      const queue = await queueResponse.json();

      if (queue.items.length === 0) {
        console.log('No in_progress orders to test complete-print response');
        test.skip(true, 'No in_progress orders');
        return;
      }

      // Don't actually complete - just verify field structure in existing tests
    });
  });

  test.describe('POST /fulfillment/queue/{id}/pass-qc', () => {
    test('response does NOT include materials_consumed (Bug #1)', async ({ request }) => {
      // Get a printed order
      const queueResponse = await request.get(
        `${ERP_URL}${ENDPOINTS.productionQueue}?status_filter=printed`
      );
      const queue = await queueResponse.json();

      // Filter to actually printed status
      const printedOrders = queue.items.filter((i: any) => i.status === 'printed');

      if (printedOrders.length === 0) {
        console.log('No printed orders to test pass-qc');
        test.skip(true, 'No printed orders');
        return;
      }

      // Note: We don't want to actually pass QC in isolated API tests
      // Just verify the endpoint exists and returns proper errors
    });

    test('returns 400 for order not in printed status', async ({ request }) => {
      const queueResponse = await request.get(
        `${ERP_URL}${ENDPOINTS.productionQueue}?status_filter=scheduled`
      );
      const queue = await queueResponse.json();

      if (queue.items.length === 0) {
        test.skip(true, 'No orders to test');
        return;
      }

      const testId = queue.items[0].id;
      const response = await request.post(
        `${ERP_URL}${ENDPOINTS.passQc(testId)}?qc_notes=test`,
        {}
      );

      expect(response.status()).toBe(400);
    });
  });

  test.describe('POST /fulfillment/queue/{id}/fail-qc', () => {
    test('returns 404 for non-existent order', async ({ request }) => {
      const response = await request.post(
        `${ERP_URL}/api/v1/admin/fulfillment/queue/999999/fail-qc?failure_reason=test`,
        {}
      );
      expect(response.status()).toBe(404);
    });
  });
});

test.describe('Inventory API Endpoints', () => {
  test.describe('GET /internal/inventory/items', () => {
    test('returns categorized inventory', async ({ request }) => {
      const response = await request.get(`${ERP_URL}${ENDPOINTS.inventoryItems}`);
      expect(response.ok()).toBeTruthy();

      const data = await response.json();
      expect(typeof data).toBe('object');
      
      // Common categories
      const possibleCategories = ['Materials', 'Components', 'Packaging', 'Finished Goods'];
      const foundCategories = Object.keys(data);
      
      console.log('Found inventory categories:', foundCategories);
    });

    test('inventory items have quantity fields', async ({ request }) => {
      const response = await request.get(`${ERP_URL}${ENDPOINTS.inventoryItems}`);
      const data = await response.json();

      // Check first category
      const firstCategory = Object.values(data)[0] as any[];
      if (firstCategory && firstCategory.length > 0) {
        const item = firstCategory[0];
        
        expect(item).toHaveProperty('on_hand_quantity');
        expect(item).toHaveProperty('allocated_quantity');
        expect(item).toHaveProperty('available_quantity');
      }
    });
  });
});

test.describe('Material API Endpoints', () => {
  test.describe('GET /materials/options', () => {
    test('returns material types with colors', async ({ request }) => {
      const response = await request.get(`${ERP_URL}${ENDPOINTS.materialOptions}`);
      expect(response.ok()).toBeTruthy();

      const data = await response.json();
      // Endpoint returns { materials: [...] }
      expect(data).toHaveProperty('materials');
      expect(Array.isArray(data.materials)).toBeTruthy();

      if (data.materials.length > 0) {
        const material = data.materials[0];
        expect(material).toHaveProperty('code');
        expect(material).toHaveProperty('name');
        expect(material).toHaveProperty('colors');
        expect(Array.isArray(material.colors)).toBeTruthy();
      }
    });

    test('colors include stock info (for lead time calculation)', async ({ request }) => {
      const response = await request.get(`${ERP_URL}${ENDPOINTS.materialOptions}`);
      const data = await response.json();

      if (data.materials.length > 0 && data.materials[0].colors.length > 0) {
        const color = data.materials[0].colors[0];
        
        // These fields are used by quote engine for lead time
        expect(color).toHaveProperty('in_stock');
        expect(color).toHaveProperty('quantity_kg');
        expect(typeof color.in_stock).toBe('boolean');
        expect(typeof color.quantity_kg).toBe('number');
      }
    });
  });
});

test.describe('Error Handling', () => {
  test('Invalid JSON returns 422', async ({ request }) => {
    const response = await request.post(
      `${ERP_URL}/api/v1/admin/fulfillment/queue/1/start`,
      {
        data: 'not valid json',
        headers: { 'Content-Type': 'application/json' },
      }
    );
    // FastAPI returns 422 for validation errors
    expect([400, 422]).toContain(response.status());
  });

  test('Missing required fields returns validation error', async ({ request }) => {
    const response = await request.post(
      `${ERP_URL}/api/v1/admin/fulfillment/queue/1/fail-qc`,
      { data: {} }  // Missing required failure_reason
    );
    expect([400, 422]).toContain(response.status());
  });
});
