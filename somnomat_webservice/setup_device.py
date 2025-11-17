"""
Complete device setup script.
Populates all tables for a new device with realistic data.
"""
import sys
from datetime import datetime, timedelta, timezone
from supabase_auth_client import auth_client
from supabase_api_client_somnomat import (
    create_device,
    create_raw_occupancy,
    get_device_by_id
)
from calculate_dashboard import calculate_and_update_dashboard
import random


def create_realistic_occupancy(device_id: int, days: int = 30):
    """
    Generate realistic sleep occupancy data.
    
    Args:
        device_id: Device ID to create data for
        days: Number of days of historical data to generate
    
    Returns:
        Number of readings created
    """
    print(f"\n📊 Generating {days} days of occupancy data...")
    
    now = datetime.now(timezone.utc)
    created_count = 0
    
    for day in range(days):
        day_start = (now - timedelta(days=day)).replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Randomize sleep schedule slightly for realism
        # Base sleep time: 11 PM to 7 AM (8 hours)
        sleep_start_hour = 23 + random.randint(-1, 1)  # 22:00 - 00:00
        sleep_end_hour = 7 + random.randint(-1, 1)     # 06:00 - 08:00
        
        # Add occasional night wakings (5% chance per hour)
        night_wakings = []
        if random.random() < 0.3:  # 30% chance of waking during night
            waking_hour = random.randint(1, 5)
            waking_duration = random.randint(5, 30)  # 5-30 minutes
            night_wakings.append((waking_hour, waking_duration))
        
        # Create readings every 5 minutes (288 readings per day)
        for minute in range(0, 1440, 5):  # 1440 minutes in a day
            timestamp = day_start + timedelta(minutes=minute)
            hour = timestamp.hour
            
            # Determine if bed is occupied
            is_occupied = False
            
            # Check if in sleep period
            if sleep_start_hour >= 23:  # Sleep starts before midnight
                if hour >= sleep_start_hour or hour < sleep_end_hour:
                    is_occupied = True
            else:  # Sleep starts after midnight
                if sleep_start_hour <= hour < sleep_end_hour:
                    is_occupied = True
            
            # Apply night wakings
            for waking_hour, waking_duration in night_wakings:
                waking_start = day_start + timedelta(hours=waking_hour)
                waking_end = waking_start + timedelta(minutes=waking_duration)
                if waking_start <= timestamp < waking_end:
                    is_occupied = False
            
            # Add occasional daytime naps (2% chance)
            if 13 <= hour <= 15 and random.random() < 0.02:
                is_occupied = True
            
            try:
                reading = create_raw_occupancy(
                    device_id=device_id,
                    occupied=is_occupied,
                    created_at=timestamp.isoformat()
                )
                
                if reading:
                    created_count += 1
                    if created_count % 500 == 0:
                        print(f"   ✓ Created {created_count} readings...")
                        
            except Exception as e:
                print(f"   ⚠️  Error at {timestamp}: {e}")
                continue
    
    print(f"   ✅ Created {created_count} total readings")
    return created_count


def setup_device(
    device_name: str,
    mac: str = None,
    boardtype: int = None,
    hardware_version: str = None,
    days_of_data: int = 30,
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
        if user:
            # Use authenticated client for auto-linking
            device = auth_client.create_device(
                name=device_name,
                mac=mac,
                boardtype=boardtype,
                hardware_version=hardware_version
            )
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
    
    # Step 3: Generate occupancy data
    print(f"\n💤 Generating sleep data...")
    occupancy_count = create_realistic_occupancy(device_id, days=days_of_data)
    
    if occupancy_count == 0:
        print("⚠️  Warning: No occupancy data created")
    
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
    
    print(f"\n🎯 Next Steps:")
    print(f"   1. View in CLI:")
    print(f"      python auth_cli.py devices")
    print(f"\n   2. View dashboard:")
    print(f"      streamlit run view_dashboard_streamlit_auth.py")
    print(f"\n   3. Recalculate metrics:")
    print(f"      python calculate_dashboard.py {device_id}")
    
    print("\n" + "=" * 70 + "\n")
    
    return device_id


def main():
    """Main CLI interface."""
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python setup_device.py <device_name> [mac] [boardtype] [days]")
        print("\nExamples:")
        print("  python setup_device.py 'My Bedroom'")
        print("  python setup_device.py 'Living Room' 'AA:BB:CC:DD:EE:FF'")
        print("  python setup_device.py 'Guest Room' 'AA:BB:CC:DD:EE:FF' 1 60")
        print("\nArguments:")
        print("  device_name  : Name for the device (required)")
        print("  mac          : MAC address (optional)")
        print("  boardtype    : Board type ID (optional)")
        print("  days         : Days of historical data (default: 30)")
        return
    
    device_name = sys.argv[1]
    mac = sys.argv[2] if len(sys.argv) > 2 else None
    boardtype = int(sys.argv[3]) if len(sys.argv) > 3 else None
    days = int(sys.argv[4]) if len(sys.argv) > 4 else 30
    
    setup_device(
        device_name=device_name,
        mac=mac,
        boardtype=boardtype,
        days_of_data=days
    )


if __name__ == "__main__":
    main()