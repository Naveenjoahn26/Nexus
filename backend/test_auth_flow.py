"""
Test the complete registration and login flow.
"""
import urllib.request
import urllib.error
import urllib.parse
import json
import uuid
import time

BASE_URL = "http://localhost:8000/api/v1"
EMAIL = f"testuser_{uuid.uuid4().hex[:8]}@example.com"
PASSWORD = "SecurePassword123"

def req(url, method='GET', data=None, headers=None):
    """Make an HTTP request and return status and response."""
    if headers is None:
        headers = {}
    if 'Content-Type' not in headers and data is not None:
        headers['Content-Type'] = 'application/json'
    
    encoded_data = None
    if data:
        if headers.get('Content-Type') == 'application/x-www-form-urlencoded':
            encoded_data = urllib.parse.urlencode(data).encode()
        else:
            encoded_data = json.dumps(data).encode()
            
    request_obj = urllib.request.Request(url, method=method, headers=headers)
    if encoded_data:
        request_obj.data = encoded_data
        
    try:
        with urllib.request.urlopen(request_obj) as r:
            response_data = r.read()
            return r.status, json.loads(response_data) if response_data else {}
    except urllib.error.HTTPError as e:
        error_data = e.read()
        return e.code, json.loads(error_data) if error_data else {"error": str(e)}
    except Exception as e:
        return 500, {"error": str(e)}

print("=" * 60)
print("TEST: User Registration and Login Flow")
print("=" * 60)

# Test 1: Register
print(f"\n[1] Registering user with email: {EMAIL}")
status, res = req(f"{BASE_URL}/auth/register", method='POST', data={
    "email": EMAIL,
    "password": PASSWORD,
    "full_name": "Test User"
})
print(f"    Status: {status}")
if status != 200:
    print(f"    ERROR: {res}")
    exit(1)
print(f"    ✓ User registered successfully")
print(f"    Response: {json.dumps(res, indent=2, default=str)}")

# Small delay to ensure DB is committed
time.sleep(0.5)

# Test 2: Login
print(f"\n[2] Logging in with email: {EMAIL}")
status, res = req(f"{BASE_URL}/auth/login", method='POST', 
    headers={'Content-Type': 'application/x-www-form-urlencoded'}, 
    data={
        "username": EMAIL,
        "password": PASSWORD,
        "grant_type": "password"
    }
)
print(f"    Status: {status}")
if status != 200:
    print(f"    ERROR: {res}")
    exit(1)

token = res.get('access_token')
if not token:
    print(f"    ERROR: No access_token in response")
    print(f"    Response: {res}")
    exit(1)

print(f"    ✓ Login successful")
print(f"    Token: {token[:50]}...")

# Test 3: Get user profile
print(f"\n[3] Getting user profile with token")
status, res = req(f"{BASE_URL}/auth/me", method='GET', 
    headers={'Authorization': f'Bearer {token}'}
)
print(f"    Status: {status}")
if status != 200:
    print(f"    ERROR: {res}")
    exit(1)

user = res.get('data') if res.get('success') else res
print(f"    ✓ User profile retrieved")
print(f"    User Email: {user.get('email')}")
print(f"    User Name: {user.get('full_name')}")

# Test 4: Try uppercase email login
print(f"\n[4] Testing case-insensitive login with uppercase email")
uppercase_email = EMAIL.upper()
status, res = req(f"{BASE_URL}/auth/login", method='POST', 
    headers={'Content-Type': 'application/x-www-form-urlencoded'}, 
    data={
        "username": uppercase_email,
        "password": PASSWORD,
        "grant_type": "password"
    }
)
print(f"    Status: {status}")
if status != 200:
    print(f"    ERROR: Case-insensitive login failed: {res}")
    exit(1)

token2 = res.get('access_token')
if not token2:
    print(f"    ERROR: No access_token in response")
    exit(1)

print(f"    ✓ Case-insensitive login successful")

# Test 5: Try duplicate registration
print(f"\n[5] Testing duplicate email registration")
status, res = req(f"{BASE_URL}/auth/register", method='POST', data={
    "email": EMAIL,  # Same email
    "password": PASSWORD,
    "full_name": "Another User"
})
print(f"    Status: {status}")
if status == 200:
    print(f"    ERROR: Duplicate registration should have failed!")
    exit(1)
print(f"    ✓ Duplicate registration correctly rejected")

print("\n" + "=" * 60)
print("ALL TESTS PASSED!")
print("=" * 60)
