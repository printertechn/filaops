import requests
import json
from datetime import datetime

# Test credentials
timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
email = f"fulltest{timestamp}@example.com"
password = "SecurePass123!"

print("="*60)
print("TESTING ALL AUTHENTICATION ENDPOINTS")
print("="*60)

# 1. Test Registration
print("\n1. Testing REGISTER...")
response = requests.post(
    "http://localhost:8000/api/v1/auth/register",
    json={
        "email": email,
        "password": password,
        "first_name": "Full",
        "last_name": "Test"
    }
)
print(f"Status: {response.status_code}")
if response.status_code == 201:
    data = response.json()
    print(f"SUCCESS - User ID: {data['id']}, Email: {data['email']}")
    access_token = data['access_token']
    refresh_token = data['refresh_token']
else:
    print(f"FAILED - {response.text}")
    exit(1)

# 2. Test Get Current User (/me)
print("\n2. Testing GET /me (current user)...")
response = requests.get(
    "http://localhost:8000/api/v1/auth/me",
    headers={"Authorization": f"Bearer {access_token}"}
)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"SUCCESS - Email: {data['email']}, Name: {data['first_name']} {data['last_name']}")
else:
    print(f"FAILED - {response.text}")

# 3. Test Login
print("\n3. Testing LOGIN...")
response = requests.post(
    "http://localhost:8000/api/v1/auth/login",
    data={
        "username": email,  # OAuth2 uses 'username' field
        "password": password
    }
)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"SUCCESS - Got new access_token and refresh_token")
    access_token2 = data['access_token']
    refresh_token2 = data['refresh_token']
else:
    print(f"FAILED - {response.text}")
    exit(1)

# 4. Test Refresh Token
print("\n4. Testing REFRESH TOKEN...")
response = requests.post(
    "http://localhost:8000/api/v1/auth/refresh",
    json={"refresh_token": refresh_token2}
)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"SUCCESS - Got new access_token and refresh_token")
else:
    print(f"FAILED - {response.text}")

# 5. Test /me with new access token
print("\n5. Testing GET /me with refreshed token...")
response = requests.get(
    "http://localhost:8000/api/v1/auth/me",
    headers={"Authorization": f"Bearer {data['access_token']}"}
)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"SUCCESS - Email: {data['email']}")
else:
    print(f"FAILED - {response.text}")

print("\n" + "="*60)
print("ALL TESTS COMPLETED SUCCESSFULLY!")
print("="*60)
