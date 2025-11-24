"""
Complete device setup script.
Populates all tables for a new device with realistic data.
"""
import sys
from datetime import datetime, timedelta, timezone
from supabase_auth_client import auth_client
from supabase_api_client_somnomat import (
    create_device,
    get_device_by_id
)
from calculate_dashboard import calculate_and_update_dashboard
# Import the realistic occupancy generator from create_occupancy_data
from create_occupancy_data import create_realistic_occupancy


def setup_device(
    device_name: str,
    mac: str = None,
    boardtype: int = None,
    hardware_version: str = None,
    days_of_data: int = 30,
    start_date: str = None,
    auto_link: bool = True
):
    """
    Complete device setup with all data.
    
    Args:
        device_name: Name for the device
        mac: MAC address (optional)
        boardtype: Board type ID (optional)
        hardware_version: Hardware version (optional)
        days_of_data: Days of historical data to generate
        start_date: Start date in YYYY-MM-DD format (default: 2025-01-01)
        auto_link: Whether to link device to current user
    
    Returns:
        Device ID if successful, None otherwise
    """
    
    print("=" * 70)
    print("🚀 SOMNOMAT DEVICE SETUP")
    print("=" * 70)
    
    # Step 1: Check authentication
    user = auth_client.get_current_user()
    if not user and auto_link:
        print("\n❌ Error: No authenticated user!")
        print("💡 Please sign in first:")
        print("   python auth_cli.py signin your@email.com yourpassword")
        return None
    
    if user:
        print(f"\n👤 Authenticated as: {user.email}")
    
    # Step 2: Create device
    print(f"\n📱 Creating device: {device_name}")
    
    try:
        # Map boardtype name to ID if it's a string
        if isinstance(boardtype, str):
            boardtype_map = {
                "ESP32": 1,
                "ESP8266": 2,
                "Arduino": 3
            }
            boardtype = boardtype_map.get(boardtype, 1)
        
        if user:
            # Use authenticated client for auto-linking
            device = auth_client.register_device(
                device_name=device_name,
                mac=mac,
                boardtype=boardtype or "ESP32",
                hardware_version=hardware_version or "v1.0"
            )
            
            if not device.get("success"):
                print(f"❌ Failed to create device: {device.get('error')}")
                return None
            
            device_id = device['device_id']
        else:
            # Use regular API client (no auto-link)
            device = create_device(
                name=device_name,
                mac=mac,
                boardtype=boardtype,
                hardware_version=hardware_version
            )
            
            if not device:
                print("❌ Failed to create device")
                return None
            
            device_id = device['id']
        
        print(f"   ✅ Device created (ID: {device_id})")
        
    except Exception as e:
        print(f"❌ Error creating device: {e}")
        return None
    
    # Step 3: Generate occupancy data using the realistic generator
    print(f"\n💤 Generating realistic sleep data...")
    occupancy_count = create_realistic_occupancy(device_id, days=days_of_data, start_date=start_date)
    
    if occupancy_count == 0:
        print("⚠️  Warning: No occupancy data created")
        return device_id
    
    # Step 4: Calculate dashboard metrics
    print(f"\n📈 Calculating dashboard metrics...")
    
    try:
        dashboard = calculate_and_update_dashboard(device_id)
        
        if dashboard:
            print(f"   ✅ Dashboard metrics calculated")
            print(f"      • Sleep Consistency: {dashboard['sleep_consistency']:.1f}/100")
            print(f"      • Avg Sleep/Night: {dashboard['avg_sleep_per_night']:.1f} hrs")
            print(f"      • Total Nights: {int(dashboard['total_nights'])}")
            print(f"      • Bedtime Consistency: {dashboard['bedtime_consistency']:.1f}/100")
        else:
            print("   ⚠️  Dashboard calculation completed but no data returned")
            
    except Exception as e:
        print(f"   ⚠️  Error calculating dashboard: {e}")
    
    # Step 5: Summary
    print("\n" + "=" * 70)
    print("✅ SETUP COMPLETE!")
    print("=" * 70)
    print(f"\n📊 Summary:")
    print(f"   Device ID:      {device_id}")
    print(f"   Device Name:    {device_name}")
    if mac:
        print(f"   MAC Address:    {mac}")
    if user:
        print(f"   Linked to:      {user.email}")
    print(f"   Data Period:    {days_of_data} days")
    print(f"   Total Readings: {occupancy_count}")
    print(f"   Sleep Pattern:  Realistic (10 PM - 8 AM base)")
    
    print(f"\n🎯 Next Steps:")
    print(f"   1. View in CLI:")
    print(f"      python auth_cli.py devices")
    print(f"\n   2. View dashboard:")
    print(f"      streamlit run somnomat_dashboard.py")
    print(f"\n   3. Recalculate metrics:")
    print(f"      python calculate_dashboard.py {device_id}")
    
    print("\n" + "=" * 70 + "\n")
    
    return device_id


def main():
    """Main CLI interface."""
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python setup_device.py <device_name> [mac] [boardtype] [days] [start_date]")
        print("\nExamples:")
        print("  python setup_device.py 'My Bedroom'")
        print("  python setup_device.py 'Living Room' 'AA:BB:CC:DD:EE:FF'")
        print("  python setup_device.py 'Guest Room' 'AA:BB:CC:DD:EE:FF' ESP32 60")
        print("  python setup_device.py 'Test Device' None ESP32 90 2024-10-01")
        print("\nArguments:")
        print("  device_name  : Name for the device (required)")
        print("  mac          : MAC address (optional, use 'None' to skip)")
        print("  boardtype    : Board type - ESP32, ESP8266, or Arduino (optional)")
        print("  days         : Days of historical data (default: 30)")
        print("  start_date   : Start date in YYYY-MM-DD format (default: 2025-01-01)")
        return
    
    device_name = sys.argv[1]
    mac = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] != 'None' else None
    boardtype = sys.argv[3] if len(sys.argv) > 3 else None
    days = int(sys.argv[4]) if len(sys.argv) > 4 else 30
    start_date = sys.argv[5] if len(sys.argv) > 5 else None
    
    setup_device(
        device_name=device_name,
        mac=mac,
        boardtype=boardtype,
        days_of_data=days,
        start_date=start_date
    )


if __name__ == "__main__":
    main()