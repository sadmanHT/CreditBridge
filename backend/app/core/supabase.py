"""
Supabase Client Configuration for CreditBridge

This module initializes a Supabase client using environment variables.
It will be used for:
- Authentication
- Secure database access
- Audit and compliance logging
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables from .env file
load_dotenv()

# Get Supabase credentials from environment
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Validate that required environment variables are present
if not SUPABASE_URL:
    raise ValueError(
        "SUPABASE_URL environment variable is missing. "
        "Please check your .env file in the backend/ directory."
    )

if not SUPABASE_ANON_KEY:
    raise ValueError(
        "SUPABASE_ANON_KEY environment variable is missing. "
        "Please check your .env file in the backend/ directory."
    )

# Initialize Supabase client (default uses anon key)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# Initialize service role client for testing/admin operations (bypasses RLS)
supabase_admin: Client = None
if SUPABASE_SERVICE_ROLE_KEY:
    supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
