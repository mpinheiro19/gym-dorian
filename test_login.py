"""Script to test login endpoint"""
import requests
from urllib.parse import urlencode

def test_login():
    """Test login endpoint"""
    base_url = "http://localhost:8000"

    # Test users to try
    test_credentials = [
        {"email": "test@example.com", "password": "test123"},
        {"email": "admin@gym.com", "password": "admin123"},
        {"email": "testuser@example.com", "password": "password123"},
    ]

    print("🔐 Testing Login Endpoint\n")
    print(f"Backend URL: {base_url}")
    print("=" * 60)

    # Test ping first
    try:
        print("\n1️⃣ Testing /ping endpoint...")
        response = requests.get(f"{base_url}/ping", timeout=5)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        print("\n⚠️  Backend is not running or not accessible!")
        return

    # Test login endpoint
    for creds in test_credentials:
        print(f"\n2️⃣ Testing login with {creds['email']}...")

        try:
            # OAuth2 expects form-encoded data
            data = {
                "username": creds["email"],  # OAuth2 uses 'username' field
                "password": creds["password"]
            }

            response = requests.post(
                f"{base_url}/api/auth/login",
                data=data,  # form-encoded, not JSON
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=5
            )

            print(f"   Status: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ SUCCESS!")
                print(f"   Token: {result.get('access_token', 'N/A')[:50]}...")
                print(f"   Token Type: {result.get('token_type', 'N/A')}")

                # Test token validity
                token = result.get('access_token')
                if token:
                    print(f"\n3️⃣ Testing token with /api/users/me...")
                    me_response = requests.get(
                        f"{base_url}/api/users/me",
                        headers={"Authorization": f"Bearer {token}"},
                        timeout=5
                    )
                    print(f"   Status: {me_response.status_code}")
                    if me_response.status_code == 200:
                        user_data = me_response.json()
                        print(f"   ✅ Token valid!")
                        print(f"   User: {user_data.get('email')}")
                        print(f"   Full Name: {user_data.get('full_name')}")
                    else:
                        print(f"   ❌ Token invalid")
                        print(f"   Response: {me_response.text}")

                return  # Success, stop testing
            else:
                print(f"   ❌ FAILED")
                print(f"   Response: {response.text}")

        except Exception as e:
            print(f"   ❌ Error: {e}")

    print("\n" + "=" * 60)
    print("❌ All login attempts failed!")
    print("\n💡 Possible issues:")
    print("   1. Wrong password")
    print("   2. Backend not running")
    print("   3. CORS configuration issue")
    print("   4. Database connection issue")

if __name__ == "__main__":
    test_login()
