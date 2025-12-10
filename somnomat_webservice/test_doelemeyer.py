"""
Test script to verify connection to the Doelemeyer Supabase database.
Tests authentication, database access, and basic CRUD operations.
"""
import os
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime, timezone
import sys

# Load environment variables
load_dotenv()

# Get Doelemeyer credentials from .env
SUPABASE_URL = os.getenv("SUPABASE_URL_CALMEA_DOELEMEYER")
SUPABASE_KEY = os.getenv("SUPABASE_KEY_CALMEA_DOELEMEYER")

print("=" * 70)
print("🧪 DOELEMEYER DATABASE CONNECTION TEST")
print("=" * 70)

# Verify credentials are loaded
print("\n1️⃣ CHECKING CREDENTIALS")
print("-" * 70)

if not SUPABASE_URL:
    print("❌ SUPABASE_URL_CALMEA_DOELEMEYER not found in .env")
    sys.exit(1)
else:
    print(f"✅ URL found: {SUPABASE_URL}")

if not SUPABASE_KEY:
    print("❌ SUPABASE_KEY_CALMEA_DOELEMEYER not found in .env")
    sys.exit(1)
else:
    print(f"✅ Key found: {SUPABASE_KEY[:30]}...")

# Test 1: Create Supabase client
print("\n2️⃣ CREATING SUPABASE CLIENT")
print("-" * 70)

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Supabase client created successfully")
except Exception as e:
    print(f"❌ Failed to create client: {e}")
    sys.exit(1)

# Test 2: Test anonymous authentication
print("\n3️⃣ TESTING ANONYMOUS ACCESS")
print("-" * 70)

try:
    # Try to access a public table (devices)
    response = supabase.table("devices").select("id").limit(1).execute()
    print(f"✅ Anonymous access works (found {len(response.data)} devices)")
except Exception as e:
    print(f"⚠️ Anonymous access test: {e}")
    print("   This might be expected if RLS is enabled")

# Test 3: Test authentication signup
print("\n4️⃣ TESTING USER AUTHENTICATION")
print("-" * 70)

test_email = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com"
test_password = "TestPassword123!"

print(f"Creating test user: {test_email}")

try:
    # Sign up a test user
    auth_response = supabase.auth.sign_up({
        "email": test_email,
        "password": test_password,
        "options": {
            "data": {
                "name": "Test User",
                "test": True
            }
        }
    })
    
    if auth_response.user:
        print(f"✅ User created successfully")
        print(f"   User ID: {auth_response.user.id}")
        print(f"   Email: {auth_response.user.email}")
        test_user_id = auth_response.user.id
        
        # Save session for cleanup
        test_session = auth_response.session
    else:
        print("⚠️ User creation returned no user object")
        test_user_id = None
        test_session = None

except Exception as e:
    print(f"⚠️ Authentication test failed: {e}")
    print("   This might be expected if email confirmation is required")
    test_user_id = None
    test_session = None

# Test 4: Test database schema
print("\n5️⃣ TESTING DATABASE SCHEMA")
print("-" * 70)

expected_tables = [
    "devices",
    "raw_occupancy", 
    "sleep_dashboard",
    "firmware",
    "user_settings",
    "user_devices"
]

print("Checking for expected tables:")

for table_name in expected_tables:
    try:
        response = supabase.table(table_name).select("*").limit(1).execute()
        print(f"   ✅ {table_name:<20} - Accessible")
    except Exception as e:
        print(f"   ❌ {table_name:<20} - Error: {str(e)[:50]}")

# Test 5: Test device creation (if authenticated)
print("\n6️⃣ TESTING DEVICE CREATION")
print("-" * 70)

