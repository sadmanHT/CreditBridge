"""
Backend Verification Script - Human-in-the-Loop Compliance
Checks audit_logs and credit_decisions tables after manual override
"""

import os
import sys
from datetime import datetime, timedelta
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_KEY")

if not supabase_url or not supabase_key:
    print("❌ ERROR: SUPABASE_URL or SUPABASE_SERVICE_KEY not found in environment")
    sys.exit(1)

supabase: Client = create_client(supabase_url, supabase_key)

print("=" * 80)
print("🔍 HUMAN-IN-THE-LOOP COMPLIANCE VERIFICATION")
print("=" * 80)
print()

# 1. Check audit_logs table for recent override actions
print("📋 1. AUDIT LOGS - Recent Decision Overrides")
print("-" * 80)

try:
    # Query recent audit logs with DECISION_OVERRIDE action
    audit_response = supabase.table('audit_log') \
        .select('*') \
        .eq('action', 'DECISION_OVERRIDE') \
        .order('created_at', desc=True) \
        .limit(5) \
        .execute()
    
    if audit_response.data and len(audit_response.data) > 0:
        print(f"✅ Found {len(audit_response.data)} recent override(s)")
        print()
        
        for idx, log in enumerate(audit_response.data, 1):
            print(f"Override #{idx}:")
            print(f"  • Audit ID: {log.get('id')}")
            print(f"  • Decision ID: {log.get('decision_id')}")
            print(f"  • Officer ID: {log.get('officer_id', 'N/A')}")
            print(f"  • User ID: {log.get('user_id', 'N/A')}")
            print(f"  • Action: {log.get('action')}")
            print(f"  • Timestamp: {log.get('created_at')}")
            
            # Extract override details from metadata
            metadata = log.get('metadata', {})
            if metadata:
                print(f"  • Override Action: {metadata.get('override_action', 'N/A')}")
                print(f"  • Justification: {metadata.get('justification', 'N/A')}")
                print(f"  • Previous Decision: {metadata.get('previous_decision', 'N/A')}")
            print()
    else:
        print("⚠️  No override actions found in audit_log")
        print("   (This is expected if no overrides have been performed yet)")
    
except Exception as e:
    print(f"❌ Error querying audit_log: {str(e)}")

print()

# 2. Check credit_decisions table for updated statuses
print("📊 2. CREDIT DECISIONS - Status Updates")
print("-" * 80)

try:
    # Get recent credit decisions with manual overrides
    # Looking for decisions where decision != original AI decision or has override metadata
    decisions_response = supabase.table('credit_decisions') \
        .select('*') \
        .order('updated_at', desc=True) \
        .limit(10) \
        .execute()
    
    if decisions_response.data and len(decisions_response.data) > 0:
        print(f"✅ Found {len(decisions_response.data)} recent decision(s)")
        print()
        
        override_count = 0
        for decision in decisions_response.data:
            # Check if decision has override indicators
            metadata = decision.get('metadata', {})
            has_override = metadata.get('is_override', False) or metadata.get('override_action')
            
            if has_override:
                override_count += 1
                print(f"Decision ID: {decision.get('id')}")
                print(f"  • Loan Request ID: {decision.get('loan_request_id')}")
                print(f"  • Current Status: {decision.get('decision', 'N/A')}")
                print(f"  • Credit Score: {decision.get('credit_score', 'N/A')}")
                print(f"  • Created: {decision.get('created_at')}")
                print(f"  • Updated: {decision.get('updated_at')}")
                
                if metadata:
                    print(f"  • Override Action: {metadata.get('override_action', 'N/A')}")
                    print(f"  • Override Reason: {metadata.get('override_reason', 'N/A')}")
                    print(f"  • Override Timestamp: {metadata.get('override_timestamp', 'N/A')}")
                    print(f"  • Overridden By: {metadata.get('overridden_by', 'N/A')}")
                print()
        
        if override_count == 0:
            print("⚠️  No decisions with override metadata found")
            print("   (This is expected if no overrides have been performed yet)")
        else:
            print(f"✅ Total decisions with overrides: {override_count}")
    else:
        print("⚠️  No credit decisions found")
    
except Exception as e:
    print(f"❌ Error querying credit_decisions: {str(e)}")

print()

# 3. Verify Override Reason Logging
print("📝 3. OVERRIDE REASON VERIFICATION")
print("-" * 80)

try:
    # Get most recent override from audit_log
    recent_override = supabase.table('audit_log') \
        .select('*') \
        .eq('action', 'DECISION_OVERRIDE') \
        .order('created_at', desc=True) \
        .limit(1) \
        .execute()
    
    if recent_override.data and len(recent_override.data) > 0:
        override = recent_override.data[0]
        metadata = override.get('metadata', {})
        
        justification = metadata.get('justification', '')
        override_action = metadata.get('override_action', '')
        previous_decision = metadata.get('previous_decision', '')
        
        print("✅ Most Recent Override Details:")
        print(f"  • Decision ID: {override.get('decision_id')}")
        print(f"  • Override Action: {override_action}")
        print(f"  • Previous Decision: {previous_decision}")
        print(f"  • Justification Length: {len(justification)} characters")
        print(f"  • Justification: \"{justification}\"")
        print(f"  • Logged By: {override.get('officer_id', override.get('user_id', 'Unknown'))}")
        print(f"  • Timestamp: {override.get('created_at')}")
        
        # Compliance checks
        print()
        print("🔐 COMPLIANCE CHECKS:")
        compliance_passed = True
        
        if justification and len(justification.strip()) > 0:
            print("  ✅ Override reason logged")
        else:
            print("  ❌ Override reason missing or empty")
            compliance_passed = False
        
        if override_action in ['APPROVE', 'REJECT', 'ESCALATE']:
            print("  ✅ Valid override action recorded")
        else:
            print("  ❌ Invalid or missing override action")
            compliance_passed = False
        
        if override.get('created_at'):
            print("  ✅ Audit timestamp recorded")
        else:
            print("  ❌ Audit timestamp missing")
            compliance_passed = False
        
        if override.get('decision_id'):
            print("  ✅ Decision ID tracked")
        else:
            print("  ❌ Decision ID missing")
            compliance_passed = False
        
        print()
        if compliance_passed:
            print("🎉 COMPLIANCE VERIFICATION: PASSED")
            print("   All required audit trail elements are present")
        else:
            print("⚠️  COMPLIANCE VERIFICATION: ISSUES FOUND")
            print("   Some required audit trail elements are missing")
    else:
        print("⚠️  No override actions found to verify")
        print("   Please perform a manual override first:")
        print("   1. Navigate to Officer Dashboard")
        print("   2. Click on a REVIEW decision")
        print("   3. Use the Override Panel to approve/reject")
        print("   4. Re-run this verification script")

except Exception as e:
    print(f"❌ Error verifying override reason: {str(e)}")

print()
print("=" * 80)
print("✅ VERIFICATION COMPLETE")
print("=" * 80)
