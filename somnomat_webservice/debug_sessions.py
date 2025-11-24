"""Debug script to see what's happening with session detection."""
from supabase_api_client_somnomat import get_raw_occupancy_by_device, get_all_raw_occupancy_by_device
from calculate_dashboard import process_occupancy_into_sessions
from datetime import datetime, timedelta  # Added timedelta here

device_id = 61

print("Fetching occupancy data...")
occupancy_data = get_all_raw_occupancy_by_device(device_id=device_id)

if occupancy_data:
    # Check date range
    dates = [datetime.fromisoformat(r['created_at'].replace('Z', '+00:00')) for r in occupancy_data]
    print(f"\nTotal readings: {len(occupancy_data)}")
    print(f"Date range: {min(dates)} to {max(dates)}")
    print(f"Days span: {(max(dates).date() - min(dates).date()).days + 1}")
    
    # Expected readings per day
    expected_per_day = 288  # One reading every 5 minutes
    days_span = (max(dates).date() - min(dates).date()).days + 1
    expected_total = days_span * expected_per_day
    print(f"\nExpected readings for {days_span} days: {expected_total}")
    print(f"Actual readings: {len(occupancy_data)}")
    
    if len(occupancy_data) == expected_total:
        print("✅ Got all expected data!")
    else:
        print(f"⚠️  Missing: {expected_total - len(occupancy_data)} readings")
    
    # Count unique dates
    unique_dates = sorted(set(d.date() for d in dates))
    print(f"\nUnique dates: {len(unique_dates)}")
    print(f"First 5 dates: {unique_dates[:5]}")
    print(f"Last 5 dates: {unique_dates[-5:]}")
    
    # Check readings per day
    from collections import Counter
    readings_per_date = Counter(d.date() for d in dates)
    print(f"\nReadings per date:")
    for date in sorted(readings_per_date.keys()):
        count = readings_per_date[date]
        status = "✅" if count == 288 else "⚠️"
        print(f"  {status} {date}: {count} readings ({count/288*100:.1f}% of expected 288)")
    
    # Process into sessions
    print("\nProcessing sessions...")
    sessions = process_occupancy_into_sessions(occupancy_data)
    
    print(f"\n{'='*60}")
    print(f"Detected {len(sessions)} sessions:")
    print(f"{'='*60}")
    
    for i, s in enumerate(sessions, 1):
        start = s['session_start']
        end = s['session_end']
        duration = s['duration_hours']
        interruptions = s.get('num_interruptions', 0)
        
        print(f"\nSession {i}:")
        print(f"  Start: {start.strftime('%Y-%m-%d %H:%M')}")
        print(f"  End: {end.strftime('%Y-%m-%d %H:%M')}")
        print(f"  Duration: {duration:.2f} hours")
        print(f"  Interruptions: {interruptions}")
        print(f"  Occupied intervals: {s.get('occupied_intervals', 0)}")
        
        # Check which night it belongs to
        if start.hour < 14:
            night_date = (start - timedelta(days=1)).date()
            print(f"  Assigned to night: {night_date} (started before 2 PM)")
        else:
            night_date = start.date()
            print(f"  Assigned to night: {night_date} (started after 2 PM)")
    
    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  Total days with data: {len(unique_dates)}")
    print(f"  Total sessions detected: {len(sessions)}")
    print(f"  Expected sessions (1 per night): {len(unique_dates)}")
    
    if len(sessions) > len(unique_dates):
        print(f"  ⚠️  More sessions than days - possible fragmentation")
    elif len(sessions) < len(unique_dates):
        print(f"  ⚠️  Fewer sessions than days - some nights missing")
    else:
        print(f"  ✅ Sessions match days!")
    print(f"{'='*60}")
    
else:
    print("No data found!")