"""Create sample sleep sessions for testing."""
from supabase_api_client import create_sleep_session
from datetime import datetime, timedelta, timezone
import random

device_id = "esp32-a1"
print(f"Creating sample sleep sessions for {device_id}...\n")

# Create 30 nights of sleep data
now = datetime.now(timezone.utc)

for i in range(30):
    # Bedtime around 10 PM ± 1 hour
    bedtime_hour = 22 + random.uniform(-1, 1)
    session_start = (now - timedelta(days=i)).replace(
        hour=int(bedtime_hour),
        minute=int((bedtime_hour % 1) * 60),
        second=0
    )
    
    # Sleep duration 6-9 hours
    duration = random.uniform(6, 9)
    session_end = session_start + timedelta(hours=duration)
    
    # Quality score 60-95
    quality = random.randint(60, 95)
    
    # Interruptions 0-5
    interruptions = random.randint(0, 5)
    
    session = create_sleep_session(
        device_id=device_id,
        session_start=session_start.isoformat(),
        session_end=session_end.isoformat(),
        duration_hours=round(duration, 2),
        sleep_quality_score=quality,
        interruptions=interruptions,
        notes=f"Night {30-i}"
    )
    
    if session:
        print(f"✅ Created session {30-i}: {duration:.1f}h, Quality {quality}/100, {interruptions} interruptions")
    else:
        print(f"❌ Failed to create session {30-i}")

print(f"\n✅ Created 30 sleep sessions for {device_id}")