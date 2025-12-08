"""Streamlit dashboard with authentication - Complete version with all visualizations."""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import re
import time
from datetime import datetime, timedelta, timezone

# ==================== PAGE CONFIG ====================
st.set_page_config(page_title="Somnomat Sleep Dashboard", layout="wide", page_icon="🛏️")

# ==================== IMPORTS ====================
try:
    from supabase_auth_client import SupabaseAuthClient
except Exception as e:
    st.error(f"Failed to import SupabaseAuthClient: {e}")
    st.stop()

try:
    from supabase_api_client_somnomat import (
        get_device_by_id,
        get_all_raw_occupancy_by_device,
        get_dashboard,
        get_user_settings,
        create_or_update_user_settings
    )
except Exception as e:
    st.error(f"Failed to import API client: {e}")
    st.stop()

try:
    from calculate_dashboard import process_occupancy_into_sessions
except Exception as e:
    st.error(f"Failed to import calculate_dashboard: {e}")
    st.stop()

try:
    from PIL import Image
except Exception as e:
    pass

# ==================== AUTH CLIENT INITIALIZATION ====================
try:
    # If auth_client doesn't exist we create new SupabaseAuthClient instance
    if 'auth_client' not in st.session_state:
        st.session_state.auth_client = SupabaseAuthClient()
    
    # Retrieve auth client from session state -> Stores user data, JWT tokens, etc.
    auth = st.session_state.auth_client
except Exception as e:
    st.error(f"Authentication initialization failed: {e}")
    st.stop()

# ==================== CHECK AUTHENTICATION ====================
try:
    user = auth.get_current_user()
except Exception as e:
    st.error(f"Error checking authentication: {e}")
    user = None

# ==================== LOGIN/SIGNUP PAGE ====================
# If no user is logged in, show login/signup forms
if not user:
    # Load logo for login page
    try:
        logo_path = os.path.join(os.path.dirname(__file__), "calmea.png")
        if os.path.exists(logo_path):
            logo = Image.open(logo_path)
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.image(logo, width='content')
    except:
        pass
    
    st.title("🔐 Somnomat Login")
    
    tab1, tab2, tab3 = st.tabs(["🔑 Sign In", "🚀 Sign Up", "🔄 Reset Password"])
    
    with tab1:
        st.markdown("#### Sign In to Your Account")
        with st.form("signin_form"):
            email = st.text_input("Email", placeholder="user@example.com")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Sign In", width='stretch')
            
            if submit:
                if not email or not password:
                    st.error("❌ Please fill in all fields")
                else:
                    try:
                        result = auth.sign_in(email, password)
                        if "user" in result:
                            st.success("✅ Signed in successfully!")
                            st.balloons()
                            st.rerun()
                        else:
                            st.error(f"❌ {result.get('error', 'Sign in failed')}")
                    except Exception as e:
                        st.error(f"Sign in error: {e}")
    
    with tab2:
        st.markdown("#### Create a New Account")
        with st.form("signup_form"):
            email = st.text_input("Email", placeholder="user@example.com", key="signup_email")
            password = st.text_input("Password (min 6 characters)", type="password", key="signup_password")
            password_confirm = st.text_input("Confirm Password", type="password")
            name = st.text_input("Name (optional)")
            submit = st.form_submit_button("Sign Up", width='stretch')
            
            if submit:
                if not email or not password:
                    st.error("❌ Please fill in all required fields")
                elif len(password) < 6:
                    st.error("❌ Password must be at least 6 characters")
                elif password != password_confirm:
                    st.error("❌ Passwords do not match")
                else:
                    try:
                        metadata = {"name": name} if name else {}
                        result = auth.sign_up(email, password, metadata)
                        if "user" in result:
                            st.success("✅ Account created! Please check your email to verify.")
                            st.info("📧 A verification email has been sent. Click the link to activate your account.")
                        else:
                            st.error(f"❌ {result.get('error', 'Sign up failed')}")
                    except Exception as e:
                        st.error(f"Sign up error: {e}")
    
    with tab3:
        st.markdown("#### Reset Your Password")
        with st.form("reset_form"):
            email = st.text_input("Email", placeholder="user@example.com", key="reset_email")
            submit = st.form_submit_button("Send Reset Email", width='stretch')
            
            if submit:
                if not email:
                    st.error("❌ Please enter your email")
                else:
                    try:
                        if auth.reset_password_email(email):
                            st.success("✅ Password reset email sent! Check your inbox.")
                        else:
                            st.error("❌ Failed to send reset email")
                    except Exception as e:
                        st.error(f"Password reset error: {e}")

