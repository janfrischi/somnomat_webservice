# Somnomat Webservice

A Python-based sleep monitoring backend using Supabase for data storage and analysis. This service calculates sleep metrics, generates personalized insights, and provides tools for analyzing sleep patterns.

## 🏗️ Architecture

```
Python Analysis Scripts
         ↓
  supabase_api_client.py (Python wrapper)
         ↓
  Supabase REST API
         ↓
  PostgreSQL Database
    • sleep_sessions
    • sleep_dashboard
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
SUPABASE_URL=https://xybqmwkxsriatdfvhpym.supabase.co
SUPABASE_KEY=your-anon-key-here
```

Get credentials from: **Supabase Dashboard** → **Project Settings** → **API**

### 3. Create Test Data

```bash
python seed_sleep_sessions.py
```

---

## 📊 Main Features

### 1. Calculate Dashboard Metrics

Analyzes sleep sessions and generates:
- Sleep consistency score (0-100)
- Bedtime consistency score (0-100)
- Bed usage percentage
- Daily occupancy (hours/day)
- Personalized AI suggestions

**Usage:**
```bash
python calculate_dashboard.py esp32-a1
```

**Output:**
```
Calculated Metrics:
  Sleep Consistency Score: 78.45/100
  Bedtime Consistency Score: 85.23/100
  Bed Use: 28.33%
  Daily Occupancy: 6.8 hours/day
  Total Interruptions: 75
  Total Nights: 30
  Average Sleep: 7.50 hours/night

✅ Dashboard updated successfully!
```

### 2. View Dashboard

Display calculated metrics and suggestions:

```bash
python view_dashboard.py esp32-a1
```

**Output:**
```
📊 Metrics:
  Sleep Consistency:    78.45/100
  Bedtime Consistency:  85.23/100
  Bed Usage:            28.33%
  Daily Occupancy:      6.8 hours/day
  Average Sleep:        7.50 hours/night

💡 Suggestions:
  🌙 Awakening: Consider reviewing your sleep environment...
  ⏱️  Average Sleep: Great! You're getting 7-9 hours of sleep.
  📅 Consistency: Stick to a regular bedtime and wake time.
```

### 3. Statistical Analysis

Perform detailed sleep analysis:

```bash
python analyze_sleep_data.py esp32-a1
```

**Output:**
```
Sleep Statistics:
  Total sessions: 30
  
  Duration:
    Average: 7.50 hours
    Min: 6.20 hours
    Max: 8.90 hours
  
  Quality Score:
    Average: 82.3/100
    Best: 95/100
    Worst: 68/100
```

---

## 🔧 Python API

### Create Sleep Session

```python
from supabase_api_client import create_sleep_session

session = create_sleep_session(
    device_id="esp32-a1",
    session_start="2024-01-15T22:00:00Z",
    session_end="2024-01-16T06:00:00Z",
    duration_hours=8.0,
    sleep_quality_score=90,
    interruptions=1,
    notes="Excellent sleep"
)
```

### Query Sessions

```python
from supabase_api_client import get_sleep_sessions

# Get all sessions for a device
sessions = get_sleep_sessions(device_id="esp32-a1", limit=100)

# Get sessions in date range
from supabase_api_client import get_sessions_by_date_range
recent = get_sessions_by_date_range("esp32-a1", "2024-01-01T00:00:00Z", "2024-01-31T23:59:59Z")
```

### Calculate Metrics

```python
from calculate_dashboard import calculate_and_update_dashboard

# Calculate and store dashboard metrics
calculate_and_update_dashboard("esp32-a1", days_back=30)
```

---

## 📁 Project Structure

```
somnomat_webservice/
├── .env                          # Supabase credentials
├── supabase_api_client.py       # Core API wrapper
├── calculate_dashboard.py       # Metrics calculator
├── view_dashboard.py            # Dashboard viewer
├── analyze_sleep_data.py        # Statistical analysis
└── seed_sleep_sessions.py       # Test data generator
```

---

## 🐛 Troubleshooting

### "Row-level security policy violated"

Disable RLS in Supabase Dashboard:
- **Table Editor** → **sleep_sessions** → Toggle **RLS** off

### "No module named 'supabase'"

```bash
source ../.webservice/bin/activate
pip install supabase
```

### "SUPABASE_URL not set"

Ensure `.env` file exists with:
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key-here
```

---

## 📚 Resources

- [Supabase Dashboard](https://supabase.com/dashboard/project/xybqmwkxsriatdfvhpym)
- [Supabase Python Docs](https://github.com/supabase-community/supabase-py)
- [Project Documentation](https://supabase.com/docs)

---

**Version:** 0.2.0  
**Last Updated:** January 2025