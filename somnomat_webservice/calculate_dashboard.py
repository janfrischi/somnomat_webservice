"""
Calculate dashboard metrics from raw occupancy data and store in sleep_dashboard table.
"""
from supabase_api_client_somnomat import (
    get_all_raw_occupancy_by_device,
    get_device_by_id,
    create_or_update_dashboard
)
import statistics
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Tuple


def process_occupancy_into_sessions(
    occupancy_readings: List[Dict[str, Any]], 
    min_duration_minutes: int = 60,
    gap_tolerance_minutes: int = 30
) -> List[Dict[str, Any]]:
    """
    Convert raw occupancy readings into sleep sessions.
    
    Key improvements:
    - Duration calculated by COUNTING occupied 5-minute intervals, not time span
    - Merges sessions separated by small gaps (night wakings < 30 min)
    - Groups multiple sessions per night into one
    - More accurate representation of actual sleep time
    
    Args:
        occupancy_readings: List of occupancy readings (5-min intervals)
        min_duration_minutes: Minimum session duration to count (default: 60 min)
        gap_tolerance_minutes: Max gap to still consider same session (default: 30 min)
    
    Returns:
        List of sleep sessions with accurate duration
    """
    if not occupancy_readings:
        return []
    
    # Sort by timestamp
    sorted_readings = sorted(occupancy_readings, key=lambda x: x['created_at'])
    
    sessions = []
    current_session_start = None
    current_session_occupied_count = 0  # Count occupied intervals
    last_occupied_time = None
    last_reading_time = None
    
    for reading in sorted_readings:
        timestamp = datetime.fromisoformat(reading['created_at'].replace('Z', '+00:00'))
        is_occupied = reading['occupied']
        
        if is_occupied:
            if current_session_start is None:
                # Start new session
                current_session_start = timestamp
                last_occupied_time = timestamp
                current_session_occupied_count = 1
            else:
                # Check gap since last occupied reading
                time_gap = (timestamp - last_occupied_time).total_seconds() / 60
                
                if time_gap <= gap_tolerance_minutes:
                    # Continue current session (small gap, like brief waking)
                    last_occupied_time = timestamp
                    current_session_occupied_count += 1
                else:
                    # Gap too large - end current session, start new one
                    duration_minutes = current_session_occupied_count * 5
                    
                    if duration_minutes >= min_duration_minutes:
                        sessions.append({
                            'session_start': current_session_start,
                            'session_end': last_occupied_time,
                            'duration_hours': duration_minutes / 60,
                            'duration_min': duration_minutes,
                            'occupied_intervals': current_session_occupied_count
                        })
                    
                    # Start new session
                    current_session_start = timestamp
                    last_occupied_time = timestamp
                    current_session_occupied_count = 1
        else:
            # Not occupied
            if current_session_start is not None and last_occupied_time is not None:
                # Check if gap is too large to continue session
                time_gap = (timestamp - last_occupied_time).total_seconds() / 60
                
                if time_gap > gap_tolerance_minutes:
                    # End the session
                    duration_minutes = current_session_occupied_count * 5
                    
                    if duration_minutes >= min_duration_minutes:
                        sessions.append({
                            'session_start': current_session_start,
                            'session_end': last_occupied_time,
                            'duration_hours': duration_minutes / 60,
                            'duration_min': duration_minutes,
                            'occupied_intervals': current_session_occupied_count
                        })
                    
                    current_session_start = None
                    last_occupied_time = None
                    current_session_occupied_count = 0
        
        last_reading_time = timestamp
    
    # Handle last session if still active
    if current_session_start is not None and last_occupied_time is not None:
        duration_minutes = current_session_occupied_count * 5
        
        if duration_minutes >= min_duration_minutes:
            sessions.append({
                'session_start': current_session_start,
                'session_end': last_occupied_time,
                'duration_hours': duration_minutes / 60,
                'duration_min': duration_minutes,
                'occupied_intervals': current_session_occupied_count
            })
    
    # Merge sessions that belong to the same night
    merged_sessions = merge_sessions_by_night(sessions)
    
    return merged_sessions


