"""
Calculate dashboard metrics from sleep sessions and store in sleep_dashboard table.
"""
from supabase_api_client import (
    get_sleep_sessions,
    get_device_by_string_id,
    create_or_update_dashboard
)
import statistics
from datetime import datetime, timedelta

def calculate_sleep_consistency(sessions):
    """
    Calculate sleep consistency score (0-100).
    Based on standard deviation of sleep duration.
    Lower std dev = higher consistency.
    """
    if len(sessions) < 2:
        return None
    
    durations = [s['duration_hours'] for s in sessions if s['duration_hours']]
    if not durations:
        return None
    
    std_dev = statistics.stdev(durations)
    # Convert to 0-100 score (assuming std dev of 0 = 100, std dev of 3+ hours = 0)
    consistency = max(0, 100 - (std_dev * 33.33))
    return round(consistency, 2)


def calculate_bedtime_consistency(sessions):
    """
    Calculate bedtime consistency score (0-100).
    Based on standard deviation of bedtime hours.
    """
    if len(sessions) < 2:
        return None
    
    # Extract hour of bedtime
    bedtimes = []
    for s in sessions:
        if s['session_start']:
            dt = datetime.fromisoformat(s['session_start'].replace('Z', '+00:00'))
            # Convert to hour of day (0-23)
            bedtimes.append(dt.hour + dt.minute / 60.0)
    
    if not bedtimes:
        return None
    
    std_dev = statistics.stdev(bedtimes)
    # Assuming std dev of 0 = 100, std dev of 4+ hours = 0
    consistency = max(0, 100 - (std_dev * 25))
    return round(consistency, 2)


def calculate_bed_use(sessions, days_period=7):
    """
    Calculate bed usage percentage.
    Total hours in bed / total hours in period.
    """
    if not sessions:
        return None
    
    total_hours_in_bed = sum(s['duration_hours'] for s in sessions if s['duration_hours'])
    total_hours_in_period = days_period * 24
    
    bed_use_percent = (total_hours_in_bed / total_hours_in_period) * 100
    return round(bed_use_percent, 2)


def calculate_daily_occupancy(sessions):
    """
    Calculate average daily bed occupancy (hours per day).
    """
    if not sessions:
        return None
    
    # Get date range
    dates = set()
    for s in sessions:
        if s['session_start']:
            dt = datetime.fromisoformat(s['session_start'].replace('Z', '+00:00'))
            dates.add(dt.date())
    
    if not dates:
        return None
    
    days = len(dates)
    total_hours = sum(s['duration_hours'] for s in sessions if s['duration_hours'])
    
    return round(total_hours / days, 2)


def generate_suggestions(metrics):
    """Generate personalized suggestions based on metrics."""
    suggestions = {}
    
    # Awakening suggestion
    if metrics.get('total_intervals', 0) > 3:
        suggestions['suggestion_awakening'] = "You're waking up frequently. Consider reviewing your sleep environment (temperature, noise, light)."
    else:
        suggestions['suggestion_awakening'] = "Good job! You're sleeping through the night with minimal interruptions."
    
    # Average sleep suggestion
    avg_sleep = metrics.get('avg_sleep_per_night', 0)
    if avg_sleep < 6:
        suggestions['suggestion_avg_sleep'] = "You're getting less than 6 hours of sleep. Aim for 7-9 hours for optimal health."
    elif avg_sleep < 7:
        suggestions['suggestion_avg_sleep'] = "Try to increase your sleep time to at least 7 hours per night."
    elif avg_sleep > 9:
        suggestions['suggestion_avg_sleep'] = "You're sleeping more than 9 hours. This might indicate poor sleep quality or other health issues."
    else:
        suggestions['suggestion_avg_sleep'] = "Great! You're getting the recommended 7-9 hours of sleep."
    
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


def calculate_and_update_dashboard(device_string_id: str, days_back: int = 30):
    """
    Calculate all dashboard metrics for a device and update the database.
    
    Args:
        device_string_id: Device ID string (e.g., 'esp32-a1')
        days_back: Number of days to analyze (default: 30)
    """
    print(f"\n{'=' * 60}")
    print(f"Calculating Dashboard for {device_string_id}")
    print(f"{'=' * 60}\n")
    
    # Get device
    device = get_device_by_string_id(device_string_id)
    if not device:
        print(f"❌ Device {device_string_id} not found")
        return None
    
    device_internal_id = device['id']
    print(f"Device: {device['device_id']} (Internal ID: {device_internal_id})")
    
    # Get sessions from last N days
    sessions = get_sleep_sessions(device_id=device_string_id, limit=1000)
    
    if not sessions:
        print("❌ No sleep sessions found")
        return None
    
    print(f"Found {len(sessions)} sleep sessions\n")
    
    # Calculate metrics
    metrics = {
        'sleep_consistency': calculate_sleep_consistency(sessions),
        'bedtime_consistency': calculate_bedtime_consistency(sessions),
        'bed_use': calculate_bed_use(sessions, days_period=days_back),
        'daily_occupancy': calculate_daily_occupancy(sessions),
        'total_intervals': sum(s['interruptions'] for s in sessions if s['interruptions'] is not None),
        'total_nights': len(sessions),
        'avg_sleep_per_night': sum(s['duration_hours'] for s in sessions if s['duration_hours']) / len([s for s in sessions if s['duration_hours']]) if sessions else None
    }
    
    # Generate suggestions
    suggestions = generate_suggestions(metrics)
    metrics.update(suggestions)
    
    # Display calculated metrics
    print("Calculated Metrics:")
    print(f"  Sleep Consistency Score: {metrics['sleep_consistency']}/100")
    print(f"  Bedtime Consistency Score: {metrics['bedtime_consistency']}/100")
    print(f"  Bed Use: {metrics['bed_use']}%")
    print(f"  Daily Occupancy: {metrics['daily_occupancy']} hours/day")
    print(f"  Total Interruptions: {metrics['total_intervals']}")
    print(f"  Total Nights: {metrics['total_nights']}")
    print(f"  Average Sleep: {metrics['avg_sleep_per_night']:.2f} hours/night")
    
    print("\nSuggestions:")
    print(f"  Awakening: {suggestions['suggestion_awakening']}")
    print(f"  Avg Sleep: {suggestions['suggestion_avg_sleep']}")
    print(f"  Consistency: {suggestions['suggestion_consistency']}")
    print(f"  Bed Use: {suggestions['suggestion_bed_use']}")
    
    # Update dashboard in Supabase
    print("\nUpdating dashboard in database...")
    result = create_or_update_dashboard(
        device_id=device_internal_id,
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
    device_id = sys.argv[1] if len(sys.argv) > 1 else "esp32-a1"
    days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    
    calculate_and_update_dashboard(device_id, days_back=days)