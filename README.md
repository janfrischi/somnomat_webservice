# Somnomat Webservice

A Python-based sleep monitoring system with **secure authentication** and **real-time dashboard**. Uses Supabase for database, authentication, and row-level security.

## 🏗️ Architecture

```
User Authentication (JWT)
         ↓
Row-Level Security (RLS)
         ↓
Python Dashboard (Streamlit)
         ↓
Supabase REST API
         ↓
PostgreSQL Database
```

---

## 🚀 Quick Start

### 1. Setup Environment

```bash
cd somnomat_webservice
source ../.webservice/bin/activate
pip install -r requirements.txt
```

### 2. Configure Supabase

Create `.env` file:

```env
SUPABASE_URL_CALMEA=https://your-project.supabase.co
SUPABASE_KEY_CALMEA=your-anon-key-here
```

### 3. Create Account & First Device

```bash
# Sign up
python auth_cli.py signup your@email.com YourPassword123 "Your Name"

# Create device with 30 days of data
python setup_device.py "Bedroom Sensor"

# Launch dashboard
streamlit run view_dashboard_streamlit_auth.py
```

Dashboard opens at: **http://localhost:8501**

---

## 📋 Essential Commands

### **Authentication**

```bash
# Sign in
python auth_cli.py signin your@email.com password

# Check current user
python auth_cli.py whoami

# Sign out
python auth_cli.py signout
```

### **Device Management**

```bash
# Create new device (with data)
python setup_device.py "Device Name"

# List your devices
python auth_cli.py devices

# Link existing device
python auth_cli.py link <device_id>
```

### **Dashboard**

```bash
# Launch authenticated dashboard
streamlit run view_dashboard_streamlit_auth.py

# Stop: Press Ctrl+C
```

### **Data Management**

```bash
# Add more occupancy data
python create_occupancy_data.py <device_id> <days>

# Recalculate metrics
python calculate_dashboard.py <device_id>
```

---

## 🎯 Complete Workflow Example

```bash
# 1. Navigate and activate
cd somnomat_webservice
source ../.webservice/bin/activate

# 2. Create account
python auth_cli.py signup alice@example.com SecurePass123 "Alice"

# 3. Create device with realistic sleep data
python setup_device.py "Alice's Bedroom"

# 4. View dashboard
streamlit run view_dashboard_streamlit_auth.py

# Done! 🎉
```

---

## 📊 Dashboard Features

- ✅ **Authentication** - Secure login/signup
- ✅ **Multi-device support** - Switch between devices
- ✅ **Comparison mode** - Compare two devices side-by-side
- ✅ **Sleep metrics** - Consistency scores, bed usage, interruptions
- ✅ **Visualizations** - Sleep patterns, trends, heatmaps
- ✅ **Personalized suggestions** - AI-generated sleep advice
- ✅ **Data export** - Download metrics as JSON/CSV

---

## 🔐 Security

- **JWT Authentication** - Token-based user sessions
- **Row-Level Security** - Database enforces user isolation
- **Automatic device linking** - New devices auto-link to creator
- **Role-based access** - Owner/viewer/admin permissions
- **Session persistence** - Saved in `~/.somnomat_session.json` (600 permissions)

---

## 📁 Project Structure

```
somnomat_webservice/
├── .env                                # Supabase credentials (gitignored)
├── auth_cli.py                        # Authentication CLI
├── setup_device.py                    # Device setup with data
├── calculate_dashboard.py             # Metrics calculator
├── view_dashboard_streamlit_auth.py   # Authenticated dashboard
├── supabase_auth_client.py           # Authentication wrapper
└── supabase_api_client_somnomat.py   # API client
```

---

## 🐛 Troubleshooting

### Virtual environment not activated

```bash
source ../.webservice/bin/activate
which python  # Should show .webservice path
```

### Not signed in

```bash
python auth_cli.py whoami  # Check status
python auth_cli.py signin your@email.com password
```

### No devices found

```bash
python auth_cli.py devices  # List devices
python setup_device.py "New Device"  # Create one
```

### Dashboard not loading

```bash
# Reinstall Streamlit
pip uninstall streamlit -y
pip install streamlit
streamlit run view_dashboard_streamlit_auth.py
```

---

## 📚 Resources

- [Supabase Dashboard](https://supabase.com/dashboard)
- [Supabase Python Docs](https://github.com/supabase-community/supabase-py)
- [Streamlit Docs](https://docs.streamlit.io)

---

**Version:** 1.0.0  
**Last Updated:** January 2025