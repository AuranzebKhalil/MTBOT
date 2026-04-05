import requests

def test_login():
    url = "http://localhost:8000/token"
    data = {
        "username": "Khalil@gmail.com",
        "password": "testpassword" # Assuming a test password for the user in the DB
    }
    # Or test@example.com
    data_test = {
        "username": "test@example.com",
        "password": "testpassword"
    }

    try:
        # FastAPI OAuth2PasswordRequestForm expects form-data (either multipart or urlencoded)
        # requests.post with 'data' kwarg uses application/x-www-form-urlencoded
        response = requests.post(url, data=data_test)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("Login successful!")
            print(f"Token: {response.json().get('access_token')[:10]}...")
        else:
            print(f"Login failed: {response.text}")
    except Exception as e:
        print(f"Request error: {e}")

if __name__ == "__main__":
    test_login()
