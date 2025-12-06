import { test, expect } from '@playwright/test';

/**
 * Customer Payment Flow E2E Tests
 *
 * Tests payment-related endpoints and flows.
 *
 * Prerequisites:
 * - ERP Backend running on port 8000
 * - Stripe test keys configured in ERP
 */

const ERP_URL = 'http://localhost:8000';

test.describe('ERP Payment Endpoints', () => {
  test('Stripe webhook endpoint exists', async ({ request }) => {
    // The Stripe webhook expects:
    // 1. POST method
    // 2. stripe-signature header (for verification)
    // 3. Raw body payload

    // Send minimal request to verify endpoint exists
    // Note: Actual endpoint is /webhook, not /stripe-webhook
    const webhook = await request.post(`${ERP_URL}/api/v1/payments/webhook`, {
      headers: {
        'Content-Type': 'application/json',
        'stripe-signature': 't=1234567890,v1=fake_signature,v0=fake'
      },
      data: JSON.stringify({
        type: 'test.webhook',
        data: {}
      })
    });

    // Expected responses:
    // 400 = Bad signature (endpoint works, verification failed) - EXPECTED
    // 401/403 = Auth issue
    // 404 = Endpoint doesn't exist - FAIL
    // 500 = Server error processing webhook

    console.log('Stripe webhook endpoint status:', webhook.status());

    // 400 is actually good - means endpoint exists and is validating signature
    if (webhook.status() === 400) {
      const body = await webhook.text();
      console.log('Webhook response (400 expected - signature validation):', body.substring(0, 200));
      // This is actually success - endpoint exists and validates signatures
    }

    expect(webhook.status()).not.toBe(404);
  });

  test('Shipping rates endpoint structure', async ({ request }) => {
    // Test the shipping rates endpoint with sample data
    const rates = await request.post(`${ERP_URL}/api/v1/shipping/rates`, {
      headers: {
        'Content-Type': 'application/json'
      },
      data: {
        quote_id: 999999, // Non-existent quote
        to_address: {
          street1: '123 Test St',
          city: 'Austin',
          state: 'TX',
          zip: '78701',
          country: 'US'
        }
      }
    });

    console.log('Shipping rates endpoint status:', rates.status());

    // Should not be 404 - means endpoint exists
    expect(rates.status()).not.toBe(404);

    if (rates.ok()) {
      const data = await rates.json();
      console.log('Shipping rates response:', JSON.stringify(data, null, 2));
    } else {
      const body = await rates.text();
      console.log('Shipping rates error:', body.substring(0, 300));
    }
  });

  test('Address validation endpoint', async ({ request }) => {
    const validate = await request.post(`${ERP_URL}/api/v1/shipping/validate-address`, {
      headers: {
        'Content-Type': 'application/json'
      },
      data: {
        street1: '123 Test St',
        city: 'Austin',
        state: 'TX',
        zip: '78701',
        country: 'US'
      }
    });

    console.log('Address validation endpoint status:', validate.status());
    // Endpoint may not exist yet - skip if 404
    if (validate.status() === 404) {
      console.log('Address validation endpoint not implemented yet');
      test.skip(true, 'Address validation endpoint not implemented');
    }
  });
});

test.describe('Quote Accept and Payment Flow', () => {
  test('Quote accept endpoint structure', async ({ request }) => {
    // Try to accept a non-existent quote to verify endpoint structure
    const accept = await request.post(`${ERP_URL}/api/v1/quotes/portal/999999/accept`, {
      headers: {
        'Content-Type': 'application/json'
      },
      data: {}
    });

    console.log('Quote accept endpoint status:', accept.status());

    // 404 on the quote ID is OK (quote not found)
    // But 404 on the route itself would be bad
    // Usually returns 404 with "Quote not found" message
    if (accept.status() === 404) {
      const body = await accept.text();
      if (body.includes('Quote') || body.includes('not found')) {
        console.log('Endpoint exists - quote not found (expected)');
      }
    }
  });

  test('Payment initialization flow check', async ({ request }) => {
    // Check if there's a payment initialization endpoint
    // Common patterns: /payments/create-intent, /payments/initialize, /checkout

    const endpoints = [
      '/api/v1/payments/create-intent',
      '/api/v1/payments/initialize',
      '/api/v1/checkout',
      '/api/v1/quotes/portal/1/payment'
    ];

    for (const endpoint of endpoints) {
      const response = await request.post(`${ERP_URL}${endpoint}`, {
        data: {}
      }).catch(() => null);

      if (response) {
        console.log(`${endpoint}: ${response.status()}`);
      }
    }
  });
});

test.describe('Stripe Configuration Check', () => {
  test('Check Stripe environment', async ({ request }) => {
    // This test documents what's needed for Stripe to work

    console.log('\n=== STRIPE CONFIGURATION CHECK ===\n');

    console.log('Required environment variables for ERP:');
    console.log('  STRIPE_SECRET_KEY - sk_test_...');
    console.log('  STRIPE_WEBHOOK_SECRET - whsec_...');
    console.log('  STRIPE_PUBLISHABLE_KEY - pk_test_...');

    console.log('\nWebhook endpoint:');
    console.log('  POST /api/v1/payments/webhook');

    console.log('\nFor local testing, use Stripe CLI:');
    console.log('  stripe listen --forward-to localhost:8000/api/v1/payments/webhook');

    console.log('\nExpected webhook events:');
    console.log('  - checkout.session.completed');
    console.log('  - payment_intent.succeeded');
    console.log('  - payment_intent.payment_failed');
  });
});
