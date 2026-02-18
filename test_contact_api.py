import http.client
import json

def test_contact_api():
    conn = http.client.HTTPConnection("localhost", 8000)
    data = {
        "name": "Test User",
        "email": "test@example.com",
        "subject": "Hello Amz AI",
        "message": "This is a test message from the automated verification script."
    }
    headers = {'Content-Type': 'application/json'}
    
    print("Testing /api/contact POST...")
    try:
        conn.request("POST", "/api/contact", json.dumps(data), headers)
        response = conn.getresponse()
        print(f"Status: {response.status}")
        print(f"Body: {response.read().decode()}")
    except Exception as e:
        print(f"Error: {e}. Is the server running?")

if __name__ == "__main__":
    test_contact_api()
