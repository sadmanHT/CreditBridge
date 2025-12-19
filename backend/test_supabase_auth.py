"""Test Supabase authentication directly"""
import os
import time
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# Initialize client
client = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_ANON_KEY')
)

print("="*60)
print("SUPABASE AUTHENTICATION TEST")
print("="*60)

# Test 1: Try signup with different email formats
test_emails = [
    f"user{int(time.time())}@example.com",
    f"test{int(time.time())}@gmail.com",
    f"borrower{int(time.time())}@test.org",
]

for email in test_emails:
    print(f"\n📧 Testing signup with: {email}")
    try:
        response = client.auth.sign_up({
            "email": email,
            "password": "TestPassword123!"
        })
        
        if response.user:
            print(f"✅ SUCCESS! User created: {response.user.id}")
            print(f"   Email: {response.user.email}")
            print(f"   Email confirmed: {response.user.email_confirmed_at}")
            break
        else:
            print(f"❌ Failed: No user returned")
            print(f"   Response: {response}")
            
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}")
        print(f"   Message: {str(e)}")

# Test 2: Check auth settings
print("\n" + "="*60)
print("SUPABASE PROJECT SETTINGS")
print("="*60)
print(f"URL: {os.getenv('SUPABASE_URL')}")
print(f"Key type: Anonymous key")
print("\n⚠️  Common issues:")
print("1. Email confirmation required (check Supabase dashboard > Authentication > Email Auth)")
print("2. Disposable email blocking enabled")
print("3. Email rate limiting")
print("4. Custom email validation rules")
print("\n💡 Solution: Go to your Supabase dashboard:")
print("   https://app.supabase.com/project/uzrnffsloaamwqfhwzyj/auth/users")
print("   Check Authentication > Providers > Email settings")
