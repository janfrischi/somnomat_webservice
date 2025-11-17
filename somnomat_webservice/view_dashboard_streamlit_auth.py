"""Streamlit dashboard with authentication - Complete version with all visualizations."""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta, timezone
from supabase_auth_client import SupabaseAuthClient
from supabase_api_client_somnomat import (
    get_device_by_id,
    get_raw_occupancy_by_device,
    get_dashboard
)
from calculate_dashboard import process_occupancy_into_sessions
from PIL import Image
import os

st.set_page_config(page_title="Sleep Dashboard", layout="wide", page_icon="🛏️")

# Initialize auth client
if 'auth_client' not in st.session_state:
    st.session_state.auth_client = SupabaseAuthClient()

auth = st.session_state.auth_client

# Check authentication
user = auth.get_current_user()

if not user:
    # ==================== LOGIN/SIGNUP PAGE ====================
    
    # Load logo for login page
    try:
        logo_path = os.path.join(os.path.dirname(__file__), "calmea.png")
        logo = Image.open(logo_path)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image(logo, width=300)
    except FileNotFoundError:
        pass
    
    st.title("🔐 Somnomat Login")
    st.markdown("---")
    
    tab1, tab2, tab3 = st.tabs(["🔑 Sign In", "✨ Sign Up", "🔄 Reset Password"])
    
    with tab1:
        st.markdown("### Sign In to Your Account")
        with st.form("signin_form"):
            email = st.text_input("Email", placeholder="user@example.com")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Sign In", use_container_width=True)
            
            if submit:
                if not email or not password:
                    st.error("❌ Please fill in all fields")
                else:
                    result = auth.sign_in(email, password)
                    if "user" in result:
                        st.success("✅ Signed in successfully!")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(f"❌ {result.get('error', 'Sign in failed')}")
    
    with tab2:
        st.markdown("### Create a New Account")
        with st.form("signup_form"):
            email = st.text_input("Email", placeholder="user@example.com", key="signup_email")
            password = st.text_input("Password (min 6 characters)", type="password", key="signup_password")
            password_confirm = st.text_input("Confirm Password", type="password")
            name = st.text_input("Name (optional)")
            submit = st.form_submit_button("Sign Up", use_container_width=True)
            
            if submit:
                if not email or not password:
                    st.error("❌ Please fill in all required fields")
                elif len(password) < 6:
                    st.error("❌ Password must be at least 6 characters")
                elif password != password_confirm:
                    st.error("❌ Passwords do not match")
                else:
                    metadata = {"name": name} if name else {}
                    result = auth.sign_up(email, password, metadata)
                    if "user" in result:
                        st.success("✅ Account created! Please check your email to verify.")
                        st.info("📧 A verification email has been sent. Click the link to activate your account.")
                    else:
                        st.error(f"❌ {result.get('error', 'Sign up failed')}")
    
    with tab3:
        st.markdown("### Reset Your Password")
        with st.form("reset_form"):
            email = st.text_input("Email", placeholder="user@example.com", key="reset_email")
            submit = st.form_submit_button("Send Reset Email", use_container_width=True)
            
            if submit:
                if not email:
                    st.error("❌ Please enter your email")
                else:
                    if auth.reset_password_email(email):
                        st.success("✅ Password reset email sent! Check your inbox.")
                    else:
                        st.error("❌ Failed to send reset email")

