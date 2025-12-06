/**
 * BLB3D ERP - Test Data Fixtures
 *
 * Shared test data for E2E tests.
 */

export const ERP_URL = 'http://localhost:8000';
export const PORTAL_URL = 'http://localhost:5173';
export const ML_DASHBOARD_URL = 'http://localhost:5174';

// Test material - should exist in your database
export const TEST_MATERIAL = {
  type: 'PLA_BASIC',
  color: 'BLK',
  sku: 'MAT-PLA-BLK',  // Adjust to match your actual SKU format
};

// Test quantities for production
export const TEST_PRODUCTION = {
  orderedQty: 5,
  goodQty: 4,
  badQty: 1,
  // Expected: 4 good parts, 1 scrapped, no reprint needed (qty fulfilled)
};

// API endpoints for fulfillment workflow
export const ENDPOINTS = {
  // Fulfillment
  fulfillmentStats: '/api/v1/admin/fulfillment/stats',
  productionQueue: '/api/v1/admin/fulfillment/queue',
  startProduction: (id: number) => `/api/v1/admin/fulfillment/queue/${id}/start`,
  completePrint: (id: number) => `/api/v1/admin/fulfillment/queue/${id}/complete-print`,
  passQc: (id: number) => `/api/v1/admin/fulfillment/queue/${id}/pass-qc`,
  failQc: (id: number) => `/api/v1/admin/fulfillment/queue/${id}/fail-qc`,

  // Inventory
  inventoryItems: '/api/v1/internal/inventory/items',
  inventoryTransactions: (productId: number) => `/api/v1/inventory/transactions?product_id=${productId}`,

  // Materials
  materialOptions: '/api/v1/materials/options',

  // Admin
  adminProducts: '/api/v1/admin/products',
  adminBoms: '/api/v1/admin/boms',

  // Production Orders (Phase 5A)
  productionOrders: '/api/v1/production-orders',
  productionOrder: (id: number) => `/api/v1/production-orders/${id}`,
  productionOrderRelease: (id: number) => `/api/v1/production-orders/${id}/release`,
  productionOrderStart: (id: number) => `/api/v1/production-orders/${id}/start`,
  productionOrderComplete: (id: number) => `/api/v1/production-orders/${id}/complete`,
  productionOrderCancel: (id: number) => `/api/v1/production-orders/${id}/cancel`,
  productionOrderHold: (id: number) => `/api/v1/production-orders/${id}/hold`,
  productionOrderOperation: (orderId: number, opId: number) => `/api/v1/production-orders/${orderId}/operations/${opId}`,
  productionOrderOperationStart: (orderId: number, opId: number) => `/api/v1/production-orders/${orderId}/operations/${opId}/start`,
  productionOrderOperationComplete: (orderId: number, opId: number) => `/api/v1/production-orders/${orderId}/operations/${opId}/complete`,
  productionScheduleSummary: '/api/v1/production-orders/schedule/summary',
  productionQueueByWorkCenter: '/api/v1/production-orders/queue/by-work-center',
};

// Helper to create test production order via API
export async function createTestProductionOrder(request: any): Promise<any> {
  // This would normally be triggered by a quote conversion
  // For testing, we may need to create directly via API
  return null; // Implement based on your actual flow
}
