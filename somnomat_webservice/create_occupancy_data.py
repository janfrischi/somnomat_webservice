"""
Create realistic occupancy data for testing the dashboard.
Simplified version - use setup_device.py for complete device setup.
"""
from supabase_api_client_somnomat import create_raw_occupancy, get_device_by_id
from datetime import datetime, timedelta, timezone
import sys
import random


def create_realistic_occupancy(device_id: int, days: int = 7, start_date: str = None):
    """
    Generate realistic sleep occupancy data going BACKWARDS from today (or specified date).
    
    Sleep pattern assumptions:
    - Base bedtime: 22:00 (10 PM) ± 60 minutes variation
    - Base wake time: 08:00 (8 AM) ± 60 minutes variation
    - Average sleep duration: 8 hours
    - 30% chance of night wakings (1-30 minutes)
    - Slight weekday/weekend variation
    
    Args:
        device_id: Device ID to create data for
        days: Number of days to generate going backwards (default: 7)
        start_date: End date to count backwards from in 'YYYY-MM-DD' format (default: today)
    
    Example:
        If today is 2024-12-20 and days=30:
        - Generates data from 2024-11-20 to 2024-12-20 (30 days)
    """
    
    print(f"Creating {days} days of occupancy data for device {device_id}...")
    
    # Verify device exists
    device = get_device_by_id(device_id)
    if not device:
        print(f"❌ Device {device_id} not found!")
        return 0
    
    print(f"✅ Found device: {device['name']} (ID: {device_id})\n")
    
    # Set end date (default to today)
    if start_date:
        try:
            end_date = datetime.strptime(start_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
        except ValueError:
            print(f"⚠️  Invalid date format '{start_date}'. Using today.")
            end_date = datetime.now(timezone.utc)
    else:
        end_date = datetime.now(timezone.utc)
    
    # Round to end of day (23:59:59)
    end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    # Calculate start date (going backwards)
    start_date_calc = end_date - timedelta(days=days - 1)
    start_date_calc = start_date_calc.replace(hour=0, minute=0, second=0, microsecond=0)
    
    print(f"📅 Generating data BACKWARDS from {end_date.strftime('%Y-%m-%d')}")
    print(f"   Start date: {start_date_calc.strftime('%Y-%m-%d')}")
    print(f"   End date: {end_date.strftime('%Y-%m-%d')}")
    print(f"   Total days: {days}\n")
    
    created_count = 0
    
    # Generate data for each day (going forward through the date range)
    for day_offset in range(days):
        # Calculate the current day
        current_day = start_date_calc + timedelta(days=day_offset)
        day_start = current_day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_of_week = day_start.weekday()  # 0=Monday, 6=Sunday
        
        # Weekend detection (Friday/Saturday nights allow later bedtimes)
        is_weekend_night = day_of_week in [4, 5]  # Friday or Saturday
        
        # Base sleep times
        base_bedtime_hour = 22  # 10 PM
        base_waketime_hour = 8  # 8 AM
        
        # Add variation
        if is_weekend_night:
            # Weekend: tend to stay up later (up to 2 hours), wake up later
            bedtime_variation = random.randint(-30, 120)  # -30 min to +2 hours
            waketime_variation = random.randint(-30, 90)  # -30 min to +1.5 hours
        else:
            # Weekday: more consistent, smaller variation
            bedtime_variation = random.randint(-45, 60)  # -45 min to +1 hour
            waketime_variation = random.randint(-30, 60)  # -30 min to +1 hour
        
        # Calculate actual sleep times in minutes from midnight
        bedtime_minutes = (base_bedtime_hour * 60) + bedtime_variation
        waketime_minutes = (base_waketime_hour * 60) + waketime_variation
        
        # Ensure reasonable bounds
        bedtime_minutes = max(20 * 60, min(26 * 60, bedtime_minutes))  # Between 8 PM and 2 AM
        waketime_minutes = max(5 * 60, min(11 * 60, waketime_minutes))  # Between 5 AM and 11 AM
        
        # Night wakings (30% chance)
        night_wakings = []
        if random.random() < 0.3:
            # 1-3 wakings per night
            num_wakings = random.randint(1, 3)
            for _ in range(num_wakings):
                # Wakings typically happen in early morning hours (3-6 AM)
                waking_start_minutes = random.randint(3 * 60, 6 * 60)  # 3-6 AM in minutes
                waking_duration = random.randint(1, 30)  # 1-30 minutes
                night_wakings.append((waking_start_minutes, waking_duration))
        
        # Format day counter to show actual date
        current_date = day_start.strftime('%Y-%m-%d')
        day_name = day_start.strftime('%A')
        days_ago = (end_date.date() - day_start.date()).days
        
        print(f"{current_date} ({day_name}) [{days_ago} days ago]: "
              f"Bedtime ~{bedtime_minutes // 60:02d}:{bedtime_minutes % 60:02d}, "
              f"Wake ~{waketime_minutes // 60:02d}:{waketime_minutes % 60:02d}")
        
        # Create readings every 5 minutes (288 readings per day)
        for minute in range(0, 1440, 5):
            timestamp = day_start + timedelta(minutes=minute)
            current_minute_of_day = timestamp.hour * 60 + timestamp.minute
            
            # Determine if occupied based on sleep schedule
            is_occupied = False
            
            # Check if in sleep period
            # Handle sleep that crosses midnight (most common case: 22:00 to 08:00)
            if bedtime_minutes >= 24 * 60:
                # Bedtime is past midnight (e.g., 1 AM = 1500 minutes)
                actual_bedtime = bedtime_minutes - 24 * 60
                if current_minute_of_day >= actual_bedtime or current_minute_of_day < waketime_minutes:
                    is_occupied = True
            elif bedtime_minutes > waketime_minutes:
                # Crosses midnight (normal case: 22:00 to 08:00)
                if current_minute_of_day >= bedtime_minutes or current_minute_of_day < waketime_minutes:
                    is_occupied = True
            else:
                # Doesn't cross midnight (unusual: e.g., nap during day)
                if bedtime_minutes <= current_minute_of_day < waketime_minutes:
                    is_occupied = True
            
            # Apply night wakings (simplified - no midnight crossing issues)
            for waking_start_minutes, waking_duration in night_wakings:
                waking_end_minutes = waking_start_minutes + waking_duration
                if waking_start_minutes <= current_minute_of_day < waking_end_minutes:
                    is_occupied = False
            
            # Add occasional sensor noise (1% false readings)
            if random.random() < 0.01:
                is_occupied = not is_occupied
            
            try:
                reading = create_raw_occupancy(
                    device_id=device_id,
                    occupied=is_occupied,
                    created_at=timestamp.isoformat()
                )
                
                if reading:
                    created_count += 1
                    if created_count % 1000 == 0:
                        print(f"   Created {created_count} readings...")
                        
            except Exception as e:
                print(f"❌ Error creating reading at {timestamp}: {e}")
                continue
    
    print(f"\n{'='*60}")
    print(f"✅ Successfully created {created_count} occupancy readings")
    print(f"   Device: {device['name']} (ID: {device_id})")
    print(f"   Period: {start_date_calc.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print(f"   Total days: {days}")
    print(f"   Total readings: {created_count} ({created_count // days} per day)")
    print(f"   Expected sleep sessions: ~{days} nights")
    print(f"   Average bedtime: 10:00 PM ± 1 hour")
    print(f"   Average wake time: 8:00 AM ± 1 hour")
    print(f"   Sleep pattern: Realistic with weekday/weekend variation")
    print(f"{'='*60}\n")
    
    print("💡 Next steps:")
    print(f"   1. Calculate dashboard: python calculate_dashboard.py {device_id}")
    print(f"   2. View in dashboard: streamlit run somnomat_dashboard.py")
    
    return created_count


if __name__ == "__main__":
    # Use device ID from command line or default
    if len(sys.argv) < 2:
        print("Usage: python create_occupancy_data.py <device_id> [days] [end_date]")
        print("\nExamples:")
        print("  # Generate last 30 days from today")
        print("  python create_occupancy_data.py 61 30")
        print()
        print("  # Generate last 7 days from today (default)")
        print("  python create_occupancy_data.py 61")
        print()
        print("  # Generate 60 days backwards from a specific date")
        print("  python create_occupancy_data.py 61 60 2024-12-31")
        print()
        print("  # Generate 90 days from today")
        print("  python create_occupancy_data.py 61 90")
        print("\nArguments:")
        print("  device_id  : Device ID (required)")
        print("  days       : Number of days to generate backwards (default: 7)")
        print("  end_date   : End date to count back from in YYYY-MM-DD (default: today)")
        print("\nNote: Data is generated BACKWARDS from the end_date (or today)")
        sys.exit(1)
    
    device_id = int(sys.argv[1])
    days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
    end_date_param = sys.argv[3] if len(sys.argv) > 3 else None
    
    create_realistic_occupancy(device_id, days, end_date_param)