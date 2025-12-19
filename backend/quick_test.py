import requests

for i in range(5):
    r = requests.post('http://localhost:8000/api/v1/test/ping')
    print(f'{i+1}: Status={r.status_code}, Limit={r.headers.get("X-RateLimit-Limit")}, Remaining={r.headers.get("X-RateLimit-Remaining")}')
