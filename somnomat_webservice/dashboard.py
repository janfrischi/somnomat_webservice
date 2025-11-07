import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000/api/v1"

def fetch_all_device_data(device_id: str):
    """Fetch all readings for a device with automatic pagination."""
    all_items = []
    offset = 0
    limit = 1000
    
    print(f"Fetching data for device: {device_id}")
    
    while True:
        params = {
            "device_id": device_id,
            "limit": limit,
            "offset": offset
        }
        response = requests.get(f"{BASE_URL}/readings", params=params)
        response.raise_for_status()
        data = response.json()
        
        all_items.extend(data['items'])
        print(f"Progress: {len(all_items)}/{data['total']}")
        
        if offset + len(data['items']) >= data['total']:
            break
        
        offset += limit
    
    return all_items

def create_dashboard(device_id: str = "esp32-a1"):
    """Create an interactive dashboard with health metrics."""
    
    # Fetch data
    readings = fetch_all_device_data(device_id)
    
    if not readings:
        print(f"No data found for device {device_id}")
        return
    
    # Sort by timestamp
    readings.sort(key=lambda x: x['timestamp'])
    
    # Extract data
    timestamps = [datetime.fromisoformat(r['timestamp'].replace('Z', '+00:00')) for r in readings]
    heartrates = [r['heartrate'] for r in readings]
    hrvs = [r['hrv'] for r in readings]
    time_in_beds = [r['time_in_bed'] for r in readings]
    total_use_times = [r['total_use_time'] for r in readings]
    
    # Create subplots (2x2 grid)
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            'Heart Rate (bpm)',
            'Heart Rate Variability (ms)',
            'Time in Bed (hours)',
            'Total Use Time (hours)'
        ),
        vertical_spacing=0.12,
        horizontal_spacing=0.1
    )
    
    # Add Heart Rate trace
    fig.add_trace(
        go.Scatter(
            x=timestamps,
            y=heartrates,
            mode='lines+markers',
            name='Heart Rate',
            line=dict(color='#FF6B6B', width=2),
            marker=dict(size=4),
            hovertemplate='<b>Time:</b> %{x}<br><b>HR:</b> %{y:.1f} bpm<extra></extra>'
        ),
        row=1, col=1
    )
    
    # Add HRV trace
    fig.add_trace(
        go.Scatter(
            x=timestamps,
            y=hrvs,
            mode='lines+markers',
            name='HRV',
            line=dict(color='#4ECDC4', width=2),
            marker=dict(size=4),
            hovertemplate='<b>Time:</b> %{x}<br><b>HRV:</b> %{y:.1f} ms<extra></extra>'
        ),
        row=1, col=2
    )
    
    # Add Time in Bed trace
    fig.add_trace(
        go.Scatter(
            x=timestamps,
            y=time_in_beds,
            mode='lines+markers',
            name='Time in Bed',
            line=dict(color='#95E1D3', width=2),
            marker=dict(size=4),
            hovertemplate='<b>Time:</b> %{x}<br><b>Bed:</b> %{y:.1f} h<extra></extra>'
        ),
        row=2, col=1
    )
    
    # Add Total Use Time trace
    fig.add_trace(
        go.Scatter(
            x=timestamps,
            y=total_use_times,
            mode='lines+markers',
            name='Total Use Time',
            line=dict(color='#F38181', width=2),
            marker=dict(size=4),
            hovertemplate='<b>Time:</b> %{x}<br><b>Use:</b> %{y:.1f} h<extra></extra>'
        ),
        row=2, col=2
    )
    
    # Calculate statistics
    avg_hr = sum(h for h in heartrates if h) / len([h for h in heartrates if h]) if heartrates else 0
    avg_hrv = sum(h for h in hrvs if h) / len([h for h in hrvs if h]) if hrvs else 0
    avg_bed = sum(t for t in time_in_beds if t) / len([t for t in time_in_beds if t]) if time_in_beds else 0
    avg_use = sum(t for t in total_use_times if t) / len([t for t in total_use_times if t]) if total_use_times else 0
    
    # Update layout
    fig.update_layout(
        title={
            'text': f'Health Metrics Dashboard - Device: {device_id}<br>' +
                    f'<sub>Avg HR: {avg_hr:.1f} bpm | Avg HRV: {avg_hrv:.1f} ms | ' +
                    f'Avg Bed Time: {avg_bed:.1f} h | Avg Use Time: {avg_use:.1f} h</sub>',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20}
        },
        showlegend=False,
        height=800,
        template='plotly_white',
        hovermode='x unified'
    )
    
    # Update axes labels
    fig.update_xaxes(title_text="Time", row=1, col=1)
    fig.update_xaxes(title_text="Time", row=1, col=2)
    fig.update_xaxes(title_text="Time", row=2, col=1)
    fig.update_xaxes(title_text="Time", row=2, col=2)
    
    fig.update_yaxes(title_text="bpm", row=1, col=1)
    fig.update_yaxes(title_text="ms", row=1, col=2)
    fig.update_yaxes(title_text="hours", row=2, col=1)
    fig.update_yaxes(title_text="hours", row=2, col=2)
    
    # Show the dashboard
    fig.show()
    
    # Optionally save to HTML
    output_file = f"dashboard_{device_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    fig.write_html(output_file)
    print(f"\n✅ Dashboard saved to: {output_file}")
    print(f"📊 Total readings: {len(readings)}")
    print(f"📈 Statistics:")
    print(f"   - Average Heart Rate: {avg_hr:.1f} bpm")
    print(f"   - Average HRV: {avg_hrv:.1f} ms")
    print(f"   - Average Time in Bed: {avg_bed:.1f} hours")
    print(f"   - Average Total Use Time: {avg_use:.1f} hours")

if __name__ == "__main__":
    # You can change the device_id here or pass it as an argument
    import sys
    
    device_id = sys.argv[1] if len(sys.argv) > 1 else "esp32-a1"
    create_dashboard(device_id)