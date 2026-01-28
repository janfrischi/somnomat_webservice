"""
Quick test script to verify occupancy data access.
Tests both authenticated and anonymous access to raw_occupancy table.
"""
from supabase_auth_client import auth_client
from supabase_api_client_somnomat import supabase, get_device_by_id, get_all_raw_occupancy_by_device

print("=" * 70)
print("🧪 OCCUPANCY DATA ACCESS TEST")
print("=" * 70)

# Test 1: Check authentication
print("\n1️⃣ CHECKING AUTHENTICATION")
print("-" * 70)

user = auth_client.get_current_user()
if user:
    print(f"✅ Authenticated as: {user.email}")
    print(f"   User ID: {user.id}")
else:
    print("❌ Not authenticated")
    print("💡 Sign in first: python auth_cli.py signin email password")
    exit(1)

# Test 2: List available devices
print("\n2️⃣ LISTING AVAILABLE DEVICES")
print("-" * 70)

try:
    # Using authenticated client
    devices_response = auth_client.client.table('devices') \
        .select('id, name, mac, boardtype') \
        .execute()
    
    if devices_response.data:
        print(f"✅ Found {len(devices_response.data)} device(s):")
        for device in devices_response.data:
            print(f"   • ID: {device['id']}, Name: {device['name']}")
        
        # Use first device for testing
        test_device_id = devices_response.data[0]['id']
        test_device_name = devices_response.data[0]['name']
    else:
        print("❌ No devices found")
        print("💡 Create a device: python setup_device.py 'My Device'")
        exit(1)
        
except Exception as e:
    print(f"❌ Error fetching devices: {e}")
    exit(1)

# Test 3: Test authenticated access to occupancy data
print(f"\n3️⃣ TESTING AUTHENTICATED ACCESS (Device: {test_device_name})")
print("-" * 70)

try:
    # Using authenticated client directly
    occupancy_auth = auth_client.client.table('raw_occupancy') \
        .select('id, device_id, occupied, created_at') \
        .eq('device_id', test_device_id) \
        .limit(5) \
        .execute()
    
    if occupancy_auth.data:
        print(f"✅ Authenticated access works!")
        print(f"   Found {len(occupancy_auth.data)} readings (showing first 5)")
        for reading in occupancy_auth.data[:3]:
            print(f"   • ID: {reading['id']}, Occupied: {reading['occupied']}, "
                  f"Time: {reading['created_at'][:19]}")
    else:
        print("⚠️  No occupancy data found for this device")
        print(f"💡 Create data: python create_occupancy_data.py {test_device_id} 7")
        
except Exception as e:
    print(f"❌ Authenticated access failed: {e}")

# Test 4: Test anonymous access to occupancy data
print(f"\n4️⃣ TESTING ANONYMOUS ACCESS (API Client)")
print("-" * 70)

try:
    # Using anonymous API client
    occupancy_anon = supabase.table('raw_occupancy') \
        .select('id, device_id, occupied, created_at') \
        .eq('device_id', test_device_id) \
        .limit(5) \
        .execute()
    
    if occupancy_anon.data:
        print(f"✅ Anonymous access works!")
        print(f"   Found {len(occupancy_anon.data)} readings (showing first 5)")
    else:
        print("⚠️  Anonymous client returned no data")
        print("   This might be due to RLS policies")
        
except Exception as e:
    print(f"❌ Anonymous access failed: {e}")
    print("   RLS is blocking anonymous access (expected)")

# Test 5: Test helper function
print(f"\n5️⃣ TESTING HELPER FUNCTION (get_all_raw_occupancy_by_device)")
print("-" * 70)

try:
    occupancy_helper = get_all_raw_occupancy_by_device(test_device_id)
    
    if occupancy_helper:
        print(f"✅ Helper function works!")
        print(f"   Total readings: {len(occupancy_helper)}")
        
        # Show date range
        if len(occupancy_helper) > 0:
            dates = [r['created_at'][:10] for r in occupancy_helper]
            print(f"   Date range: {min(dates)} to {max(dates)}")
    else:
        print("⚠️  Helper function returned no data")
        
except Exception as e:
    print(f"❌ Helper function failed: {e}")

# Test 6: Test device lookup
print(f"\n6️⃣ TESTING DEVICE LOOKUP (get_device_by_id)")
print("-" * 70)

try:
    device = get_device_by_id(test_device_id)
    
    if device:
        print(f"✅ Device lookup works!")
        print(f"   Name: {device['name']}")
        print(f"   ID: {device['id']}")
    else:
        print(f"❌ Device {test_device_id} not found via anonymous client")
        print("   RLS is blocking anonymous access")
        
except Exception as e:
    print(f"❌ Device lookup failed: {e}")

# Summary
print("\n" + "=" * 70)
print("📋 TEST SUMMARY")
print("=" * 70)

print(f"""
✅ Authentication: {'Working' if user else 'Failed'}
✅ Device Listing: {'Working' if devices_response.data else 'Failed'}
✅ Authenticated Access: Check output above
⚠️  Anonymous Access: Likely blocked by RLS (this is normal)

💡 RECOMMENDATIONS:
   1. If authenticated access works but anonymous doesn't:
      → This is expected! RLS is protecting your data
      → Update create_occupancy_data.py to use auth_client
   
   2. If both fail:
      → Check RLS policies in Supabase Dashboard
      → Run: DROP POLICY IF EXISTS ... and recreate policies
   
   3. If no occupancy data found:
      → Run: python create_occupancy_data.py {test_device_id} 30
""")

print("=" * 70)