import requests

url = "http://localhost:8000/token"
payload = {
    "username": "test3@example.com",
    "password": "testpassword123"
}

try:
    # FastAPI OAuth2 expects form data (x-www-form-urlencoded)
    response = requests.post(url, data=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
