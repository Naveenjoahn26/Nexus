import urllib.request
import urllib.error
import urllib.parse
import json
import uuid

BASE_URL = "http://localhost:8000/api/v1"
EMAIL = f"test_all_{uuid.uuid4().hex[:8]}@example.com"
PASSWORD = "password123"

def req(url, method='GET', data=None, headers=None):
    if headers is None: headers = {}
    if 'Content-Type' not in headers and data is not None:
        headers['Content-Type'] = 'application/json'
    encoded_data = None
    if data:
        if headers.get('Content-Type') == 'application/x-www-form-urlencoded':
            encoded_data = urllib.parse.urlencode(data).encode()
        else:
            encoded_data = json.dumps(data).encode()
    request_obj = urllib.request.Request(url, method=method, headers=headers)
    if encoded_data: request_obj.data = encoded_data
    try:
        with urllib.request.urlopen(request_obj) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())

print(f"Registering user: {EMAIL}")
status, res = req(f"{BASE_URL}/auth/register", method='POST', data={"email": EMAIL, "password": PASSWORD, "full_name": "Test User"})
if status != 200: print(res); exit(1)

print("Logging in...")
status, res = req(f"{BASE_URL}/auth/login", method='POST', headers={'Content-Type': 'application/x-www-form-urlencoded'}, data={"username": EMAIL, "password": PASSWORD, "grant_type": "password"})
token = res['access_token']
headers = {'Authorization': f'Bearer {token}'}

print("Creating course...")
status, res = req(f"{BASE_URL}/courses", method='POST', headers=headers, data={
    "name": "Advanced Biology", "code": "BIO401", "description": "Genetics", "subject_area": "Biology", "academic_level": "Undergraduate"
})
course_id = res['data']['id']
headers_with_ws = {**headers, 'X-Workspace-ID': course_id}

print("Testing Lecture Generation...")
status, res = req(f"{BASE_URL}/generate/lecture", method='POST', headers=headers_with_ws, data={"topic": "DNA Replication", "additional_instructions": "Keep it brief"})
print(f"Lecture Status: {status}")

print("Testing Summary Generation...")
status, res = req(f"{BASE_URL}/generate/summary", method='POST', headers=headers_with_ws, data={"topic": "Genetics", "additional_instructions": ""})
print(f"Summary Status: {status}")

print("Testing Question Paper Generation...")
status, res = req(f"{BASE_URL}/generate/question-paper", method='POST', headers=headers_with_ws, data={"topic": "Genetics", "additional_instructions": ""})
print(f"Question Paper Status: {status}")

print("Testing Presentation Generation...")
status, res = req(f"{BASE_URL}/generate/presentation", method='POST', headers=headers_with_ws, data={"topic": "Genetics", "additional_instructions": ""})
print(f"Presentation Status: {status}")

print("All generation endpoints tested!")
