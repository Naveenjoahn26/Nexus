import urllib.request
import urllib.error
import urllib.parse
import json
import uuid

BASE_URL = "http://localhost:8000/api/v1"
EMAIL = f"test_{uuid.uuid4().hex[:8]}@example.com"
PASSWORD = "password123"

def req(url, method='GET', data=None, headers=None):
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
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())

print(f"Registering user: {EMAIL}")
status, res = req(f"{BASE_URL}/auth/register", method='POST', data={
    "email": EMAIL,
    "password": PASSWORD,
    "full_name": "Test User"
})
print(f"Register Status: {status}")
if status != 200:
    print(res)
    exit(1)

print("Logging in...")
status, res = req(f"{BASE_URL}/auth/login", method='POST', headers={'Content-Type': 'application/x-www-form-urlencoded'}, data={
    "username": EMAIL,
    "password": PASSWORD,
    "grant_type": "password"
})
print(f"Login Status: {status}")
if status != 200:
    print(res)
    exit(1)

token = res['access_token']
headers = {'Authorization': f'Bearer {token}'}

print("Creating course...")
status, res = req(f"{BASE_URL}/courses", method='POST', headers=headers, data={
    "name": "Advanced Physics",
    "code": "PHY401",
    "description": "Quantum Mechanics and Relativity",
    "subject_area": "Physics",
    "academic_level": "Undergraduate"
})
print(f"Create Course Status: {status}")
if status != 200:
    print(res)
    exit(1)

course_id = res['data']['id']
print(f"Created Course ID: {course_id}")

print("Testing Chat...")
status, res = req(f"{BASE_URL}/chat", method='POST', headers={**headers, 'X-Workspace-ID': course_id}, data={
    "message": "Hello, I am testing the chat."
})
print(f"Chat Status: {status}")
if status != 200:
    print(res)
    exit(1)

print(f"Chat Response: {res['data']['content']}")
print("Test completed successfully!")
