# Manual Testing Guide

**Quick verification of rate limiting and idempotency**

## Prerequisites

```bash
# Terminal 1: Start the server
cd backend
uvicorn app.main:app --reload

# Terminal 2: Run tests
cd backend
python test_integration.py
```

## Automated Tests (RECOMMENDED)

```bash
# Run all integration tests automatically
python test_integration.py
```

This will test:
- ✅ Rate limiting (60+ requests → 429)
- ✅ Idempotency (same key → same response)
- ✅ Normal flow (no key → works normally)

## Manual Tests with curl

### Test A: Rate Limiting

```bash
# Bash/Linux/Mac: Make 65 requests rapidly
for i in {1..65}; do
  echo "Request $i:"
  curl -s -o /dev/null -w "Status: %{http_code}\n" \
    -X POST http://localhost:8000/api/v1/loans/request \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer test-token" \
    -d '{"requested_amount": 10000, "purpose": "test"}'
done

# Expected:
# Requests 1-60: Status: 200
# Requests 61+:  Status: 429
```

```powershell
# PowerShell/Windows
for ($i=1; $i -le 65; $i++) {
  Write-Host "Request $i:"
  $response = Invoke-WebRequest `
    -Uri "http://localhost:8000/api/v1/loans/request" `
    -Method POST `
    -Headers @{
      "Content-Type"="application/json"
      "Authorization"="Bearer test-token"
    } `
    -Body '{"requested_amount": 10000, "purpose": "test"}' `
    -UseBasicParsing -ErrorAction SilentlyContinue
  Write-Host "Status: $($response.StatusCode)"
}
```

### Test B: Idempotency

```bash
# First request with idempotency key
curl -i -X POST http://localhost:8000/api/v1/loans/request \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-token" \
  -H "Idempotency-Key: test-123" \
  -d '{"requested_amount": 10000, "purpose": "test"}'

# Expected:
# Status: 200 OK
# Idempotent-Replayed: (not present)

# Second request (SAME KEY, SAME BODY)
curl -i -X POST http://localhost:8000/api/v1/loans/request \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-token" \
  -H "Idempotency-Key: test-123" \
  -d '{"requested_amount": 10000, "purpose": "test"}'

# Expected:
# Status: 200 OK
# Idempotent-Replayed: true  ← Cached response!
# Response body identical to first request
```

### Test C: Normal Flow

```bash
# Request without idempotency key
curl -i -X POST http://localhost:8000/api/v1/loans/request \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-token" \
  -d '{"requested_amount": 10000, "purpose": "test"}'

# Expected:
# Status: 200 OK
# No Idempotent-Replayed header
# Creates new loan request each time
```

## Verification Checklist

### ✅ Rate Limiting Working

- [ ] First 60 requests return 200 OK
- [ ] 61st request returns 429 Too Many Requests
- [ ] Response includes `Retry-After` header
- [ ] Response includes `X-RateLimit-*` headers:
  ```
  X-RateLimit-Limit: 60
  X-RateLimit-Remaining: 0
  X-RateLimit-Reset: <timestamp>
  ```

### ✅ Idempotency Working

- [ ] First request processes normally (200 OK)
- [ ] Second request with same key returns 200 OK
- [ ] Second request has `Idempotent-Replayed: true` header
- [ ] Response bodies are identical
- [ ] No duplicate loan created (check loan IDs match)

### ✅ Normal Flow Working

- [ ] Requests without idempotency key work normally
- [ ] Each request creates new loan
- [ ] No caching applied

## Quick Python Test

```python
import requests
import uuid

# Test idempotency
key = str(uuid.uuid4())

# Request 1
r1 = requests.post('http://localhost:8000/api/v1/loans/request',
    headers={'Idempotency-Key': key, 'Authorization': 'Bearer test'},
    json={'requested_amount': 10000, 'purpose': 'test'})

print(f"Request 1: {r1.status_code}")
print(f"Replayed: {r1.headers.get('Idempotent-Replayed', 'N/A')}")

# Request 2 (same key)
r2 = requests.post('http://localhost:8000/api/v1/loans/request',
    headers={'Idempotency-Key': key, 'Authorization': 'Bearer test'},
    json={'requested_amount': 10000, 'purpose': 'test'})

print(f"Request 2: {r2.status_code}")
print(f"Replayed: {r2.headers.get('Idempotent-Replayed', 'N/A')}")

# Verify
assert r1.status_code == 200
assert r2.status_code == 200
assert r2.headers.get('Idempotent-Replayed') == 'true'
print("✅ Idempotency working!")
```

## Troubleshooting

### Server not starting

```bash
# Check if port 8000 is in use
netstat -ano | findstr :8000  # Windows
lsof -i :8000                 # Mac/Linux

# Try different port
uvicorn app.main:app --reload --port 8001
```

### Rate limiting not working

Check middleware is registered in `app/main.py`:

```python
app.add_middleware(IdempotencyMiddleware)
app.add_middleware(RateLimitHeaderMiddleware)
```

### Idempotency not working

1. Check middleware registration
2. Verify endpoint in PROTECTED_PATHS:
   ```python
   PROTECTED_PATHS = ["/api/v1/loans/request"]
   ```
3. Check server logs for idempotency messages

### Authentication errors

Update TEST_USER_TOKEN in test_integration.py or use:
```bash
curl ... -H "Authorization: Bearer your-actual-token"
```

## Expected Output

### Rate Limiting Test
```
TEST A: RATE LIMITING
Request 1:  ✅ 200 OK (Remaining: 59)
Request 2:  ✅ 200 OK (Remaining: 58)
...
Request 60: ✅ 200 OK (Remaining: 0)
Request 61: 🛑 429 RATE LIMITED (Retry-After: 5s)
Request 62: 🛑 429 RATE LIMITED (Retry-After: 5s)

🎉 TEST A PASSED: Rate limiting working correctly!
```

### Idempotency Test
```
TEST B: IDEMPOTENCY
REQUEST 1: First submission
   Status: 200
   Idempotent-Replayed: false
   Loan Request ID: abc-123

REQUEST 2: Retry with same key
   Status: 200
   Idempotent-Replayed: true  ← Cached!
   Loan Request ID: abc-123   ← Same ID!

🎉 TEST B PASSED: Idempotency working correctly!
```

### Normal Flow Test
```
TEST C: NORMAL FLOW
REQUEST 1: No Idempotency-Key header
   Loan Request ID: loan-1

REQUEST 2: No Idempotency-Key header
   Loan Request ID: loan-2  ← Different ID

REQUEST 3: No Idempotency-Key header
   Loan Request ID: loan-3  ← Different ID

🎉 TEST C PASSED: Normal flow working correctly!
```

## Success Criteria

✅ **All tests pass**
- Rate limiting blocks after 60 requests
- Idempotency prevents duplicates with same key
- Normal flow works without idempotency key

✅ **Performance acceptable**
- Request latency < 250ms
- Rate check overhead < 0.1ms
- Memory usage < 10MB additional

✅ **Headers present**
- X-RateLimit-Limit
- X-RateLimit-Remaining
- X-RateLimit-Reset
- Idempotent-Replayed (when applicable)
- Retry-After (on 429)

---

**Ready to test?**
```bash
cd backend
python test_integration.py
```
