#!/usr/bin/env python
"""
Example of how to use the receptionist confirmation API
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:8000/api"
RECEPTIONIST_TOKEN = "your_receptionist_auth_token_here"

def test_receptionist_confirmation():
    """Test the receptionist confirmation endpoints"""
    
    print("=== Receptionist Token Confirmation API Test ===")
    
    # Method 1: Use the dedicated receptionist confirmation endpoint
    token_id = 123  # Replace with actual token ID
    
    print(f"\n1. Testing receptionist-confirm endpoint for token {token_id}")
    
    response = requests.post(
        f"{BASE_URL}/tokens/{token_id}/receptionist-confirm/",
        headers={
            "Authorization": f"Token {RECEPTIONIST_TOKEN}",
            "Content-Type": "application/json"
        }
    )
    
    if response.status_code == 200:
        print("[SUCCESS] Receptionist confirmation worked!")
        print(f"Response: {response.json()}")
    else:
        print(f"[ERROR] Failed with status {response.status_code}")
        print(f"Error: {response.text}")
    
    # Method 2: Use the general status update endpoint
    print(f"\n2. Testing general status update for token {token_id}")
    
    response = requests.patch(
        f"{BASE_URL}/tokens/{token_id}/",
        headers={
            "Authorization": f"Token {RECEPTIONIST_TOKEN}",
            "Content-Type": "application/json"
        },
        json={"status": "confirmed"}
    )
    
    if response.status_code == 200:
        print("[SUCCESS] Status update worked!")
        print(f"Response: {response.json()}")
    else:
        print(f"[ERROR] Failed with status {response.status_code}")
        print(f"Error: {response.text}")

def show_curl_examples():
    """Show curl command examples"""
    
    print("\n=== CURL Examples ===")
    
    print("\n1. Receptionist Confirmation:")
    print(f"""curl -X POST {BASE_URL}/tokens/123/receptionist-confirm/ \\
  -H "Authorization: Token {RECEPTIONIST_TOKEN}" \\
  -H "Content-Type: application/json"
""")
    
    print("\n2. General Status Update:")
    print(f"""curl -X PATCH {BASE_URL}/tokens/123/ \\
  -H "Authorization: Token {RECEPTIONIST_TOKEN}" \\
  -H "Content-Type: application/json" \\
  -d '{{"status": "confirmed"}}'
""")

if __name__ == "__main__":
    print("This is an example script showing how to use the API.")
    print("Replace RECEPTIONIST_TOKEN with your actual token.")
    print("Replace token_id with the actual token ID you want to confirm.")
    
    show_curl_examples()
    
    # Uncomment to run actual API test:
    # test_receptionist_confirmation()