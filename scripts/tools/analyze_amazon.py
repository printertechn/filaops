"""
Analyze Amazon Business CSV for import
"""
import csv
from collections import defaultdict

csv_path = r'c:\Users\brand\OneDrive\Desktop\orders_from_20250101_to_20251204_20251204_0452.csv'

orders = defaultdict(lambda: {'items': [], 'date': None, 'total': 0, 'tax': 0, 'shipping': 0})
unique_products = {}

with open(csv_path, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        order_id = row['Order ID']
        asin = row['ASIN']
        title = row['Title'][:60] if row['Title'] else 'Unknown'
        brand = row['Brand'] or 'Unknown'
        qty = int(row['Item Quantity']) if row['Item Quantity'] else 1

        # Clean up pricing
        def clean_price(val):
            if not val:
                return 0
            return float(str(val).replace(',','').replace('"','').replace('$','').strip() or 0)

        unit_cost = clean_price(row.get('Purchase PPU', '')) or clean_price(row.get('Item Subtotal', ''))
        item_total = clean_price(row.get('Item Net Total', ''))

        # Track unique products
        if asin and asin not in unique_products:
            unique_products[asin] = {
                'asin': asin,
                'title': title,
                'brand': brand,
                'count': 0,
                'total_spent': 0
            }
        if asin:
            unique_products[asin]['count'] += qty
            unique_products[asin]['total_spent'] += item_total

        orders[order_id]['date'] = row['Order Date']
        orders[order_id]['items'].append({
            'asin': asin,
            'title': title,
            'brand': brand,
            'qty': qty,
            'unit_cost': unit_cost,
            'total': item_total
        })

print(f'Total Orders: {len(orders)}')
print(f'Total Unique Products: {len(unique_products)}')
print()
print('=== TOP 25 PRODUCTS BY SPEND ===')
sorted_products = sorted(unique_products.values(), key=lambda x: x['total_spent'], reverse=True)[:25]
for i, p in enumerate(sorted_products, 1):
    print(f"{i:2}. [{p['asin']}] {p['brand'][:12]:12} | ${p['total_spent']:8.2f} | qty:{p['count']:3} | {p['title'][:45]}")

print()
print('=== UNIQUE BRANDS ===')
brands = set(p['brand'] for p in unique_products.values())
for b in sorted(brands):
    print(f"  - {b}")
