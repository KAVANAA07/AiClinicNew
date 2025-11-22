import json
import urllib.request

url = 'http://127.0.0.1:8000/api/login/'
data = json.dumps({'username': 'testuser_ci', 'password': 'TestPass123!'})
req = urllib.request.Request(url, data=data.encode('utf-8'), headers={'Content-Type': 'application/json'})
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        print('STATUS', resp.status)
        print(resp.read().decode('utf-8'))
except Exception as e:
    try:
        import sys
        print('ERROR', e)
        if hasattr(e, 'read'):
            print(e.read().decode())
    except Exception:
        print('ERROR', e)
