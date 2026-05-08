import requests

base_url = 'http://127.0.0.1:5000'

# Test 1: Access /register without login (should redirect to /)
response = requests.get(f'{base_url}/register', allow_redirects=False)
print(f"Test 1 - Non-logged-in access: Status {response.status_code}, Location: {response.headers.get('Location', 'None')}")

# Test 2: Login as IT Admin (assuming username 'admin', password 'admin123' from setup_db)
s = requests.Session()
login_data = {'username': 'admin', 'password': 'admin123'}
login_response = s.post(f'{base_url}/login', json=login_data)
print(f"Login response: {login_response.json()}")

# Test 3: Access /register as IT Admin
reg_response = s.get(f'{base_url}/register', allow_redirects=False)
print(f"Test 3 - IT Admin access: Status {reg_response.status_code}")

# Test 4: Login as Staff (assuming username 'staff1', password 'staff123')
s2 = requests.Session()
login_data2 = {'username': 'staff1', 'password': 'staff123'}
login_response2 = s2.post(f'{base_url}/login', json=login_data2)
print(f"Staff login response: {login_response2.json()}")

# Test 5: Access /register as Staff (should redirect)
reg_response2 = s2.get(f'{base_url}/register', allow_redirects=False)
print(f"Test 5 - Staff access: Status {reg_response2.status_code}, Location: {reg_response2.headers.get('Location', 'None')}")
