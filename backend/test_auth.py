import requests
import json
from datetime import datetime

# Test registration with timestamp to ensure unique email
timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
email = f"test{timestamp}@example.com"

print("Testing registration...")
print(f"Email: {email}")

response = requests.post(
    "http://localhost:8000/api/v1/auth/register",
    json={
        "email": email,
        "password": "SecurePass123!",
        "first_name": "Test",
        "last_name": "User"
    }
)

print(f"\nStatus Code: {response.status_code}")
if response.status_code == 201:
    data = response.json()
    print("\nSUCCESS: Registration successful!")
    print(f"User ID: {data['id']}")
    print(f"Email: {data['email']}")
    print(f"Access Token: {data['access_token'][:50]}...")
    print(f"Refresh Token: {data['refresh_token'][:50]}...")
    print(f"Token Type: {data['token_type']}")
else:
    print("\nFAILED: Registration failed")
    try:
        print(json.dumps(response.json(), indent=2))
    except:
        print(response.text)
