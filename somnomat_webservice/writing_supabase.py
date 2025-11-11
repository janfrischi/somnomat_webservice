from supabase_api_client import (
    create_sleep_session,
    get_sleep_sessions,
    get_session_by_id,
    update_sleep_session,
    delete_sleep_session,
    get_sessions_by_date_range,
    get_average_sleep_quality
)
from datetime import datetime, timezone, timedelta

print("=" * 60)
print("Testing Supabase API for Sleep Sessions")
print("=" * 60)

# Test 1: Create a new sleep session
print("\n1. Creating a new sleep session...")
now = datetime.now(timezone.utc)
session_start = (now - timedelta(hours=8)).isoformat()
session_end = now.isoformat()

session = create_sleep_session(
    device_id="esp32-a1",
    session_start=session_start,
    session_end=session_end,
    duration_hours=8.0,
    sleep_quality_score=85,
    interruptions=2,
    notes="Good night's sleep with minimal interruptions"
)

if session:
    print(f"✅ Session created with ID: {session['id']}")
    print(f"   Device: {session['device_id']}")
    print(f"   Duration: {session['duration_hours']} hours")
    print(f"   Quality Score: {session['sleep_quality_score']}")
    session_id = session['id']
else:
    print("❌ Failed to create session")
    exit(1)

# Test 2: Get all sessions for a device
print("\n2. Fetching all sessions for device esp32-a1...")
sessions = get_sleep_sessions(device_id="esp32-a1", limit=5)
print(f"✅ Found {len(sessions)} sessions")
for s in sessions:
    print(f"   - Session {s['id']}: Quality {s['sleep_quality_score']}, Duration {s['duration_hours']}h")

# Test 3: Get a specific session
print(f"\n3. Fetching session {session_id}...")
retrieved_session = get_session_by_id(session_id)
if retrieved_session:
    print(f"✅ Retrieved session {retrieved_session['id']}")
    print(f"   Notes: {retrieved_session['notes']}")

# Test 4: Update a session
print(f"\n4. Updating session {session_id}...")
updated = update_sleep_session(
    session_id,
    sleep_quality_score=90,
    notes="Updated: Actually slept really well!"
)
if updated:
    print(f"✅ Session updated")
    print(f"   New quality score: {updated['sleep_quality_score']}")
    print(f"   New notes: {updated['notes']}")

# Test 5: Get sessions by date range
print("\n5. Fetching sessions from last 7 days...")
week_ago = (now - timedelta(days=7)).isoformat()
recent_sessions = get_sessions_by_date_range(
    device_id="esp32-a1",
    start_date=week_ago,
    end_date=now.isoformat()
)
print(f"✅ Found {len(recent_sessions)} sessions in the last week")

# Test 6: Calculate average sleep quality
print("\n6. Calculating average sleep quality...")
avg_quality = get_average_sleep_quality("esp32-a1")
if avg_quality:
    print(f"✅ Average sleep quality: {avg_quality:.1f}")

# # Test 7: Delete the test session
# print(f"\n7. Deleting test session {session_id}...")
# deleted = delete_sleep_session(session_id)
# if deleted:
#     print(f"✅ Session {session_id} deleted")
# else:
#     print(f"❌ Failed to delete session")

print("\n" + "=" * 60)
print("🎉 All Supabase API tests completed!")
print("=" * 60)