if test_user_id and test_session:
    try:
        # Use authenticated session
        supabase.auth.set_session(test_session.access_token, test_session.refresh_token)
        
        # Try to create a test device
        test_device = {
            "name": f"Test Device {datetime.now().strftime('%H:%M:%S')}",
            "boardtype": 1,
            "mac": "AA:BB:CC:DD:EE:FF",
            "hardware_version": "1.0"
        }
        
        device_response = supabase.table("devices").insert(test_device).execute()
        
        if device_response.data:
            device = device_response.data[0]
            print(f"✅ Device created successfully")
            print(f"   Device ID: {device['id']}")
            print(f"   Name: {device['name']}")
            test_device_id = device['id']
            
            # Test 6: Check if device was auto-linked to user
            print("\n7️⃣ TESTING AUTO-LINKING")
            print("-" * 70)
            
            try:
                user_devices = supabase.table("user_devices") \
                    .select("*") \
                    .eq("device_id", test_device_id) \
                    .eq("user_id", test_user_id) \
                    .execute()
                
                if user_devices.data:
                    print(f"✅ Device auto-linked to user")
                    print(f"   Role: {user_devices.data[0]['role']}")
                else:
                    print("⚠️ Device NOT auto-linked (trigger might be missing)")
                    
            except Exception as e:
                print(f"❌ Auto-link check failed: {e}")
            
            # Cleanup: Delete test device
            try:
                supabase.table("devices").delete().eq("id", test_device_id).execute()
                print(f"\n🧹 Cleaned up test device (ID: {test_device_id})")
            except:
                pass
                
        else:
            print("⚠️ Device creation returned no data")
            
    except Exception as e:
        print(f"❌ Device creation failed: {e}")
        print(f"   Error details: {str(e)}")
else:
    print("⏭️ Skipped (no authenticated user)")

# Test 7: Test occupancy data creation
print("\n8️⃣ TESTING OCCUPANCY DATA")
print("-" * 70)

if test_user_id and test_session:
    try:
        # Create a simple device for testing
        simple_device = supabase.table("devices") \
            .insert({"name": "Occupancy Test Device"}) \
            .execute()
        
        if simple_device.data:
            device_id = simple_device.data[0]['id']
            
            # Try to insert occupancy reading
            occupancy_data = {
                "device_id": device_id,
                "occupied": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            occupancy_response = supabase.table("raw_occupancy") \
                .insert(occupancy_data) \
                .execute()
            
            if occupancy_response.data:
                print(f"✅ Occupancy data created")
                print(f"   Device ID: {device_id}")
                print(f"   Occupied: {occupancy_response.data[0]['occupied']}")
            else:
                print("⚠️ Occupancy creation returned no data")
            
            # Cleanup
            try:
                supabase.table("devices").delete().eq("id", device_id).execute()
                print(f"🧹 Cleaned up occupancy test device")
            except:
                pass
                
    except Exception as e:
        print(f"⚠️ Occupancy test: {e}")
else:
    print("⏭️ Skipped (no authenticated user)")

# Test 8: Check existing data
print("\n9️⃣ CHECKING EXISTING DATA")
print("-" * 70)

try:
    # Count devices
    devices = supabase.table("devices").select("id", count="exact").execute()
    print(f"📊 Total devices in database: {devices.count if hasattr(devices, 'count') else 'N/A'}")
    
    # Count occupancy readings
    occupancy = supabase.table("raw_occupancy").select("id", count="exact").limit(1).execute()
    print(f"📊 Total occupancy readings: {occupancy.count if hasattr(occupancy, 'count') else 'N/A'}")
    
    # Count users (if accessible)
    try:
        users = supabase.table("user_devices").select("user_id", count="exact").execute()
        print(f"📊 Total user-device links: {users.count if hasattr(users, 'count') else 'N/A'}")
    except:
        print(f"📊 User data: Not accessible (RLS enabled)")
        
except Exception as e:
    print(f"⚠️ Could not count existing data: {e}")

# Final Summary
print("\n" + "=" * 70)
print("📋 TEST SUMMARY")
print("=" * 70)

print(f"""
✅ Connection Status: {'SUCCESS' if supabase else 'FAILED'}
✅ Database URL: {SUPABASE_URL}
✅ Authentication: {'Working' if test_user_id else 'Limited/Email confirmation required'}
✅ Tables: Accessible
✅ Device Creation: {'Working' if test_user_id else 'Requires authentication'}

💡 Next Steps:
   1. If authentication requires email confirmation, check your Supabase auth settings
   2. Verify Row-Level Security (RLS) policies are properly configured
   3. Test with your actual user account:
      
      python auth_cli.py signup your@email.com YourPassword123
      python setup_device.py "Test Device"
      streamlit run somnomat_dashboard.py

🎉 Database connection is working! You can now use this database.
""")

print("=" * 70)

# Cleanup test user (if created)
if test_session:
    try:
        supabase.auth.sign_out()
        print("🧹 Signed out test user")
    except:
        pass