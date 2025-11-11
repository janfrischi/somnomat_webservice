"""
View dashboard metrics for a device.
"""
from supabase_api_client import get_dashboard_with_device, get_device_by_string_id
import sys

def view_dashboard(device_string_id: str):
    """Display dashboard metrics for a device."""
    
    # Get device
    device = get_device_by_string_id(device_string_id)
    if not device:
        print(f"❌ Device {device_string_id} not found")
        return
    
    # Get dashboard
    dashboard = get_dashboard_with_device(device['id'])
    
    if not dashboard:
        print(f"❌ No dashboard data found for {device_string_id}")
        print("   Run: python calculate_dashboard.py {device_string_id}")
        return
    
    print("\n" + "=" * 60)
    print(f"Sleep Dashboard for {device_string_id}")
    print("=" * 60)
    
    print(f"\n📊 Metrics:")
    print(f"  Sleep Consistency:    {dashboard['sleep_consistency']}/100")
    print(f"  Bedtime Consistency:  {dashboard['bedtime_consistency']}/100")
    print(f"  Bed Usage:            {dashboard['bed_use']}%")
    print(f"  Daily Occupancy:      {dashboard['daily_occupany']} hours/day")
    print(f"  Total Nights:         {dashboard['total_nights']}")
    print(f"  Average Sleep:        {dashboard['avg_sleep_per_night']:.2f} hours/night")
    print(f"  Total Interruptions:  {dashboard['total_intervals']}")
    
    print(f"\n💡 Suggestions:")
    print(f"  🌙 Awakening:\n     {dashboard['suggestion_awakening']}")
    print(f"\n  ⏱️  Average Sleep:\n     {dashboard['suggestion_avg_sleep']}")
    print(f"\n  📅 Consistency:\n     {dashboard['suggestion_consistency']}")
    print(f"\n  🛏️  Bed Use:\n     {dashboard['suggestion_bed_use']}")
    
    print(f"\n📅 Last Updated: {dashboard['created_at']}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    device_id = sys.argv[1] if len(sys.argv) > 1 else "esp32-a1"
    view_dashboard(device_id)