def merge_sessions_by_night(sessions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Merge multiple sessions that belong to the same night.
    
    A "night" is defined as starting at 6 PM and ending at 2 PM the next day.
    This handles multiple sessions caused by night wakings.
    
    Duration is calculated as the SUM of all session durations in that night.
    """
    if not sessions:
        return []
    
    # Group sessions by night
    nights = {}
    
    for session in sessions:
        start_time = session['session_start']
        
        # Determine which "night" this belongs to
        # If start time is before 2 PM (14:00), it belongs to previous night
        # Otherwise it belongs to current night
        if start_time.hour < 14:
            # Belongs to previous night
            night_date = (start_time - timedelta(days=1)).date()
        else:
            # Belongs to current night
            night_date = start_time.date()
        
        if night_date not in nights:
            nights[night_date] = []
        
        nights[night_date].append(session)
    
    # Merge sessions for each night
    merged = []
    
    for night_date, night_sessions in sorted(nights.items()):
        if not night_sessions:
            continue
        
        # Sort sessions by start time
        night_sessions.sort(key=lambda x: x['session_start'])
        
        # Find earliest start and latest end
        earliest_start = min(s['session_start'] for s in night_sessions)
        latest_end = max(s['session_end'] for s in night_sessions)
        
        # Sum the actual occupied time (not the span)
        total_duration_hours = sum(s['duration_hours'] for s in night_sessions)
        total_duration_min = sum(s['duration_min'] for s in night_sessions)
        total_intervals = sum(s['occupied_intervals'] for s in night_sessions)
        
        merged.append({
            'session_start': earliest_start,
            'session_end': latest_end,
            'duration_hours': total_duration_hours,
            'duration_min': total_duration_min,
            'occupied_intervals': total_intervals,
            'num_interruptions': len(night_sessions) - 1  # Number of gaps
        })
    
    return merged


def calculate_sleep_consistency(sessions: List[Dict[str, Any]]) -> float:
    """
    Calculate sleep consistency score (0-100).
    Based on standard deviation of sleep duration.
    Lower std dev = higher consistency.
    """
    if len(sessions) < 2:
        return 100.0  # Default to perfect if not enough data
    
    durations = [s['duration_hours'] for s in sessions if s.get('duration_hours')]
    if not durations:
        return 100.0
    
    std_dev = statistics.stdev(durations)
    # Convert to 0-100 score (assuming std dev of 0 = 100, std dev of 3+ hours = 0)
    consistency = max(0, 100 - (std_dev * 33.33))
    return round(consistency, 2)


def calculate_bedtime_consistency(sessions: List[Dict[str, Any]]) -> float:
    """
    Calculate bedtime consistency score (0-100).
    Based on standard deviation of bedtime hours.
    """
    if len(sessions) < 2:
        return 100.0  # Default to perfect if not enough data
    
    # Extract hour of bedtime
    bedtimes = []
    for s in sessions:
        if s.get('session_start'):
            dt = s['session_start']
            # Convert to hour of day (0-23)
            bedtimes.append(dt.hour + dt.minute / 60.0)
    
    if not bedtimes:
        return 100.0
    
    std_dev = statistics.stdev(bedtimes)
    # Assuming std dev of 0 = 100, std dev of 4+ hours = 0
    consistency = max(0, 100 - (std_dev * 25))
    return round(consistency, 2)


def calculate_bed_use(sessions: List[Dict[str, Any]], days_period: int = 30) -> float:
    """
    Calculate bed usage percentage.
    Total hours in bed / total hours in period.
    """
    if not sessions:
        return 0.0
    
    total_hours_in_bed = sum(s['duration_hours'] for s in sessions if s.get('duration_hours'))
    total_hours_in_period = days_period * 24
    
    bed_use_percent = (total_hours_in_bed / total_hours_in_period) * 100
    return round(bed_use_percent, 2)


def calculate_daily_occupancy(sessions: List[Dict[str, Any]]) -> float:
    """
    Calculate average daily bed occupancy (hours per day).
    """
    if not sessions:
        return 0.0
    
    # Get date range
    dates = set()
    for s in sessions:
        if s.get('session_start'):
            dates.add(s['session_start'].date())
    
    if not dates:
        return 0.0
    
    days = len(dates)
    total_hours = sum(s['duration_hours'] for s in sessions if s.get('duration_hours'))
    
    return round(total_hours / days, 2)


def count_interruptions(sessions: List[Dict[str, Any]]) -> int:
    """
    Count total number of sleep interruptions.
    Now uses the num_interruptions from merged sessions.
    """
    if not sessions:
        return 0
    
    # Sum up interruptions from all nights
    total_interruptions = sum(s.get('num_interruptions', 0) for s in sessions)
    
    return total_interruptions


def generate_suggestions(metrics: Dict[str, Any]) -> Dict[str, str]:
    """Generate personalized suggestions based on metrics."""
    suggestions = {}
    
    # Awakening suggestion
    total_intervals = metrics.get('total_intervals', 0)
    if total_intervals > 10:
        suggestions['suggestion_awakening'] = "You're waking up frequently. Consider reviewing your sleep environment (temperature, noise, light)."
    elif total_intervals > 5:
        suggestions['suggestion_awakening'] = "You have some sleep interruptions. Try to maintain a consistent sleep routine."
    else:
        suggestions['suggestion_awakening'] = "Great job! You're sleeping through the night with minimal interruptions."
    
    # Average sleep suggestion
    avg_sleep = metrics.get('avg_sleep_per_night', 0)
    if avg_sleep < 6:
        suggestions['suggestion_avg_sleep'] = "You're getting less than 6 hours of sleep. Aim for 7-9 hours for optimal health."
    elif avg_sleep < 7:
        suggestions['suggestion_avg_sleep'] = "Try to increase your sleep time to at least 7 hours per night."
    elif avg_sleep > 9:
        suggestions['suggestion_avg_sleep'] = "You're sleeping more than 9 hours. This might indicate poor sleep quality or other health issues."
    else:
        suggestions['suggestion_avg_sleep'] = "Excellent! You're getting the recommended 7-9 hours of sleep."
    
    # Consistency suggestion
    consistency = metrics.get('sleep_consistency', 0)
    if consistency < 60:
        suggestions['suggestion_consistency'] = "Your sleep duration varies significantly. Try maintaining a consistent sleep schedule."
    elif consistency < 80:
        suggestions['suggestion_consistency'] = "Your sleep consistency is moderate. Stick to a regular bedtime and wake time."
    else:
        suggestions['suggestion_consistency'] = "Excellent sleep consistency! Keep maintaining your regular sleep schedule."
    
    # Bed use suggestion
    bed_use = metrics.get('bed_use', 0)
    if bed_use < 20:
        suggestions['suggestion_bed_use'] = "You're using your bed less than 5 hours per day. Are you getting enough rest?"
    elif bed_use > 50:
        suggestions['suggestion_bed_use'] = "You're spending more than 12 hours in bed. Consider if you're oversleeping or having sleep quality issues."
    else:
        suggestions['suggestion_bed_use'] = "Your bed usage time is appropriate for healthy sleep patterns."
    
    return suggestions


def calculate_and_update_dashboard(device_id: int, days_back: int = None) -> Dict[str, Any] | None:
    """
    Calculate all dashboard metrics for a device and update the database.
    
    Args:
        device_id: Device ID (integer primary key)
        days_back: Number of days to analyze (default: None = all data)
    
    Returns:
        Updated dashboard data or None if failed
    """
    print(f"\n{'=' * 60}")
    print(f"Calculating Dashboard for Device ID {device_id}")
    print(f"{'=' * 60}\n")
    
    # Get device
    device = get_device_by_id(device_id)
    if not device:
        print(f"❌ Device {device_id} not found")
        return None
    
    print(f"✅ Device: {device['name']} (ID: {device_id})")
    
    # Get raw occupancy data
    if days_back:
        print(f"📊 Fetching raw occupancy data for last {days_back} days...")
    else:
        print(f"📊 Fetching all raw occupancy data...")
    
    # Fetch occupancy readings
    occupancy_readings = get_all_raw_occupancy_by_device(device_id=device_id)
    
    if not occupancy_readings:
        print("❌ No occupancy data found")
        print(f"   Make sure you have occupancy readings in the database")
        return None
    
    # Filter readings to date range if specified
    if days_back:
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days_back)
        
        filtered_readings = [
            r for r in occupancy_readings
            if start_date <= datetime.fromisoformat(r['created_at'].replace('Z', '+00:00')) <= end_date
        ]
        
        print(f"✅ Found {len(filtered_readings)} occupancy readings in the last {days_back} days")
        
        if len(filtered_readings) == 0:
            print(f"\n⚠️  No data in the last {days_back} days.")
            print(f"   Total readings available: {len(occupancy_readings)}")
            if occupancy_readings:
                first_reading = min(occupancy_readings, key=lambda x: x['created_at'])
                last_reading = max(occupancy_readings, key=lambda x: x['created_at'])
                print(f"   Data range: {first_reading['created_at'][:10]} to {last_reading['created_at'][:10]}")
            return None
    else:
        filtered_readings = occupancy_readings
        
        # Calculate actual days period from data
        if filtered_readings:
            dates = [datetime.fromisoformat(r['created_at'].replace('Z', '+00:00')).date() 
                    for r in filtered_readings]
            min_date = min(dates)
            max_date = max(dates)
            days_back = (max_date - min_date).days + 1
            
            print(f"✅ Found {len(filtered_readings)} occupancy readings")
            print(f"   Date range: {min_date} to {max_date} ({days_back} days)")
    
    # Process raw occupancy data into sessions
    print("🔄 Processing occupancy data into sleep sessions...")
    sessions = process_occupancy_into_sessions(filtered_readings)
    
    if not sessions:
        print("❌ No sleep sessions detected")
        print(f"   Raw occupancy readings need to show occupied/vacant patterns")
        return None
    
    print(f"✅ Detected {len(sessions)} sleep sessions\n")
    
    # -------- Calculate metrics --------
    print("📈 Calculating metrics...")
    
    # Count interruptions
    total_intervals = count_interruptions(sessions)
    
    # Calculate average sleep
    avg_sleep = sum(s['duration_hours'] for s in sessions) / len(sessions) if sessions else 0
    
    # Count unique nights
    unique_nights = len(sessions)  # Now each session represents one night
    
    # Create metrics dictionary
    metrics = {
        'sleep_consistency': calculate_sleep_consistency(sessions),
        'bedtime_consistency': calculate_bedtime_consistency(sessions),
        'bed_use': calculate_bed_use(sessions, days_period=days_back),
        'daily_occupancy': calculate_daily_occupancy(sessions),
        'total_intervals': float(total_intervals),
        'total_nights': float(unique_nights),
        'avg_sleep_per_night': round(avg_sleep, 2)
    }
    
    # Generate suggestions
    suggestions = generate_suggestions(metrics)
    metrics.update(suggestions)
    
    # Display calculated metrics
    print("\n" + "=" * 60)
    print("📊 Calculated Metrics:")
    print("=" * 60)
    print(f"  Sleep Consistency Score: {metrics['sleep_consistency']}/100")
    print(f"  Bedtime Consistency Score: {metrics['bedtime_consistency']}/100")
    print(f"  Bed Use: {metrics['bed_use']}%")
    print(f"  Daily Occupancy: {metrics['daily_occupancy']} hours/day")
    print(f"  Total Interruptions: {int(metrics['total_intervals'])}")
    print(f"  Total Nights: {int(metrics['total_nights'])}")
    print(f"  Average Sleep: {metrics['avg_sleep_per_night']:.2f} hours/night")
    
    print("\n" + "=" * 60)
    print("💡 Suggestions:")
    print("=" * 60)
    print(f"  🌙 Awakening:\n     {suggestions['suggestion_awakening']}")
    print(f"  ⏱️  Average Sleep:\n     {suggestions['suggestion_avg_sleep']}")
    print(f"  📅 Consistency:\n     {suggestions['suggestion_consistency']}")
    print(f"  🛏️  Bed Use:\n     {suggestions['suggestion_bed_use']}")
    
    # Update dashboard in Supabase
    print("\n" + "=" * 60)
    print("💾 Updating dashboard in database...")
    print("=" * 60)
    
    result = create_or_update_dashboard(
        device_id=device_id,
        **metrics
    )
    
    if result:
        print("✅ Dashboard updated successfully!")
        print(f"   Last updated: {result.get('created_at', 'N/A')}")
    else:
        print("❌ Failed to update dashboard")
    
    print(f"\n{'=' * 60}\n")
    return result


if __name__ == "__main__":
    import sys
    
    # Get device ID from command line or use default
    device_id = int(sys.argv[1]) if len(sys.argv) > 1 else 9
    days = int(sys.argv[2]) if len(sys.argv) > 2 else None  # None = all data
    
    # Calculate the dashboard and write the data to Supabase
    calculate_and_update_dashboard(device_id, days_back=days)