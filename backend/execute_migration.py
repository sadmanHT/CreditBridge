"""
Execute SQL migration to create raw_events table
"""

import os
from supabase import create_client, Client

print("="*70)
print("[MIGRATION EXECUTOR] Creating raw_events table")
print("="*70)

# Get Supabase credentials
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")  # Need service key for schema changes

if not SUPABASE_URL or not SUPABASE_KEY:
    print("\n✗ Missing Supabase credentials")
    print("  Required environment variables:")
    print("    - SUPABASE_URL")
    print("    - SUPABASE_SERVICE_KEY")
    print("\n  Please set these and run again, or execute the SQL manually.")
    exit(1)

# Read the SQL migration file
with open("migrations/create_raw_events_table.sql", "r") as f:
    sql = f.read()

print("\n✓ Loaded SQL migration")
print(f"  File: migrations/create_raw_events_table.sql")
print(f"  Size: {len(sql)} characters")

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Execute SQL via RPC
    print("\n⚠️  Note: Supabase Python client doesn't support direct SQL execution")
    print("  Please use one of these methods:")
    print("\n  METHOD 1: Supabase Dashboard")
    print("    1. Go to: https://supabase.com/dashboard/project/<project-id>/sql")
    print("    2. Click 'New Query'")
    print("    3. Paste the SQL from migrations/create_raw_events_table.sql")
    print("    4. Click 'Run'")
    
    print("\n  METHOD 2: psql CLI")
    print("    psql postgresql://postgres:[password]@[host]:5432/postgres < migrations/create_raw_events_table.sql")
    
    print("\n  METHOD 3: Use Supabase CLI")
    print("    supabase db push --db-url postgresql://...")
    
except Exception as e:
    print(f"\n✗ Error: {str(e)}")

print("\n" + "="*70)
