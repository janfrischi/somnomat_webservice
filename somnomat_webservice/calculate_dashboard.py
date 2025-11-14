"""
Calculate dashboard metrics from raw occupancy data and store in sleep_dashboard table.
"""
from supabase_api_client_somnomat import (
    get_raw_occupancy_by_device,
    get_device_by_id,
    create_or_update_dashboard
)
import statistics
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Tuple


def process_occupancy_into_sessions(occupancy_readings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Convert raw occupancy readings into sleep sessions.
    A session starts when occupied=True and ends when occupied=False.
    """
    if not occupancy_readings:
        return []
    
    sessions = []
    current_session_start = None
    
    # Sort by timestamp
    sorted_readings = sorted(occupancy_readings, key=lambda x: x['created_at'])
    
    for reading in sorted_readings:
        occupied = reading['occupied']
        timestamp = datetime.fromisoformat(reading['created_at'].replace('Z', '+00:00'))
        
        if occupied and current_session_start is None:
            # Start of a new session
            current_session_start = timestamp
        elif not occupied and current_session_start is not None:
            # End of current session
            session_end = timestamp
            duration_seconds = (session_end - current_session_start).total_seconds()
            duration_hours = duration_seconds / 3600
            
            # Only count sessions longer than 1 hour
            if duration_hours >= 1.0:
                sessions.append({
                    'session_start': current_session_start,
                    'session_end': session_end,
                    'duration_hours': duration_hours,
                    'duration_min': duration_hours * 60
                })
            
            current_session_start = None
    
    # Handle case where last session is still ongoing
    if current_session_start is not None:
        session_end = datetime.now(timezone.utc)
        duration_seconds = (session_end - current_session_start).total_seconds()
        duration_hours = duration_seconds / 3600
        
        if duration_hours >= 1.0:
            sessions.append({
                'session_start': current_session_start,
                'session_end': session_end,
                'duration_hours': duration_hours,
                'duration_min': duration_hours * 60
            })
    
    return sessions


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
    An interruption is when there are multiple sessions per night.
    """
    if not sessions:
        return 0
    
    # Group sessions by date
    sessions_by_date: Dict[Any, int] = {}
    for s in sessions:
        if s.get('session_start'):
            date = s['session_start'].date()
            sessions_by_date[date] = sessions_by_date.get(date, 0) + 1
    
    # Total interruptions = total sessions - total nights
    # (e.g., 3 sessions on one night = 2 interruptions)
    total_interruptions = sum(max(0, count - 1) for count in sessions_by_date.values())
    
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


def calculate_and_update_dashboard(device_id: int, days_back: int = 30) -> Dict[str, Any] | None:
    """
    Calculate all dashboard metrics for a device and update the database.
    
    Args:
        device_id: Device ID (integer primary key)
        days_back: Number of days to analyze (default: 30)
    
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
    print(f"📊 Fetching raw occupancy data for last {days_back} days...")
    
    # Calculate date range
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days_back)
    
    occupancy_readings = get_raw_occupancy_by_device(
        device_id=device_id,
        limit=10000  # Get enough data for analysis
    )
    
    if not occupancy_readings:
        print("❌ No occupancy data found")
        print(f"   Make sure you have occupancy readings in the database")
        return None
    
    # Filter readings to date range
    filtered_readings = [
        r for r in occupancy_readings
        if start_date <= datetime.fromisoformat(r['created_at'].replace('Z', '+00:00')) <= end_date
    ]
    
    print(f"✅ Found {len(filtered_readings)} occupancy readings in the last {days_back} days\n")
    
    # Process into sessions
    print("🔄 Processing occupancy data into sleep sessions...")
    sessions = process_occupancy_into_sessions(filtered_readings)
    
    if not sessions:
        print("❌ No sleep sessions detected")
        print(f"   Raw occupancy readings need to show occupied/vacant patterns")
        return None
    
    print(f"✅ Detected {len(sessions)} sleep sessions\n")
    
    # Calculate metrics
    print("📈 Calculating metrics...")
    
    # Count interruptions
    total_intervals = count_interruptions(sessions)
    
    # Calculate average sleep
    avg_sleep = sum(s['duration_hours'] for s in sessions) / len(sessions) if sessions else 0
    
    # Count unique nights
    unique_nights = len(set(s['session_start'].date() for s in sessions))
    
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
    device_id = int(sys.argv[1]) if len(sys.argv) > 1 else 9  # Default to test device
    days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    
    calculate_and_update_dashboard(device_id, days_back=days)