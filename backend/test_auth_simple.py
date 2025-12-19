"""
Simple test to verify auth dependency works
"""
import requests

# Test without auth header - should use "anonymous_user"
print("Testing without Authorization header...")
response = requests.post(
    'http://localhost:8000/api/v1/loans/request',
    headers={'Content-Type': 'application/json'},
    json={'requested_amount': 10000, 'purpose': 'test'}
)
print(f"Status: {response.status_code}")
print(f"Response: {response.text[:500]}")

# Test with dummy Bearer token
print("\nTesting with dummy Bearer token...")
response = requests.post(
    'http://localhost:8000/api/v1/loans/request',
    headers={
        'Content-Type': 'application/json',
        'Authorization': 'Bearer dummy-token'
    },
    json={'requested_amount': 10000, 'purpose': 'test'}
)
print(f"Status: {response.status_code}")
print(f"Response: {response.text[:500]}")
