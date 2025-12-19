#!/usr/bin/env python3
"""
Quick Test Runner for API Gateway Hardening

This script:
1. Checks if server is running
2. Runs integration tests
3. Reports results

Usage:
    python run_tests.py
"""

import subprocess
import sys
import time
import requests
import os

BASE_URL = "http://localhost:8000"


def check_server_running():
    """Check if API server is running."""
    try:
        response = requests.get(f"{BASE_URL}/", timeout=2)
        return response.status_code == 200
    except:
        return False


def start_server():
    """Start the FastAPI server."""
    print("🚀 Starting FastAPI server...")
    print("   Command: uvicorn app.main:app --reload")
    print("\n   (Server will run in background)")
    print("   (Press Ctrl+C to stop tests, server will continue)")
    print()
    
    # Start server in background
    try:
        if sys.platform == "win32":
            # Windows
            process = subprocess.Popen(
                ["python", "-m", "uvicorn", "app.main:app", "--reload"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
        else:
            # Unix/Mac
            process = subprocess.Popen(
                ["uvicorn", "app.main:app", "--reload"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        
        # Wait for server to start
        print("⏳ Waiting for server to start...")
        for i in range(10):
            time.sleep(1)
            if check_server_running():
                print("✅ Server started successfully!\n")
                return process
            print(f"   Attempt {i+1}/10...")
        
        print("❌ Server failed to start in 10 seconds")
        return None
        
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        return None


def main():
    """Main test runner."""
    print("="*80)
    print("API GATEWAY HARDENING - INTEGRATION TESTS")
    print("="*80)
    print()
    
    # Check if we're in the correct directory
    if not os.path.exists("app"):
        print("❌ Error: 'app' directory not found")
        print("   Please run this script from the 'backend' directory:")
        print("   cd backend")
        print("   python run_tests.py")
        return 1
    
    # Check if server is running
    server_process = None
    if check_server_running():
        print("✅ API server is already running")
        print()
    else:
        print("⚠️  API server is not running")
        print()
        
        # Ask user if they want to start it
        response = input("Would you like to start the server now? (y/n): ").strip().lower()
        if response == 'y':
            server_process = start_server()
            if not server_process:
                print("\n❌ Cannot proceed without server")
                print("\n📝 To start manually:")
                print("   Terminal 1: uvicorn app.main:app --reload")
                print("   Terminal 2: python run_tests.py")
                return 1
        else:
            print("\n📝 Please start the server manually:")
            print("   uvicorn app.main:app --reload")
            print("\nThen run this script again.")
            return 1
    
    # Run integration tests
    print("="*80)
    print("RUNNING INTEGRATION TESTS")
    print("="*80)
    print()
    
    try:
        # Import and run tests
        from test_integration import run_integration_tests
        run_integration_tests()
        
    except ImportError as e:
        print(f"❌ Failed to import test_integration: {e}")
        print("\nMake sure test_integration.py exists in the current directory")
        return 1
    except Exception as e:
        print(f"❌ Tests failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        # Clean up server if we started it
        if server_process:
            print("\n" + "="*80)
            print("SERVER CLEANUP")
            print("="*80)
            print("⚠️  Server is still running in background")
            print("   To stop it, check Task Manager (Windows) or Activity Monitor (Mac)")
            print("   Or restart your terminal")
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
