"""
Simple test script for the Face Recognition API
This script demonstrates how to use the API endpoints
"""
import requests
import json


# API base URL
BASE_URL = "http://localhost:8003"


def test_health():
    """Test health check endpoint"""
    print("\n=== Testing Health Check ===")
    response = requests.get(f"{BASE_URL}/api/health")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200


def test_register_user(user_id, name, image_path):
    """Test user registration"""
    print(f"\n=== Registering User: {user_id} ===")
    
    with open(image_path, 'rb') as image_file:
        files = {'file': image_file}
        data = {
            'user_id': user_id,
            'name': name
        }
        
        response = requests.post(f"{BASE_URL}/api/register", files=files, data=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        return response.status_code == 200


def test_recognize_user(image_path):
    """Test user recognition"""
    print(f"\n=== Recognizing User ===")
    
    with open(image_path, 'rb') as image_file:
        files = {'file': image_file}
        
        response = requests.post(f"{BASE_URL}/api/recognize", files=files)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        return response.json()


def test_get_users():
    """Test get all users"""
    print("\n=== Getting All Users ===")
    response = requests.get(f"{BASE_URL}/api/users")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.json()


def test_get_user(user_id):
    """Test get specific user"""
    print(f"\n=== Getting User: {user_id} ===")
    response = requests.get(f"{BASE_URL}/api/users/{user_id}")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200


def test_delete_user(user_id):
    """Test delete user"""
    print(f"\n=== Deleting User: {user_id} ===")
    response = requests.delete(f"{BASE_URL}/api/users/{user_id}")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200


def main():
    """Main test function"""
    print("=" * 60)
    print("Face Recognition System - API Test Script")
    print("=" * 60)
    
    # Test 1: Health check
    if not test_health():
        print("\n❌ Health check failed. Make sure the server is running!")
        return
    
    print("\n✅ Server is running!")
    
    # Test 2: Get all users (should be empty initially)
    test_get_users()
    
    # Note: The following tests require actual image files
    # Uncomment and modify the image paths to test
    
    # Example usage (uncomment to use):
    # test_register_user("user001", "John Doe", "path/to/john_face.jpg")
    # test_get_users()
    # test_get_user("user001")
    # test_recognize_user("path/to/john_face.jpg")
    # test_delete_user("user001")
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)
    print("\nTo test with actual images:")
    print("1. Take or find clear face images")
    print("2. Update the image paths in this script")
    print("3. Uncomment the test functions")
    print("4. Run the script again")


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Cannot connect to the server!")
        print("Make sure the server is running: python main.py")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")

