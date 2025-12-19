import requests
import time

print("Testing rate limiting...")
print(f"Making 65 requests rapidly...\n")

success = 0
rate_limited = 0

for i in range(1, 66):
    r = requests.post('http://localhost:8000/api/v1/test/ping')
    limit = r.headers.get("X-RateLimit-Limit", "?")
    remaining = r.headers.get("X-RateLimit-Remaining", "?")
    
    if r.status_code == 200:
        success += 1
        if i <= 3 or i >= 59:
            print(f'Request {i:2d}: 200 OK (Limit={limit}, Remaining={remaining})')
    elif r.status_code == 429:
        rate_limited += 1
        print(f'Request {i:2d}: 429 RATE LIMITED (Remaining={remaining})')
    else:
        print(f'Request {i:2d}: {r.status_code} ERROR')
    
    if i == 10 or i == 20 or i == 30 or i == 40 or i == 50:
        print(f'... {i} requests done, Remaining={remaining}')

print(f"\nResults:")
print(f"  Success: {success}")
print(f"  Rate Limited: {rate_limited}")
print(f"  Expected: ~60 success, ~5 rate limited")
