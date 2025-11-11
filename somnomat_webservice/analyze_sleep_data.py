from supabase_api_client import get_sleep_sessions, get_dashboard
from calculate_dashboard import calculate_and_update_dashboard
import statistics
from datetime import datetime, timedelta
import sys

device_id = sys.argv[1] if len(sys.argv) > 1 else "esp32-a1"

# Get all sessions
print(f"Analyzing sleep data for {device_id}...\n")
sessions = get_sleep_sessions(device_id=device_id, limit=1000)

if not sessions:
    print("No data found")
    exit()

# Extract metrics
durations = [s['duration_hours'] for s in sessions if s['duration_hours']]
qualities = [s['sleep_quality_score'] for s in sessions if s['sleep_quality_score']]
interruptions = [s['interruptions'] for s in sessions if s['interruptions'] is not None]

# Calculate statistics
print("Sleep Statistics:")
print(f"  Total sessions: {len(sessions)}")
print(f"\n  Duration:")
print(f"    Average: {statistics.mean(durations):.2f} hours")
print(f"    Min: {min(durations):.2f} hours")
print(f"    Max: {max(durations):.2f} hours")
print(f"\n  Quality Score:")
print(f"    Average: {statistics.mean(qualities):.1f}/100")
print(f"    Best: {max(qualities)}/100")
print(f"    Worst: {min(qualities)}/100")
print(f"\n  Interruptions:")
print(f"    Average: {statistics.mean(interruptions):.1f}")
print(f"    Total nights with 0 interruptions: {interruptions.count(0)}")

# Find best and worst nights
best = max(sessions, key=lambda s: s['sleep_quality_score'] or 0)
worst = min(sessions, key=lambda s: s['sleep_quality_score'] or 100)

print(f"\n  Best night:")
print(f"    Date: {best['session_start']}")
print(f"    Quality: {best['sleep_quality_score']}/100")
print(f"    Duration: {best['duration_hours']} hours")

print(f"\n  Worst night:")
print(f"    Date: {worst['session_start']}")
print(f"    Quality: {worst['sleep_quality_score']}/100")
print(f"    Duration: {worst['duration_hours']} hours")

# Calculate and update dashboard
print("\n" + "=" * 60)
print("Updating Dashboard Metrics...")
print("=" * 60)
calculate_and_update_dashboard(device_id)

print("\n✅ Analysis complete!")