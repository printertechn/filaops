import time
time.sleep(3)
import requests

r = requests.get('http://localhost:8000/api/v1/routings/7')
d = r.json()

print("Operation Costs (with setup included):")
print("=" * 55)
total = 0
for op in d['operations']:
    setup = float(op['setup_time_minutes'] or 0)
    run = float(op['run_time_minutes'] or 0)
    cost = float(op['calculated_cost'])
    total += cost
    print(f"{op['operation_code']:10} {setup:>4.0f}m + {run:>4.0f}m = {setup+run:>5.0f}m | ${cost:>6.2f}")
print("=" * 55)
print(f"{'Calculated Total':>37} | ${total:>6.2f}")
print(f"{'Stored total_cost':>37} | ${float(d['total_cost']):>6.2f}")
