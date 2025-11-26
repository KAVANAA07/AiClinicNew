"""
Test IVR endpoint locally
Run: python test_ivr.py
"""
import requests

# Test the IVR welcome endpoint
ngrok_url = "https://6fe50d311dd7.ngrok-free.app"  # Update with your current ngrok URL
ivr_url = f"{ngrok_url}/api/ivr/welcome/"

print("Testing IVR endpoint...")
print(f"URL: {ivr_url}")
print("-" * 60)

try:
    # Simulate Twilio POST request
    response = requests.post(ivr_url, data={
        'From': '+1234567890',
        'To': '+12154340068',
        'CallSid': 'TEST123456',
    })
    
    print(f"Status Code: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type')}")
    print("\nResponse:")
    print(response.text)
    
    if response.status_code == 200:
        print("\n✓ IVR endpoint is working!")
    else:
        print("\n✗ IVR endpoint returned an error")
        
except Exception as e:
    print(f"\n✗ Error: {e}")
    print("\nMake sure:")
    print("1. Django server is running: python manage.py runserver")
    print("2. ngrok is running: ngrok http 8000")
    print("3. Update the ngrok_url in this script")