# ==================== AUTHENTICATED USER DASHBOARD ====================
else:
    # ==================== SIDEBAR ====================
    # Load logo for sidebar
    try:
        logo_path = os.path.join(os.path.dirname(__file__), "calmea.png")
        if os.path.exists(logo_path):
            logo = Image.open(logo_path)
            st.sidebar.image(logo, width='stretch')
            st.sidebar.divider()
    except:
        st.sidebar.title("🛏️ Somnomat")
        st.sidebar.divider()
    
    # User info and sign out
    st.sidebar.title("User Account")
    user_name = user.user_metadata.get('name', user.email.split('@')[0]) if hasattr(user, 'user_metadata') else user.email.split('@')[0]
    st.sidebar.success(f"👤 {user_name}")
    st.sidebar.caption(f"📧 {user.email}")
    
    # Sign out button -> If pressed user is signed out
    if st.sidebar.button("🚪 Sign Out", width='stretch'):
        auth.sign_out()
        st.rerun()
    
    st.sidebar.divider()
    
    # Get authorized users devices
    try:
        user_devices = auth.get_user_devices()
    except Exception as e:
        st.error(f"Error loading devices: {e}")
        user_devices = []
    
    # Initial device registration
    if not user_devices:
        # ==================== NO DEVICES ====================
        st.title("📱 Welcome to Somnomat!")
        st.markdown("### No devices linked to your account yet")
        
        # Add tabs for different registration methods
        tab1, tab2 = st.tabs(["🆕 Register New Device", "🔗 Link Existing Device"])
        
        with tab1:
            st.markdown("#### Register a New Device")
            st.info("Create a new device and link it to your account")
            
            with st.form("register_device_form"):
                device_name = st.text_input(
                    "Device Name*",
                    placeholder="My Bedroom Monitor",
                    help="Choose a memorable name for your device"
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    boardtype = st.selectbox(
                        "Board Type",
                        ["ESP32", "ESP8266", "Arduino"],
                        help="Select your device's board type"
                    )
                with col2:
                    hardware_version = st.text_input(
                        "Hardware Version",
                        value="v1.0",
                        help="Hardware version of your device"
                    )
                
                mac_option = st.radio(
                    "MAC Address",
                    ["Auto-generate", "Enter manually"],
                    help="MAC address for device identification"
                )
                
                mac_address = None
                if mac_option == "Enter manually":
                    mac_address = st.text_input(
                        "MAC Address",
                        placeholder="AA:BB:CC:DD:EE:FF",
                        help="Format: XX:XX:XX:XX:XX:XX"
                    )
                
                submit = st.form_submit_button("🚀 Register Device", width='stretch')
                
                if submit:
                    if not device_name:
                        st.error("❌ Device name is required")
                    else:
                        if mac_address:
                            if not re.match(r'^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$', mac_address):
                                st.error("❌ Invalid MAC address format. Use XX:XX:XX:XX:XX:XX")
                            else:
                                result = auth.register_device(
                                    device_name=device_name,
                                    boardtype=boardtype,
                                    mac=mac_address,
                                    hardware_version=hardware_version
                                )
                                if result.get("success"):
                                    st.success(f"✅ Device '{device_name}' registered successfully!")
                                    st.info(f"**Device ID:** `{result['device_id']}`")
                                    st.info(f"**MAC Address:** `{result['mac']}`")
                                    st.balloons()
                                    # Auto-refresh after 2 seconds
                                    time.sleep(2)
                                    st.rerun()
                                else:
                                    st.error(f"❌ {result.get('error', 'Registration failed')}")
                        else:
                            result = auth.register_device(
                                device_name=device_name,
                                boardtype=boardtype,
                                hardware_version=hardware_version
                            )
                            if result.get("success"):
                                st.success(f"✅ Device '{device_name}' registered successfully!")
                                st.info(f"**Device ID:** `{result['device_id']}`")
                                st.info(f"**MAC Address:** `{result['mac']}`")
                                st.balloons()
                                # Auto-refresh after 2 seconds
                                time.sleep(2)
                                st.rerun()
                            else:
                                st.error(f"❌ {result.get('error', 'Registration failed')}")
        
        with tab2:
            st.markdown("#### Link an Existing Device")
            st.info("Link a device that's already registered in the system")
            
            # Replace the CLI-only instructions with an actual form
            with st.form("link_device_form"):
                device_id_to_link = st.number_input(
                    "Device ID",
                    min_value=1,
                    step=1,
                    help="Enter the ID of the device you want to link"
                )
                
                st.markdown("**Role**")
                link_role = st.radio(
                    "Select your role for this device",
                    ["owner", "viewer", "admin"],
                    index=1,  # Default to 'viewer'
                    help="Owner: Full control | Viewer: Read-only | Admin: Can modify settings",
                    horizontal=True
                )
                
                submit_link = st.form_submit_button("🔗 Link Device", width='stretch')
                
                if submit_link:
                    with st.spinner(f"Linking device {device_id_to_link}..."):
                        result = auth.link_device_to_user(int(device_id_to_link), role=link_role)
                        
                        if result:
                            st.success(f"✅ Device {device_id_to_link} successfully linked to your account as {link_role}!")
                            st.balloons()
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error(f"❌ Failed to link device {device_id_to_link}. Make sure the device exists and you have permission.")
            
            st.divider()
            
            st.markdown("**Alternative: Use CLI**")
            st.code("""
cd somnomat_webservice
python auth_cli.py link <device_id>
            """, language="bash")
        
        st.divider()
        
        if st.button("🔄 Refresh Page", width='stretch'):
            st.rerun()
        
        # ==================== STOP HERE - NO DEVICES ====================
        st.stop()  # Add this line to prevent further execution
    
    else:
        # ==================== DEVICE SELECTION & MANAGEMENT ====================
        st.sidebar.title("Device Management")
        
        device_options = {
            f"{d['devices']['name']} (ID: {d['device_id']})": d['device_id'] 
            for d in user_devices
        }
        
        selected = st.sidebar.selectbox("Select Device", list(device_options.keys()))
        device_id = device_options[selected]
        
        current_device = next(d for d in user_devices if d['device_id'] == device_id)
        user_role = current_device['role']
        
        if st.sidebar.button("➕ Register/Link New Device", width='stretch'):
            st.session_state.show_register_form = True
        
        if st.sidebar.button("⚙️ Adjust Device Settings", use_container_width=True, key="settings_button_sidebar"):
            st.session_state.show_settings = True
        
        if user_role == 'owner':
            if st.sidebar.button("🗑️ Delete Device", width='stretch', type="secondary"):
                st.session_state.show_delete_confirmation = True
        
        st.sidebar.divider()
        
        # ==================== LOAD DEVICE DATA ====================
        device = get_device_by_id(device_id)
        if not device:
            st.error(f"Device {device_id} not found")
            st.stop()
        
        # Check if user wants to delete device
        if st.session_state.get('show_delete_confirmation', False):
            st.title("🗑️ Delete Device")
            st.markdown(f"### Are you sure you want to delete '{device['name']}'?")
            
            st.error("⚠️ **WARNING: This action cannot be undone!**")
            
            st.markdown(f"""
            **Device Information:**
            - **Name:** {device['name']}
            - **ID:** {device_id}
            - **MAC:** {device.get('mac', 'N/A')}
            - **Board Type:** {device.get('boardtype', 'N/A')}
            
            **The following data will be permanently deleted:**
            - All occupancy readings
            - All dashboard metrics
            - All sleep sessions
            - Device configuration
            - User associations
            """)
            
            st.divider()
            
            # Confirmation form
            with st.form("delete_confirmation_form"):
                st.markdown("#### Type the device name to confirm deletion")
                
                confirmation_name = st.text_input(
                    f"Type '{device['name']}' to confirm",
                    placeholder=device['name'],
                    key="delete_confirmation_input"
                )
                
                st.markdown("#### Are you absolutely sure?")
                final_confirmation = st.checkbox(
                    "Yes, I understand this action is permanent and irreversible",
                    key="final_delete_confirmation"
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    delete_btn = st.form_submit_button(
                        "🗑️ Delete Permanently",
                     width='stretch',
                        type="primary"
                    )
                with col2:
                    cancel_btn = st.form_submit_button(
                        "❌ Cancel",
                     width='stretch'
                    )
                
                if cancel_btn:
                    st.session_state.show_delete_confirmation = False
                    # Go back to main page
                    st.rerun()
                
                if delete_btn:
                    if confirmation_name != device['name']:
                        st.error("❌ Device name doesn't match. Deletion cancelled.")
                    elif not final_confirmation:
                        st.error("❌ Please confirm that you understand this action is permanent.")
                    else:
                        # Proceed with deletion
                        with st.spinner("Deleting device..."):
                            result = auth.delete_device(device_id)
                            
                            if result.get("success"):
                                st.success(f"✅ Device '{device['name']}' has been permanently deleted.")
                                st.success("All associated data has been removed.")
                                st.session_state.show_delete_confirmation = False
                                
                                # Wait a moment then refresh
                                import time
                                time.sleep(2)
                                st.rerun()
                            else:
                                st.error(f"❌ {result.get('error', 'Failed to delete device')}")
            
            st.stop()
        
        # Check if user wants to register a new device
        if st.session_state.get('show_register_form', False):
            # Show title in main area
            st.title("📱 Device Management")
            st.markdown("#### Add a device to your account")
            
            # Add tabs for registration vs linking
            tab1, tab2 = st.tabs(["🆕 Register New Device", "🔗 Link Existing Device"])
            
            with tab1:
                st.markdown("**Create a brand new device**")
                
                with st.form("sidebar_register_device_form"):
                    device_name = st.text_input(
                        "Device Name",
                        placeholder="My Bedroom",
                        key="sidebar_device_name"
                    )
                    
                    boardtype = st.selectbox(
                        "Board Type",
                        ["ESP32", "ESP8266", "Arduino"],
                        key="sidebar_boardtype"
                    )
                    
                    hardware_version = st.text_input(
                        "Hardware Version",
                        value="v1.0",
                        key="sidebar_hardware_version"
                    )
                    
                    mac_option = st.radio(
                        "MAC Address",
                        ["Auto-generate", "Enter manually"],
                        key="sidebar_mac_option"
                    )
                    
                    mac_address = None
                    if mac_option == "Enter manually":
                        mac_address = st.text_input(
                            "MAC Address",
                            placeholder="AA:BB:CC:DD:EE:FF",
                            key="sidebar_mac_address"
                        )
                    
                    # Define columns for buttons
                    col1, col2 = st.columns(2)
                    with col1:
                        submit = st.form_submit_button("✅ Register", width='stretch')
                    with col2:
                        cancel = st.form_submit_button("❌ Cancel", width='stretch')
                
                if cancel:
                    st.session_state.show_register_form = False
                    st.rerun()
                
                if submit:
                    if not device_name:
                        st.error("❌ Name required")
                    else:
                        if mac_address:
                            if not re.match(r'^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$', mac_address):
                                st.error("❌ Invalid MAC format")
                            else:
                                result = auth.register_device(
                                    device_name=device_name,
                                    boardtype=boardtype,
                                    mac=mac_address,
                                    hardware_version=hardware_version
                                )
                                if result.get("success"):
                                    st.success(f"✅ Device registered!")
                                    st.info(f"ID: `{result['device_id']}`")
                                    st.info(f"MAC: `{result['mac']}`")
                                    st.session_state.show_register_form = False
                                    st.rerun()
                                else:
                                    st.error(f"❌ {result.get('error', 'Failed')}")
                        else:
                            result = auth.register_device(
                                device_name=device_name,
                                boardtype=boardtype,
                                hardware_version=hardware_version
                            )
                            if result.get("success"):
                                st.success(f"✅ Device registered!")
                                st.info(f"ID: `{result['device_id']}`")
                                st.info(f"MAC: `{result['mac']}`")
                                st.session_state.show_register_form = False
                                st.rerun()
                            else:
                                st.error(f"❌ {result.get('error', 'Failed')}")
            
            with tab2:
                st.markdown("**Connect a device that's already in the database**")
                
                with st.form("sidebar_link_device_form"):
                    device_id_to_link = st.number_input(
                        "Device ID",
                        min_value=1,
                        step=1,
                        value=987,  # Pre-fill with 987 as default
                        help="Enter the ID of the device you want to link (e.g., 987)"
                    )
                    
                    st.markdown("**Your Role**")
                    link_role = st.radio(
                        "Select your access level",
                        ["owner", "viewer", "admin"],
                        index=0,  # Default to owner
                        help="Owner: Full control | Viewer: Read-only | Admin: Can modify settings",
                        horizontal=True,
                        key="sidebar_link_role"
                    )
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        submit_link = st.form_submit_button("🔗 Link Device", width='stretch', type="primary")
                    with col2:
                        cancel_link = st.form_submit_button("❌ Cancel", width='stretch')
                    
                    if cancel_link:
                        st.session_state.show_register_form = False
                        st.rerun()
                    
                    if submit_link:
                        with st.spinner(f"Linking device {device_id_to_link}..."):
                            result = auth.link_device_to_user(int(device_id_to_link), role=link_role)
                            
                            if result:
                                st.success(f"✅ Device {device_id_to_link} successfully linked!")
                                st.info(f"**Role:** {link_role}")
                                st.balloons()
                                
                                # Close the form and refresh
                                st.session_state.show_register_form = False
                                time.sleep(1.5)
                                st.rerun()
                            else:
                                st.error(f"❌ Failed to link device {device_id_to_link}")
                                st.warning("**Possible reasons:**")
                                st.write("- Device doesn't exist in the database")
                                st.write("- You don't have permission to link this device")
                                st.write("- Device is already linked to your account")
                
                st.divider()
            st.sidebar.divider()
            
            st.stop()  # Stop execution here so dashboard doesn't try to load
        
        # Settings Modal/Expander in main area
        if st.session_state.get('show_settings', False):
            st.title("⚙️ Device Settings")
            st.markdown(f"#### Configure {device['name']}")
            
            # Get current user ID
            current_user_id = user.id
            
            # Load existing settings
            user_settings = get_user_settings(device_id, current_user_id)
            
            # Default values if no settings exist
            default_amplitude = user_settings['amplitude'] if user_settings else 5
            default_frequency = user_settings['frequency'] if user_settings else 5
            default_vibration = user_settings['vibration'] if user_settings else 3
            
            # Create settings form
            with st.form("device_settings_form", clear_on_submit=False):
                st.markdown("#### Adjust Device Parameters")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    amplitude = st.slider(
                        "🔊 Amplitude",
                        min_value=1,
                        max_value=10,
                        value=default_amplitude,
                        help="Adjust the amplitude level (1-10)",
                        key="amplitude_slider"
                    )
                    st.caption(f"Current: {amplitude}/10")
                
                with col2:
                    frequency = st.slider(
                        "📡 Frequency",
                        min_value=1,
                        max_value=10,
                        value=default_frequency,
                        help="Adjust the frequency level (1-10)",
                        key="frequency_slider"
                    )
                    st.caption(f"Current: {frequency}/10")
                
                with col3:
                    vibration = st.slider(
                        "📳 Vibration",
                        min_value=1,
                        max_value=5,
                        value=default_vibration,
                        help="Adjust the vibration intensity (1-5)",
                        key="vibration_slider"
                    )
                    st.caption(f"Current: {vibration}/5")
                
                # Show preview of current settings
                st.markdown("#### Current Configuration")
                
                preview_col1, preview_col2, preview_col3 = st.columns(3)
                
                with preview_col1:
                    st.metric("Amplitude", f"{amplitude}/10", 
                             delta=f"{amplitude - default_amplitude:+d}" if user_settings else None)
                
                with preview_col2:
                    st.metric("Frequency", f"{frequency}/10",
                             delta=f"{frequency - default_frequency:+d}" if user_settings else None)
                
                with preview_col3:
                    st.metric("Vibration", f"{vibration}/5",
                             delta=f"{vibration - default_vibration:+d}" if user_settings else None)
                
                # Submit buttons
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    submit = st.form_submit_button(
                        "💾 Save Settings",
                        use_container_width=True,
                        type="primary"
                    )
                
                with col2:
                    reset = st.form_submit_button(
                        "🔄 Reset to Defaults",
                        use_container_width=True
                    )
                
                with col3:
                    cancel = st.form_submit_button(
                        "❌ Close",
                        use_container_width=True
                    )
                
                if cancel:
                    st.session_state.show_settings = False
                    st.rerun()
                
                if submit:
                    # Save settings to database
                    with st.spinner("Saving settings..."):
                        result = create_or_update_user_settings(
                            device_id=device_id,
                            user_id=current_user_id,
                            amplitude=amplitude,
                            frequency=frequency,
                            vibration=vibration
                        )
                        
                        if result:
                            st.success("✅ Settings saved successfully!")
                            
                            # Show what was saved
                            st.info(f"""
                            **Saved Configuration:**
                            - Amplitude: {amplitude}/10
                            - Frequency: {frequency}/10
                            - Vibration: {vibration}/5
                            """)
                            
                            # Close settings and refresh
                            time.sleep(0.5)
                            st.session_state.show_settings = False
                            st.rerun()
                        else:
                            st.error("❌ Failed to save settings. Please try again.")
                
                # Reset to defaults
                if reset:
                    # Reset to defaults (5, 5, 3)
                    result = create_or_update_user_settings(
                        device_id=device_id,
                        user_id=current_user_id,
                        amplitude=5,
                        frequency=5,
                        vibration=3
                    )
                    
                    if result:
                        st.success("✅ Settings reset to defaults!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Failed to reset settings.")
            
            # Show last updated timestamp if settings exist
            if user_settings and user_settings.get('updated_at'):
                last_updated = datetime.fromisoformat(user_settings['updated_at'].replace('Z', '+00:00'))
                st.caption(f"Last updated: {last_updated.strftime('%Y-%m-%d %H:%M:%S')}")
            
            st.divider()
            st.stop()  # Stop rendering the rest of the dashboard when settings are open


        # -----Comparison Mode------
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
        
        # Define the headers for both comparison and single mode
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
        
        # Comparison Mode Device Info
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
        # Regular mode
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
    
        # ==================== LOAD DASHBOARD METRICS ====================
        # Load dashboard metrics -> Pull data from Supabase
        dashboard = get_dashboard(device_id) # Values were previously computed with calculate_dashboard.py
        compare_dashboard = get_dashboard(compare_device_id) if compare_device else None
        
        # ==================== METRICS DISPLAY ====================
        # Comparison Mode Metrics
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
            
            st.plotly_chart(fig_comparison, width='stretch')
            
            st.caption("*Note: Avg Sleep and Daily Occupancy values are multiplied by 10 for visualization")
            
            st.divider()
        
        # Regular Mode Metrics
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
                st.plotly_chart(fig_gauge, width='stretch')
            
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
                st.plotly_chart(fig_consistency, width='stretch')
            
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
            st.markdown(f"**{device['name']} - Last {days_back} Days**")
            occupancy_data = get_all_raw_occupancy_by_device(device_id)
            
            if occupancy_data:
                df = pd.DataFrame(occupancy_data)
                df['created_at'] = pd.to_datetime(df['created_at'])
                df = df.sort_values('created_at')
                
                # Filter to date range
                cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
                df = df[df['created_at'] >= cutoff_date]
                
                # Check if filtered data is empty
                if len(df) == 0:
                    st.warning(f"⚠️ No data in the last {days_back} days")
                    
                    # Show available range
                    all_df = pd.DataFrame(occupancy_data)
                    all_df['created_at'] = pd.to_datetime(all_df['created_at'])
                    if len(all_df) > 0:
                        st.info(f"Data available from {all_df['created_at'].min().strftime('%Y-%m-%d')} to {all_df['created_at'].max().strftime('%Y-%m-%d')}")
                else:
                    st.write(f"Total readings: {len(df)}")
                    st.caption(f"From {df['created_at'].min().strftime('%Y-%m-%d')} to {df['created_at'].max().strftime('%Y-%m-%d')}")
                    
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
                    st.plotly_chart(fig, width='stretch')
            else:
                st.warning("No data available")
        
        # Device 2 data
        with col2:
            st.markdown(f"**{compare_device['name']} - Last {days_back} Days**")
            compare_occupancy_data = get_all_raw_occupancy_by_device(compare_device_id)
            
            if compare_occupancy_data:
                df_compare = pd.DataFrame(compare_occupancy_data)
                df_compare['created_at'] = pd.to_datetime(df_compare['created_at'])
                df_compare = df_compare.sort_values('created_at')
                
                # Filter to date range
                cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
                df_compare = df_compare[df_compare['created_at'] >= cutoff_date]
                
                # Check if filtered data is empty
                if len(df_compare) == 0:
                    st.warning(f"⚠️ No data in the last {days_back} days")
                    
                    # Show available range
                    all_df = pd.DataFrame(compare_occupancy_data)
                    all_df['created_at'] = pd.to_datetime(all_df['created_at'])
                    if len(all_df) > 0:
                        st.info(f"Data available from {all_df['created_at'].min().strftime('%Y-%m-%d')} to {all_df['created_at'].max().strftime('%Y-%m-%d')}")
                else:
                    st.write(f"Total readings: {len(df_compare)}")
                    st.caption(f"From {df_compare['created_at'].min().strftime('%Y-%m-%d')} to {df_compare['created_at'].max().strftime('%Y-%m-%d')}")
                    
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
                    st.plotly_chart(fig, width='stretch')
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
                st.plotly_chart(fig_combined, width='stretch')
    
    else:
        st.markdown(f"### 📊 Raw Occupancy Data (Last {days_back} Days)")
        
        occupancy_data = get_all_raw_occupancy_by_device(device_id)
        
        if occupancy_data:
            df = pd.DataFrame(occupancy_data)
            df['created_at'] = pd.to_datetime(df['created_at'])
            df = df.sort_values('created_at')
            
            # Filter to selected date range
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
            df = df[df['created_at'] >= cutoff_date]
            
            # Check if filtered data is empty
            if len(df) == 0:
                st.warning(f"⚠️ No occupancy data found in the last {days_back} days")
                
                # Show available data range if there's any data at all
                if len(occupancy_data) > 0:
                    all_df = pd.DataFrame(occupancy_data)
                    all_df['created_at'] = pd.to_datetime(all_df['created_at'])
                    oldest_date = all_df['created_at'].min().strftime('%Y-%m-%d')
                    newest_date = all_df['created_at'].max().strftime('%Y-%m-%d')
                    
                    st.info(f"""
                    **Available data range:**  
                    From **{oldest_date}** to **{newest_date}**
                    
                    💡 Tip: Try selecting a longer date range or use the **Custom Range** option.
                    """)
                
                st.stop()  # Stop rendering this section
            
            st.write(f"Total readings: {len(df)}")
            st.caption(f"Date range: {df['created_at'].min().strftime('%Y-%m-%d')} to {df['created_at'].max().strftime('%Y-%m-%d')}")
            
            # Occupancy timeline
            fig = px.scatter(
                df,
                x='created_at',
                y='occupied',
                color='occupied',
                title=f'Occupancy Timeline ({days_back} Days)',
                labels={'created_at': 'Time', 'occupied': 'Occupied'},
                height=400
            )
            fig.update_traces(marker=dict(size=3))
            st.plotly_chart(fig, width='stretch')
            
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
                st.plotly_chart(fig2, width='stretch')
                
                # Bedtime and wake time calculations
                sessions_df['bedtime_hour'] = sessions_df['session_start'].dt.hour + sessions_df['session_start'].dt.minute / 60
                sessions_df['wakeup_hour'] = sessions_df['session_end'].dt.hour + sessions_df['session_end'].dt.minute / 60
                
                # Add num_interruptions if not present
                if 'num_interruptions' not in sessions_df.columns:
                    sessions_df['num_interruptions'] = 0
                
                # ==================== TREND ANALYSIS ====================
                st.divider()
                st.markdown("### 📈 Trend Analysis")
                
                # Add time period selector
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    trend_period = st.selectbox(
                        "Select Analysis Period",
                        ["Daily", "Weekly", "Monthly"],
                        key="trend_period"
                    )
                
                with col2:
                    trend_metric = st.selectbox(
                        "Select Metric",
                        ["Sleep Duration", "Sleep Consistency", "Bedtime", "Wake Time", "Interruptions"],
                        key="trend_metric"
                    )
                
                with col3:
                    show_moving_avg = st.checkbox("Moving Avg", value=True, key="show_ma")
                
                # Prepare data based on selected period
                sessions_df_copy = sessions_df.copy()
                sessions_df_copy['date_only'] = sessions_df_copy['session_start'].dt.date
                
                if trend_period == "Daily":
                    # Group by day
                    agg_dict = {
                        'duration_hours': ['mean', 'std', 'count'],
                        'bedtime_hour': 'mean',
                        'wakeup_hour': 'mean'
                    }
                    
                    # Only include num_interruptions if it exists
                    if 'num_interruptions' in sessions_df_copy.columns:
                        agg_dict['num_interruptions'] = 'sum'
                    
                    trend_data = sessions_df_copy.groupby('date_only').agg(agg_dict).reset_index()
                    
                    # Flatten column names
                    if 'num_interruptions' in sessions_df_copy.columns:
                        trend_data.columns = ['date', 'avg_duration', 'std_duration', 'count', 'avg_bedtime', 'avg_wakeup', 'interruptions']
                    else:
                        trend_data.columns = ['date', 'avg_duration', 'std_duration', 'count', 'avg_bedtime', 'avg_wakeup']
                        trend_data['interruptions'] = 0
                    
                    x_label = 'Date'
                    date_format = '%Y-%m-%d'
                    
                elif trend_period == "Weekly":
                    # Group by week
                    sessions_df_copy['week'] = sessions_df_copy['session_start'].dt.tz_localize(None).dt.to_period('W')
                    
                    agg_dict = {
                        'duration_hours': ['mean', 'std', 'count'],
                        'bedtime_hour': 'mean',
                        'wakeup_hour': 'mean'
                    }
                    
                    # Only add num_interruptions if column exists AND has data
                    if 'num_interruptions' in sessions_df_copy.columns and sessions_df_copy['num_interruptions'].notna().any():
                        agg_dict['num_interruptions'] = 'sum'
                    
                    trend_data = sessions_df_copy.groupby('week').agg(agg_dict).reset_index()
                    
                    # Build column names based on what was actually aggregated
                    if 'num_interruptions' in agg_dict:
                        trend_data.columns = ['week', 'avg_duration', 'std_duration', 'count', 'avg_bedtime', 'avg_wakeup', 'interruptions']
                    else:
                        trend_data.columns = ['week', 'avg_duration', 'std_duration', 'count', 'avg_bedtime', 'avg_wakeup']
                        trend_data['interruptions'] = 0
                    
                    trend_data['date'] = trend_data['week'].astype(str)
                    x_label = 'Week'
                    date_format = None;
                    
                else:  # Monthly
                    # Group by month
                    sessions_df_copy['month'] = sessions_df_copy['session_start'].dt.tz_localize(None).dt.to_period('M')
    
                    agg_dict = {
                        'duration_hours': ['mean', 'std', 'count'],
                        'bedtime_hour': 'mean',
                        'wakeup_hour': 'mean'
                    }
    
                    # Only add num_interruptions if column exists AND has data
                    if 'num_interruptions' in sessions_df_copy.columns and sessions_df_copy['num_interruptions'].notna().any():
                        agg_dict['num_interruptions'] = 'sum'
    
                    trend_data = sessions_df_copy.groupby('month').agg(agg_dict).reset_index()
    
                    # Build column names based on what was actually aggregated
                    if 'num_interruptions' in agg_dict:
                        trend_data.columns = ['month', 'avg_duration', 'std_duration', 'count', 'avg_bedtime', 'avg_wakeup', 'interruptions']
                    else:
                        trend_data.columns = ['month', 'avg_duration', 'std_duration', 'count', 'avg_bedtime', 'avg_wakeup']
                        trend_data['interruptions'] = 0
    
                    trend_data['date'] = trend_data['month'].astype(str)
                    x_label = 'Month'
                    date_format = None
                
                # Calculate sleep consistency score for each period
                trend_data['consistency_score'] = trend_data.apply(
                    lambda row: max(0, 100 - (row['std_duration'] * 33.33)) if pd.notna(row['std_duration']) else 100,
                    axis=1
                )
                
                # Select data based on chosen metric
                metric_mapping = {
                    "Sleep Duration": ('avg_duration', 'Hours', 'Sleep Duration'),
                    "Sleep Consistency": ('consistency_score', 'Score (0-100)', 'Sleep Consistency'),
                    "Bedtime": ('avg_bedtime', 'Hour (24h)', 'Average Bedtime'),
                    "Wake Time": ('avg_wakeup', 'Hour (24h)', 'Average Wake Time'),
                    "Interruptions": ('interruptions', 'Count', 'Sleep Interruptions')
                }
                
                y_column, y_label, chart_title = metric_mapping[trend_metric]
                
                # Create the main trend chart
                fig_trend = go.Figure()
                
                # Add main data line
                fig_trend.add_trace(go.Scatter(
                    x=trend_data['date'],
                    y=trend_data[y_column],
                    mode='lines+markers',
                    name=trend_metric,
                    line=dict(color='#1f77b4', width=3),
                    marker=dict(size=8),
                    hovertemplate=f'<b>{x_label}</b>: %{{x}}<br><b>{trend_metric}</b>: %{{y:.2f}}<extra></extra>'
                ))
                
                # Add moving average if selected
                if show_moving_avg and len(trend_data) >= 3:
                    if trend_period == "Daily":
                        window = 7  # 7-day moving average
                    elif trend_period == "Weekly":
                        window = 4  # 4-week moving average
                    else:
                        window = 3  # 3-month moving average
                    
                    if len(trend_data) >= window:
                        trend_data['moving_avg'] = trend_data[y_column].rolling(window=window, center=True).mean()
                        
                        fig_trend.add_trace(go.Scatter(
                            x=trend_data['date'],
                            y=trend_data['moving_avg'],
                            mode='lines',
                            name=f'{window}-Period MA',
                            line=dict(color='#ff7f0e', width=2, dash='dash'),
                            hovertemplate=f'<b>Moving Average</b>: %{{y:.2f}}<extra></extra>'
                        ))
                
                # Add reference line for sleep duration
                if trend_metric == "Sleep Duration":
                    fig_trend.add_hline(
                        y=8, 
                        line_dash="dot", 
                        line_color="green",
                        annotation_text="Recommended (8h)",
                        annotation_position="right"
                    )
                    fig_trend.add_hline(
                        y=7, 
                        line_dash="dot", 
                        line_color="orange",
                        annotation_text="Minimum (7h)",
                        annotation_position="right"
                    )
                
                # Add reference line for bedtime
                elif trend_metric == "Bedtime":
                    fig_trend.add_hline(
                        y=22, 
                        line_dash="dot", 
                        line_color="green",
                        annotation_text="Optimal (10 PM)",
                        annotation_position="right"
                    )
                
                # Add reference line for wake time
                elif trend_metric == "Wake Time":
                    fig_trend.add_hline(
                        y=7, 
                        line_dash="dot", 
                        line_color="green",
                        annotation_text="Optimal (7 AM)",
                        annotation_position="right"
                    )
                
                fig_trend.update_layout(
                    title=f'{chart_title} - {trend_period} Trend',
                    xaxis_title=x_label,
                    yaxis_title=y_label,
                    height=400,
                    hovermode='x unified',
                    showlegend=True
                )
                
                st.plotly_chart(fig_trend, width='stretch')
                
                # Add statistics summary
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    avg_value = trend_data[y_column].mean()
                    st.metric(
                        f"Average {trend_metric}",
                        f"{avg_value:.2f}" + (" hrs" if "Duration" in trend_metric or "Time" in trend_metric else "")
                    )
                
                with col2:
                    trend_direction = "📈" if trend_data[y_column].iloc[-1] > trend_data[y_column].iloc[0] else "📉"
                    trend_change = ((trend_data[y_column].iloc[-1] - trend_data[y_column].iloc[0]) / trend_data[y_column].iloc[0] * 100)
                    st.metric(
                        "Trend",
                        f"{trend_direction} {abs(trend_change):.1f}%",
                        delta=f"{trend_change:+.1f}%"
                    )
                
                with col3:
                    best_value = trend_data[y_column].max() if trend_metric != "Interruptions" else trend_data[y_column].min()
                    st.metric(
                        "Best Period",
                        f"{best_value:.2f}"
                    )
                
                with col4:
                    std_value = trend_data[y_column].std()
                    st.metric(
                        "Variability",
                        f"{std_value:.2f}",
                        help="Lower is more consistent"
                    )
                
                # ==================== DETAILED BREAKDOWN ====================
                with st.expander("📊 Detailed Breakdown"):
                    # Show data table
                    display_trend_data = trend_data.copy()
                    
                    if trend_period == "Daily":
                        display_trend_data['date'] = pd.to_datetime(display_trend_data['date']).dt.strftime('%Y-%m-%d')
                    
                    # Rename columns for display
                    display_columns = {
                        'date': 'Period',
                        'avg_duration': 'Avg Sleep (hrs)',
                        'std_duration': 'Std Dev (hrs)',
                        'count': 'Nights',
                        'avg_bedtime': 'Avg Bedtime (24h)',
                        'avg_wakeup': 'Avg Wake (24h)',
                        'interruptions': 'Interruptions',
                        'consistency_score': 'Consistency Score'
                    }
                    
                    display_trend_data = display_trend_data.rename(columns=display_columns)
                    display_trend_data = display_trend_data[[col for col in display_columns.values() if col in display_trend_data.columns]]
                    
                    # Round numeric columns
                    numeric_cols = display_trend_data.select_dtypes(include=['float64']).columns
                    display_trend_data[numeric_cols] = display_trend_data[numeric_cols].round(2)
                    
                    st.dataframe(display_trend_data, width='stretch', hide_index=True)
                    
                    # Download button for trend data
                    csv_trend = display_trend_data.to_csv(index=False)
                    st.download_button(
                        label=f"📥 Download {trend_period} Trend Data",
                        data=csv_trend,
                        file_name=f"trend_{trend_period.lower()}_{device_id}_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
                
                # ==================== COMPARISON VIEW ====================
                if trend_period == "Daily" or trend_period == "Weekly":
                    st.markdown("#### 📊 Multi-Metric Comparison")
                    
                    # Create comparison chart with multiple metrics
                    fig_multi = go.Figure()
                    
                    # Normalize data to 0-100 scale for comparison
                    # Handle case where interruptions might be 0 (avoid division by zero)
                    max_interruptions = trend_data['interruptions'].max()
                    if max_interruptions > 0:
                        interruption_score = 100 - (trend_data['interruptions'] / max_interruptions * 100)
                    else:
                        interruption_score = pd.Series([100] * len(trend_data))
                    
                    metrics_to_compare = {
                        'Sleep Duration': (trend_data['avg_duration'] / 12 * 100, '#1f77b4'),
                        'Consistency': (trend_data['consistency_score'], '#2ca02c'),
                        'Interruptions': (interruption_score, '#d62728')
                    }
                    
                    for metric_name, (data, color) in metrics_to_compare.items():
                        fig_multi.add_trace(go.Scatter(
                            x=trend_data['date'],
                            y=data,
                            mode='lines',
                            name=metric_name,
                            line=dict(color=color, width=2)
                        ))
                    
                    fig_multi.update_layout(
                        title='Multi-Metric Comparison (Normalized to 0-100)',
                        xaxis_title=x_label,
                        yaxis_title='Score (0-100)',
                        height=350,
                        hovermode='x unified'
                    )
                    
                    st.plotly_chart(fig_multi, width='stretch')
                
                st.divider()
    
    # ==================== RAW DATA DOWNLOAD ====================
    st.markdown("### 📥 Download Your Data")
    
    # Occupancy data download
    if st.button("📄 Download Raw Occupancy Data", width='stretch'):
        occupancy_data_download = get_all_raw_occupancy_by_device(device_id)
        
        if occupancy_data_download:
            df_occupancy = pd.DataFrame(occupancy_data_download)
            
            # Filter to date range
            df_occupancy['created_at'] = pd.to_datetime(df_occupancy['created_at'])
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
            df_occupancy = df_occupancy[df_occupancy['created_at'] >= cutoff_date]
            
            # Check if there's any data after filtering
            if len(df_occupancy) == 0:
                st.warning(f"⚠️ No occupancy data available in the last {days_back} days")
                
                # Show total available data
                all_df = pd.DataFrame(occupancy_data_download)
                all_df['created_at'] = pd.to_datetime(all_df['created_at'])
                st.info(f"""
                **Total data available:** {len(all_df)} readings  
                **Date range:** {all_df['created_at'].min().strftime('%Y-%m-%d')} to {all_df['created_at'].max().strftime('%Y-%m-%d')}
                
                💡 Tip: Adjust your date range to include this data.
                """)
            else:
                csv_occupancy = df_occupancy.to_csv(index=False)
                
                st.download_button(
                    label=f"📥 Download Occupancy Data ({len(df_occupancy)} readings)",
                    data=csv_occupancy,
                    file_name=f"occupancy_data_{device_id}_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    width='stretch'
                )
        else:
            st.warning("No occupancy data available for download")
    
    # Dashboard data download
    if st.button("📊 Download Dashboard Metrics", width='stretch'):
        dashboard_data = get_dashboard(device_id)
        
        if dashboard_data:
            df_dashboard = pd.DataFrame([dashboard_data])
            csv_dashboard = df_dashboard.to_csv(index=False)
            
            st.download_button(
                label="📥 Download Dashboard Metrics",
                data=csv_dashboard,
                file_name=f"dashboard_metrics_{device_id}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
             width='stretch'
            )
        else:
            st.warning("No dashboard data available for download")
    
    # Footer
    st.divider()
    st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # ==================== SIDEBAR CONTROLS ====================
    
    st.sidebar.divider()
    
    # Refresh Controls
    st.sidebar.subheader("🔄 Refresh")
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("🔄 Refresh Now", width='stretch'):
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
    
    if dashboard:
        dashboard_json = pd.DataFrame([dashboard]).to_json(orient='records')
        st.sidebar.download_button(
            label="📊 Download Dashboard",
            data=dashboard_json,
            file_name=f"dashboard_{device_id}_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json",
            width='stretch'
        )
        
        # Export all occupancy data
        occupancy_export = get_all_raw_occupancy_by_device(device_id)
        
        if occupancy_export:
            df_export = pd.DataFrame(occupancy_export)
            df_export['created_at'] = pd.to_datetime(df_export['created_at'])
            
            # Filter to date range
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
            df_export = df_export[df_export['created_at'] >= cutoff_date]
            
            csv = df_export.to_csv(index=False)
            st.sidebar.download_button(
                label=f"📄 Download Raw Data ({len(df_export)} readings)",
                data=csv,
                file_name=f"occupancy_{device_id}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                width='stretch'
            )