"""
SQLBot Dimension Value Management Test Script
"""
import requests
import json

BASE_URL = "http://localhost:8000"

HEADERS = {
    "Content-Type": "application/json"
}

def test_dimension_api():
    print("=" * 50)
    print("SQLBot Dimension Value API Test")
    print("=" * 50)
    print()

    # Test 1: Get all dimensions
    print("Test 1: Get all dimensions")
    print("-" * 30)
    try:
        response = requests.get(
            f"{BASE_URL}/api/dimension/all",
            headers=HEADERS,
            params={"enabled_only": True}
        )
        if response.status_code == 200:
            data = response.json()
            print(f"[OK] Status: {response.status_code}")
            print(f"Result: {json.dumps(data, ensure_ascii=False, indent=2)}")
        elif response.status_code == 401:
            print(f"[AUTH] Authentication required (401)")
        else:
            print(f"[ERROR] Status: {response.status_code}")
            print(f"Response: {response.text[:200]}")
    except Exception as e:
        print(f"[ERROR] {e}")

    print()

    # Test 2: Paginated list
    print("Test 2: Paginated list")
    print("-" * 30)
    try:
        response = requests.get(
            f"{BASE_URL}/api/dimension/list",
            headers=HEADERS,
            params={"page": 1, "page_size": 10}
        )
        if response.status_code == 200:
            data = response.json()
            print(f"[OK] Status: {response.status_code}")
            print(f"Total: {data.get('total_count', 0)}")
            print(f"Current page: {data.get('current_page', 0)}")
        else:
            print(f"[ERROR] Status: {response.status_code}")
    except Exception as e:
        print(f"[ERROR] {e}")

    print()
    print("=" * 50)
    print("Test completed")
    print("=" * 50)
    print()
    print("Access URLs:")
    print("  Frontend: http://localhost:5173")
    print("  API Docs: http://localhost:8000/docs")
    print("  Dimension Management: http://localhost:5173/#/set/dimension")

if __name__ == "__main__":
    test_dimension_api()