else:
    # ==================== AUTHENTICATED DASHBOARD ====================
    
    # Load logo for sidebar
    try:
        logo_path = os.path.join(os.path.dirname(__file__), "calmea.png")
        logo = Image.open(logo_path)
        st.sidebar.image(logo, width='stretch')
        st.sidebar.divider()
    except FileNotFoundError:
        st.sidebar.warning("Logo not found")
    
    # User info and sign out
    user_name = user.user_metadata.get('name', user.email.split('@')[0]) if hasattr(user, 'user_metadata') else user.email.split('@')[0]
    st.sidebar.success(f"👤 {user_name}")
    st.sidebar.caption(f"📧 {user.email}")
    
    if st.sidebar.button("🚪 Sign Out", use_container_width=True):
        auth.sign_out()
        st.rerun()
    
    st.sidebar.divider()
    
    # Get user's devices
    user_devices = auth.get_user_devices()
    
    if not user_devices:
        # ==================== NO DEVICES ====================
        st.title("📱 Welcome to Somnomat!")
        st.markdown("### No devices linked to your account yet")
        
        st.info("""
        **To get started:**
        
        1. Register a new device using the CLI:
           ```bash
           python setup_device.py "My Bedroom"
           ```
        
        2. Or link an existing device:
           ```bash
           python auth_cli.py link <device_id>
           ```
        
        3. Refresh this page to see your devices
        """)
        
        if st.button("🔄 Refresh Page"):
            st.rerun()
    
    else:
        # ==================== DEVICE SELECTION ====================
        st.sidebar.title("Device Selection")
        
        device_options = {
            f"{d['devices']['name']} (ID: {d['device_id']})": d['device_id'] 
            for d in user_devices
        }
        
        selected = st.sidebar.selectbox("Select Device", list(device_options.keys()))
        device_id = device_options[selected]
        
        # Get device role
        current_device = next(d for d in user_devices if d['device_id'] == device_id)
        user_role = current_device['role']
        
        st.sidebar.caption(f"Role: {user_role.upper()}")
        
        st.sidebar.divider()
        
        # Comparison Mode
        st.sidebar.subheader("🔀 Compare")
        comparison_mode = st.sidebar.checkbox("Enable Comparison")
        
        compare_device_id = None
        compare_device = None
        if comparison_mode and len(user_devices) > 1:
            other_devices = {k: v for k, v in device_options.items() if v != device_id}
            if other_devices:
                compare_selected = st.sidebar.selectbox(
                    "Compare with Device",
                    list(other_devices.keys()),
                    key="compare_device"
                )
                compare_device_id = other_devices[compare_selected]
                compare_device = get_device_by_id(compare_device_id)
        elif comparison_mode and len(user_devices) == 1:
            st.sidebar.warning("⚠️ You need at least 2 devices to compare")
            comparison_mode = False
        
        st.sidebar.divider()
        
        # Date Range Selector
        st.sidebar.subheader("📅 Date Range")
        date_range_option = st.sidebar.selectbox(
            "Select Period",
            ["Last 7 Days", "Last 30 Days", "Last 90 Days", "Custom Range"]
        )
        
        if date_range_option == "Custom Range":
            start_date = st.sidebar.date_input(
                "Start Date",
                value=datetime.now().date() - timedelta(days=30)
            )
            end_date = st.sidebar.date_input(
                "End Date",
                value=datetime.now().date()
            )
            days_back = (end_date - start_date).days
        else:
            days_map = {
                "Last 7 Days": 7,
                "Last 30 Days": 30,
                "Last 90 Days": 90
            }
            days_back = days_map[date_range_option]
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days_back)
        
        st.sidebar.caption(f"Analyzing {days_back} days of data")
        
        # ==================== MAIN DASHBOARD ====================
        
        # Load device data
        device = get_device_by_id(device_id)
        if not device:
            st.error(f"Device {device_id} not found")
            st.stop()
        
        # Header
        if comparison_mode and compare_device:
            col1, col2 = st.columns(2)
            with col1:
                st.title(f"Sleep Dashboard - {device['name']}")
                st.caption(f"Device ID: {device_id} | MAC: {device.get('mac', 'N/A')}")
            with col2:
                st.title(f"Sleep Dashboard - {compare_device['name']}")
                st.caption(f"Device ID: {compare_device_id} | MAC: {compare_device.get('mac', 'N/A')}")
        else:
            st.title(f"Sleep Dashboard - {device['name']}")
            st.caption(f"Device ID: {device_id} | MAC: {device.get('mac', 'N/A')} | Your Role: {user_role}")
        
        # Custom CSS for smaller metrics
        st.markdown("""
        <style>
            [data-testid="stMetricValue"] {
                font-size: 20px;
            }
            [data-testid="stMetricLabel"] {
                font-size: 14px;
            }
        </style>
        """, unsafe_allow_html=True)
        
        # Device Information
        st.markdown("### 📱 Device Information")
        
        if comparison_mode and compare_device:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**{device['name']}**")
                sub_col1, sub_col2 = st.columns(2)
                with sub_col1:
                    st.metric("Board Type", device.get('boardtype', 'N/A'))
                    st.metric("MAC Address", device.get('mac', 'N/A'))
                with sub_col2:
                    st.metric("Hardware Version", device.get('hardware_version', 'N/A'))
            
            with col2:
                st.markdown(f"**{compare_device['name']}**")
                sub_col1, sub_col2 = st.columns(2)
                with sub_col1:
                    st.metric("Board Type", compare_device.get('boardtype', 'N/A'))
                    st.metric("MAC Address", compare_device.get('mac', 'N/A'))
                with sub_col2:
                    st.metric("Hardware Version", compare_device.get('hardware_version', 'N/A'))
        else:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Device Name", device['name'])
            with col2:
                st.metric("Board Type", device.get('boardtype', 'N/A'))
            with col3:
                st.metric("MAC Address", device.get('mac', 'N/A'))
            with col4:
                st.metric("Hardware Version", device.get('hardware_version', 'N/A'))
        
        st.divider()
        
        # Load dashboard metrics
        dashboard = get_dashboard(device_id)
        compare_dashboard = get_dashboard(compare_device_id) if compare_device else None
        
        # ==================== METRICS DISPLAY ====================
        
        if comparison_mode and compare_device and dashboard and compare_dashboard:
            st.markdown("### 📊 Sleep Metrics Comparison")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**{device['name']}**")
                sub1, sub2, sub3, sub4 = st.columns(4)
                with sub1:
                    st.metric("Sleep Consistency", f"{dashboard['sleep_consistency']:.1f}/100")
                with sub2:
                    st.metric("Bedtime Consistency", f"{dashboard['bedtime_consistency']:.1f}/100")
                with sub3:
                    st.metric("Bed Usage", f"{dashboard['bed_use']:.1f}%")
                with sub4:
                    st.metric("Avg Sleep/Night", f"{dashboard['avg_sleep_per_night']:.1f} hrs")
                
                sub5, sub6, sub7 = st.columns(3)
                with sub5:
                    st.metric("Daily Occupancy", f"{dashboard['daily_occupancy']:.1f} hrs/day")
                with sub6:
                    st.metric("Total Nights", f"{int(dashboard['total_nights'])}")
                with sub7:
                    st.metric("Interruptions", f"{int(dashboard['total_intervals'])}")
            
            with col2:
                st.markdown(f"**{compare_device['name']}**")
                sub1, sub2, sub3, sub4 = st.columns(4)
                with sub1:
                    delta1 = compare_dashboard['sleep_consistency'] - dashboard['sleep_consistency']
                    st.metric("Sleep Consistency", f"{compare_dashboard['sleep_consistency']:.1f}/100", 
                             delta=f"{delta1:+.1f}")
                with sub2:
                    delta2 = compare_dashboard['bedtime_consistency'] - dashboard['bedtime_consistency']
                    st.metric("Bedtime Consistency", f"{compare_dashboard['bedtime_consistency']:.1f}/100",
                             delta=f"{delta2:+.1f}")
                with sub3:
                    delta3 = compare_dashboard['bed_use'] - dashboard['bed_use']
                    st.metric("Bed Usage", f"{compare_dashboard['bed_use']:.1f}%",
                             delta=f"{delta3:+.1f}%")
                with sub4:
                    delta4 = compare_dashboard['avg_sleep_per_night'] - dashboard['avg_sleep_per_night']
                    st.metric("Avg Sleep/Night", f"{compare_dashboard['avg_sleep_per_night']:.1f} hrs",
                             delta=f"{delta4:+.1f} hrs")
                
                sub5, sub6, sub7 = st.columns(3)
                with sub5:
                    delta5 = compare_dashboard['daily_occupancy'] - dashboard['daily_occupancy']
                    st.metric("Daily Occupancy", f"{compare_dashboard['daily_occupancy']:.1f} hrs/day",
                             delta=f"{delta5:+.1f} hrs")
                with sub6:
                    delta6 = int(compare_dashboard['total_nights']) - int(dashboard['total_nights'])
                    st.metric("Total Nights", f"{int(compare_dashboard['total_nights'])}",
                             delta=f"{delta6:+d}")
                with sub7:
                    delta7 = int(compare_dashboard['total_intervals']) - int(dashboard['total_intervals'])
                    st.metric("Interruptions", f"{int(compare_dashboard['total_intervals'])}",
                             delta=f"{delta7:+d}", delta_color="inverse")
            
            st.divider()
            
            # Comparison Bar Chart
            st.markdown("### 📊 Metrics Comparison Chart")
            
            fig_comparison = go.Figure()
            
            fig_comparison.add_trace(go.Bar(
                name=device['name'],
                x=['Sleep\nConsistency', 'Bedtime\nConsistency', 'Bed\nUsage', 'Avg Sleep\n(hrs)', 'Daily\nOccupancy'],
                y=[dashboard['sleep_consistency'], dashboard['bedtime_consistency'], 
                   dashboard['bed_use'], dashboard['avg_sleep_per_night'] * 10, 
                   dashboard['daily_occupancy'] * 10],
                marker_color='steelblue'
            ))
            
            fig_comparison.add_trace(go.Bar(
                name=compare_device['name'],
                x=['Sleep\nConsistency', 'Bedtime\nConsistency', 'Bed\nUsage', 'Avg Sleep\n(hrs)', 'Daily\nOccupancy'],
                y=[compare_dashboard['sleep_consistency'], compare_dashboard['bedtime_consistency'],
                   compare_dashboard['bed_use'], compare_dashboard['avg_sleep_per_night'] * 10,
                   compare_dashboard['daily_occupancy'] * 10],
                marker_color='coral'
            ))
            
            fig_comparison.update_layout(
                barmode='group',
                height=400,
                yaxis_title='Score (normalized to 0-100)',
                xaxis_title='Metrics'
            )
            
            st.plotly_chart(fig_comparison, use_container_width=True)
            
            st.caption("*Note: Avg Sleep and Daily Occupancy values are multiplied by 10 for visualization")
            
            st.divider()
        
        elif dashboard:
            st.markdown("### 📊 Sleep Metrics")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Sleep Consistency", f"{dashboard['sleep_consistency']:.1f}/100")
            with col2:
                st.metric("Bedtime Consistency", f"{dashboard['bedtime_consistency']:.1f}/100")
            with col3:
                st.metric("Bed Usage", f"{dashboard['bed_use']:.1f}%")
            with col4:
                st.metric("Avg Sleep/Night", f"{dashboard['avg_sleep_per_night']:.1f} hrs")
            
            col5, col6, col7 = st.columns(3)
            with col5:
                st.metric("Daily Occupancy", f"{dashboard['daily_occupancy']:.1f} hrs/day")
            with col6:
                st.metric("Total Nights", f"{int(dashboard['total_nights'])}")
            with col7:
                st.metric("Interruptions", f"{int(dashboard['total_intervals'])}")
            
            st.divider()
            
            # Sleep Goals Progress
            st.markdown("### ⏱️ Sleep Goals Progress")
            
            col1, col2 = st.columns(2)
            
            with col1:
                avg_sleep = dashboard['avg_sleep_per_night']
                
                fig_gauge = go.Figure(go.Indicator(
                    mode="gauge+number+delta",
                    value=avg_sleep,
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={'text': "Avg Sleep Duration"},
                    delta={'reference': 8, 'suffix': ' hrs'},
                    gauge={
                        'axis': {'range': [None, 12]},
                        'bar': {'color': "darkblue"},
                        'steps': [
                            {'range': [0, 6], 'color': "#ffcccc"},
                            {'range': [6, 7], 'color': "#fff4cc"},
                            {'range': [7, 9], 'color': "#ccffcc"},
                            {'range': [9, 12], 'color': "#cce5ff"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': 8
                        }
                    }
                ))
                fig_gauge.update_layout(height=300)
                st.plotly_chart(fig_gauge, use_container_width=True)
            
            with col2:
                consistency_score = dashboard['sleep_consistency']
                
                fig_consistency = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=consistency_score,
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={'text': "Sleep Consistency"},
                    gauge={
                        'axis': {'range': [0, 100]},
                        'bar': {'color': "darkgreen"},
                        'steps': [
                            {'range': [0, 50], 'color': "lightgray"},
                            {'range': [50, 75], 'color': "lightblue"},
                            {'range': [75, 100], 'color': "lightgreen"}
                        ]
                    }
                ))
                fig_consistency.update_layout(height=300)
                st.plotly_chart(fig_consistency, use_container_width=True)
            
            st.divider()
            
            # Suggestions
            st.markdown("### 💡 Personalized Suggestions")
            
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"**🌙 Awakening:** {dashboard['suggestion_awakening']}")
                st.info(f"**📅 Consistency:** {dashboard['suggestion_consistency']}")
            with col2:
                st.info(f"**⏱️ Average Sleep:** {dashboard['suggestion_avg_sleep']}")
                st.info(f"**🛏️ Bed Use:** {dashboard['suggestion_bed_use']}")
        
        else:
            st.warning("⚠️ No dashboard metrics available.")
            st.info(f"Run: `python calculate_dashboard.py {device_id}` to generate metrics from occupancy data.")
        
        st.divider()
        
        # ==================== OCCUPANCY DATA ====================
        
        if comparison_mode and compare_device:
            st.markdown("### 📊 Occupancy Data Comparison")
            
            col1, col2 = st.columns(2)
            
            # Device 1 data
            with col1:
                st.markdown(f"**{device['name']} - Last 7 Days**")
                occupancy_data = get_raw_occupancy_by_device(device_id, limit=5000)
                
                if occupancy_data:
                    df = pd.DataFrame(occupancy_data)
                    df['created_at'] = pd.to_datetime(df['created_at'])
                    df = df.sort_values('created_at')
                    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
                    df = df[df['created_at'] >= seven_days_ago]
                    
                    st.write(f"Total readings: {len(df)}")
                    
                    fig = px.scatter(
                        df,
                        x='created_at',
                        y='occupied',
                        color='occupied',
                        title=f'{device["name"]} - Occupancy Timeline',
                        labels={'created_at': 'Time', 'occupied': 'Occupied'},
                        height=300
                    )
                    fig.update_traces(marker=dict(size=2))
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("No data available")
            
            # Device 2 data
            with col2:
                st.markdown(f"**{compare_device['name']} - Last 7 Days**")
                compare_occupancy_data = get_raw_occupancy_by_device(compare_device_id, limit=5000)
                
                if compare_occupancy_data:
                    df_compare = pd.DataFrame(compare_occupancy_data)
                    df_compare['created_at'] = pd.to_datetime(df_compare['created_at'])
                    df_compare = df_compare.sort_values('created_at')
                    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
                    df_compare = df_compare[df_compare['created_at'] >= seven_days_ago]
                    
                    st.write(f"Total readings: {len(df_compare)}")
                    
                    fig = px.scatter(
                        df_compare,
                        x='created_at',
                        y='occupied',
                        color='occupied',
                        title=f'{compare_device["name"]} - Occupancy Timeline',
                        labels={'created_at': 'Time', 'occupied': 'Occupied'},
                        height=300
                    )
                    fig.update_traces(marker=dict(size=2))
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("No data available")
            
            # Combined comparison chart
            if occupancy_data and compare_occupancy_data:
                st.markdown("### 📊 Sleep Duration Comparison")
                
                sessions1 = process_occupancy_into_sessions(occupancy_data)
                sessions2 = process_occupancy_into_sessions(compare_occupancy_data)
                
                if sessions1 and sessions2:
                    df1 = pd.DataFrame(sessions1)
                    df1['device'] = device['name']
                    df1['session_start'] = pd.to_datetime(df1['session_start'])
                    df1['date'] = df1['session_start'].dt.date
                    
                    df2 = pd.DataFrame(sessions2)
                    df2['device'] = compare_device['name']
                    df2['session_start'] = pd.to_datetime(df2['session_start'])
                    df2['date'] = df2['session_start'].dt.date
                    
                    combined_df = pd.concat([df1, df2])
                    
                    fig_combined = px.bar(
                        combined_df,
                        x='date',
                        y='duration_hours',
                        color='device',
                        barmode='group',
                        title='Sleep Duration Comparison by Night',
                        labels={'date': 'Date', 'duration_hours': 'Hours', 'device': 'Device'},
                        height=400
                    )
                    st.plotly_chart(fig_combined, use_container_width=True)
        
        else:
            st.markdown("### 📊 Raw Occupancy Data (Last 7 Days)")
            
            occupancy_data = get_raw_occupancy_by_device(device_id, limit=5000)
            
            if occupancy_data:
                df = pd.DataFrame(occupancy_data)
                df['created_at'] = pd.to_datetime(df['created_at'])
                df = df.sort_values('created_at')
                
                seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
                df = df[df['created_at'] >= seven_days_ago]
                
                st.write(f"Total readings: {len(df)}")
                
                # Occupancy timeline
                fig = px.scatter(
                    df,
                    x='created_at',
                    y='occupied',
                    color='occupied',
                    title='Occupancy Timeline (7 Days)',
                    labels={'created_at': 'Time', 'occupied': 'Occupied'},
                    height=400
                )
                fig.update_traces(marker=dict(size=3))
                st.plotly_chart(fig, use_container_width=True)
                
                # Process into sessions
                sessions = process_occupancy_into_sessions(occupancy_data)
                
                if sessions:
                    st.markdown("### 🛏️ Detected Sleep Sessions")
                    
                    sessions_df = pd.DataFrame(sessions)
                    sessions_df['session_start'] = pd.to_datetime(sessions_df['session_start'])
                    sessions_df['session_end'] = pd.to_datetime(sessions_df['session_end'])
                    sessions_df['date'] = sessions_df['session_start'].dt.date
                    
                    # Sleep duration by day
                    fig2 = px.bar(
                        sessions_df,
                        x='date',
                        y='duration_hours',
                        title='Sleep Duration by Night',
                        labels={'date': 'Date', 'duration_hours': 'Hours'},
                        height=400
                    )
                    fig2.update_layout(showlegend=False)
                    st.plotly_chart(fig2, use_container_width=True)
                    
                    # Sessions table
                    st.markdown("#### Sleep Sessions Details")
                    display_df = sessions_df[['session_start', 'session_end', 'duration_hours']].copy()
                    display_df['session_start'] = display_df['session_start'].dt.strftime('%Y-%m-%d %H:%M')
                    display_df['session_end'] = display_df['session_end'].dt.strftime('%Y-%m-%d %H:%M')
                    display_df['duration_hours'] = display_df['duration_hours'].round(2)
                    st.dataframe(display_df, use_container_width=True)
                    
                    # Bedtime distribution
                    sessions_df['bedtime_hour'] = sessions_df['session_start'].dt.hour + sessions_df['session_start'].dt.minute / 60
                    fig3 = px.histogram(
                        sessions_df,
                        x='bedtime_hour',
                        nbins=24,
                        title='Bedtime Distribution',
                        labels={'bedtime_hour': 'Hour of Day'},
                        height=300
                    )
                    st.plotly_chart(fig3, use_container_width=True)
                    
                    # ==================== TREND ANALYSIS ====================
                    st.divider()
                    st.markdown("### 📈 Trend Analysis")
                    
                    # Weekly trends
                    sessions_df['week'] = sessions_df['session_start'].dt.tz_localize(None).dt.to_period('W')
                    weekly_stats = sessions_df.groupby('week').agg({
                        'duration_hours': ['mean', 'std', 'count']
                    }).reset_index()
                    
                    fig_trend = go.Figure()
                    fig_trend.add_trace(go.Scatter(
                        x=weekly_stats['week'].astype(str),
                        y=weekly_stats['duration_hours']['mean'],
                        mode='lines+markers',
                        name='Avg Sleep Duration',
                        line=dict(color='#1f77b4', width=3)
                    ))
                    fig_trend.update_layout(
                        title='Weekly Sleep Duration Trend',
                        xaxis_title='Week',
                        yaxis_title='Hours',
                        height=300
                    )
                    st.plotly_chart(fig_trend, use_container_width=True)
                    
                    # ==================== SLEEP QUALITY DISTRIBUTION ====================
                    st.markdown("### 🎯 Sleep Quality Distribution")
                    
                    good_sleep = len(sessions_df[sessions_df['duration_hours'] >= 7])
                    poor_sleep = len(sessions_df[sessions_df['duration_hours'] < 7])
                    
                    fig_donut = go.Figure(data=[go.Pie(
                        labels=['Good Sleep (≥7h)', 'Poor Sleep (<7h)'],
                        values=[good_sleep, poor_sleep],
                        hole=0.4,
                        marker=dict(colors=['#2ecc71', '#e74c3c'])
                    )])
                    fig_donut.update_layout(
                        title='Sleep Quality Distribution',
                        annotations=[dict(text=f'{(good_sleep/len(sessions_df)*100):.0f}%', 
                                         x=0.5, y=0.5, 
                                         font_size=20, 
                                         showarrow=False)],
                        height=400
                    )
                    st.plotly_chart(fig_donut, use_container_width=True)
                    
                    # ==================== WEEKLY HEATMAP ====================
                    st.markdown("### 🗓️ Weekly Sleep Pattern Heatmap")
                    
                    df['hour'] = df['created_at'].dt.hour
                    df['day_of_week'] = df['created_at'].dt.day_name()
                    
                    heatmap_data = df.groupby(['day_of_week', 'hour'])['occupied'].mean() * 100
                    heatmap_pivot = heatmap_data.unstack(fill_value=0)
                    
                    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                    heatmap_pivot = heatmap_pivot.reindex(day_order)
                    
                    fig_heatmap = go.Figure(data=go.Heatmap(
                        z=heatmap_pivot.values,
                        x=heatmap_pivot.columns,
                        y=heatmap_pivot.index,
                        colorscale='Blues',
                        text=heatmap_pivot.values.round(0),
                        texttemplate='%{text}%',
                        textfont={"size": 8},
                        colorbar=dict(title="Occupancy %")
                    ))
                    
                    fig_heatmap.update_layout(
                        title='Sleep Pattern by Day and Hour',
                        xaxis_title='Hour of Day',
                        yaxis_title='Day of Week',
                        height=400
                    )
                    st.plotly_chart(fig_heatmap, use_container_width=True)
                    
                    # ==================== SLEEP SCHEDULE CONSISTENCY ====================
                    st.markdown("### 🌅 Sleep Schedule Consistency")
                    
                    sessions_df['wakeup_hour'] = sessions_df['session_end'].dt.hour + sessions_df['session_end'].dt.minute / 60
                    
                    fig_schedule = go.Figure()
                    
                    fig_schedule.add_trace(go.Scatter(
                        x=sessions_df['bedtime_hour'],
                        y=sessions_df['wakeup_hour'],
                        mode='markers',
                        marker=dict(
                            size=sessions_df['duration_hours'] * 5,
                            color=sessions_df['duration_hours'],
                            colorscale='Viridis',
                            showscale=True,
                            colorbar=dict(title="Sleep Duration (hrs)")
                        ),
                        text=[f"{d:.1f} hrs" for d in sessions_df['duration_hours']],
                        hovertemplate='Bedtime: %{x:.1f}<br>Wake: %{y:.1f}<br>Duration: %{text}<extra></extra>'
                    ))
                    
                    # Ideal sleep zone
                    fig_schedule.add_shape(
                        type="rect",
                        x0=22, x1=23,
                        y0=6, y1=7,
                        fillcolor="green",
                        opacity=0.2,
                        layer="below",
                        line_width=0,
                    )
                    
                    fig_schedule.update_layout(
                        title='Bedtime vs Wake Time Pattern',
                        xaxis_title='Bedtime (24h)',
                        yaxis_title='Wake Time (24h)',
                        height=400,
                        xaxis=dict(range=[20, 26]),
                        yaxis=dict(range=[4, 10])
                    )
                    
                    st.plotly_chart(fig_schedule, use_container_width=True)
                    
                    # ==================== POLAR VIEW ====================
                    st.markdown("### 🕐 24-Hour Sleep Pattern (Polar View)")
                    
                    hourly_occupancy = df.groupby('hour')['occupied'].mean() * 100
                    
                    fig_polar = go.Figure(go.Scatterpolar(
                        r=hourly_occupancy.values,
                        theta=hourly_occupancy.index * 15,
                        fill='toself',
                        line=dict(color='#2ecc71', width=2),
                        marker=dict(size=8)
                    ))
                    
                    fig_polar.update_layout(
                        polar=dict(
                            radialaxis=dict(
                                visible=True,
                                range=[0, 100],
                                ticksuffix='%'
                            ),
                            angularaxis=dict(
                                tickmode='array',
                                tickvals=[0, 90, 180, 270],
                                ticktext=['00:00', '06:00', '12:00', '18:00']
                            )
                        ),
                        title='Average Occupancy by Hour (Polar)',
                        height=500
                    )
                    
                    st.plotly_chart(fig_polar, use_container_width=True)
                
                else:
                    st.warning("No sleep sessions found in the occupancy data.")
            else:
                st.warning("No occupancy data found for this device")
        
        # Footer
        st.divider()
        st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # ==================== SIDEBAR CONTROLS ====================
        
        st.sidebar.divider()
        
        # Refresh Controls
        st.sidebar.subheader("🔄 Refresh")
        
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("🔄 Refresh Now", use_container_width=True):
                st.rerun()
        
        with col2:
            auto_refresh = st.checkbox("Auto", value=False)
        
        if auto_refresh:
            import time
            refresh_interval = st.sidebar.slider("Interval (sec)", 10, 300, 60)
            st.sidebar.caption(f"Auto-refreshing every {refresh_interval}s")
            time.sleep(refresh_interval)
            st.rerun()
        
        st.sidebar.divider()
        
        # Export Options
        st.sidebar.subheader("💾 Export")
        
        if dashboard and occupancy_data:
            dashboard_json = pd.DataFrame([dashboard]).to_json(orient='records')
            st.sidebar.download_button(
                label="📊 Download Dashboard",
                data=dashboard_json,
                file_name=f"dashboard_{device_id}_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json",
                use_container_width=True
            )
            
            df_export = pd.DataFrame(occupancy_data)
            csv = df_export.to_csv(index=False)
            st.sidebar.download_button(
                label="📄 Download Raw Data",
                data=csv,
                file_name=f"occupancy_{device_id}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        st.sidebar.divider()