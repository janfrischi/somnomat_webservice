"""
Basic Streamlit Debug App
Tests environment, imports, and Supabase connection
"""
import streamlit as st
import sys
import os
from datetime import datetime

# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="Somnomat Debug",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 Somnomat Debug Dashboard")
st.markdown("---")

# ==================== ENVIRONMENT INFO ====================
st.header("1️⃣ Environment Information")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Python Environment")
    st.code(f"""
Python Version: {sys.version}
Python Executable: {sys.executable}
Current Working Directory: {os.getcwd()}
Script Location: {__file__}
    """)

with col2:
    st.subheader("Streamlit Info")
    st.code(f"""
Streamlit Version: {st.__version__}
Running in Streamlit: True
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """)

st.markdown("---")

# ==================== SECRETS CHECK ====================
st.header("2️⃣ Secrets Configuration")

try:
    # Check if secrets exist
    if hasattr(st, 'secrets'):
        st.success("✅ Streamlit secrets are available")
        
        # List available secret keys
        available_keys = list(st.secrets.keys())
        st.write(f"**Available secret keys ({len(available_keys)}):**")
        st.code("\n".join(available_keys))
        
        # Check for Supabase secrets
        col1, col2 = st.columns(2)
        
        with col1:
            if "SUPABASE_URL_CALMEA" in st.secrets:
                st.success("✅ SUPABASE_URL_CALMEA found")
                url = st.secrets["SUPABASE_URL_CALMEA"]
                st.code(f"URL: {url[:30]}...")
            else:
                st.error("❌ SUPABASE_URL_CALMEA not found")
        
        with col2:
            if "SUPABASE_KEY_CALMEA" in st.secrets:
                st.success("✅ SUPABASE_KEY_CALMEA found")
                key = st.secrets["SUPABASE_KEY_CALMEA"]
                st.code(f"Key: {key[:20]}...{key[-10:]}")
            else:
                st.error("❌ SUPABASE_KEY_CALMEA not found")
    else:
        st.error("❌ Streamlit secrets not available")
        
except Exception as e:
    st.error(f"❌ Error checking secrets: {e}")
    st.code(str(e))

st.markdown("---")

# ==================== IMPORT TESTS ====================
st.header("3️⃣ Import Tests")

imports_to_test = [
    ("pandas", "import pandas as pd"),
    ("plotly", "import plotly.express as px"),
    ("PIL", "from PIL import Image"),
    ("supabase", "from supabase import create_client"),
    ("SupabaseAuthClient", "from supabase_auth_client import SupabaseAuthClient"),
    ("supabase_api_client_somnomat", "from supabase_api_client_somnomat import get_device_by_id"),
    ("calculate_dashboard", "from calculate_dashboard import process_occupancy_into_sessions"),
]

col1, col2 = st.columns(2)

for i, (name, import_stmt) in enumerate(imports_to_test):
    target_col = col1 if i % 2 == 0 else col2
    
    with target_col:
        try:
            exec(import_stmt)
            st.success(f"✅ {name}")
        except Exception as e:
            st.error(f"❌ {name}")
            with st.expander(f"Error details for {name}"):
                st.code(str(e))

st.markdown("---")

# ==================== SUPABASE CONNECTION TEST ====================
st.header("4️⃣ Supabase Connection Test")

if st.button("🔌 Test Supabase Connection", use_container_width=True):
    try:
        from supabase import create_client
        
        url = st.secrets.get("SUPABASE_URL_CALMEA")
        key = st.secrets.get("SUPABASE_KEY_CALMEA")
        
        if not url or not key:
            st.error("❌ Missing Supabase credentials in secrets")
        else:
            with st.spinner("Connecting to Supabase..."):
                # Create client
                supabase = create_client(url, key)
                st.success("✅ Supabase client created")
                
                # Test a simple query
                try:
                    response = supabase.table("devices").select("id, name").limit(5).execute()
                    st.success(f"✅ Successfully queried devices table")
                    st.write(f"**Found {len(response.data)} devices:**")
                    
                    if response.data:
                        import pandas as pd
                        df = pd.DataFrame(response.data)
                        st.dataframe(df, use_container_width=True)
                    else:
                        st.info("No devices found in database")
                        
                except Exception as e:
                    st.error(f"❌ Error querying database: {e}")
                    st.code(str(e))
                    
    except Exception as e:
        st.error(f"❌ Connection failed: {e}")
        st.code(str(e))

st.markdown("---")

# ==================== AUTH CLIENT TEST ====================
st.header("5️⃣ Authentication Client Test")

if st.button("🔐 Test Auth Client", use_container_width=True):
    try:
        from supabase_auth_client import SupabaseAuthClient
        
        with st.spinner("Initializing auth client..."):
            auth_client = SupabaseAuthClient()
            st.success("✅ Auth client initialized")
            
            # Check for existing session
            user = auth_client.get_current_user()
            
            if user:
                st.success(f"✅ User session found: {user.email}")
                st.json({
                    "email": user.email,
                    "id": user.id,
                    "created_at": str(user.created_at)
                })
            else:
                st.info("ℹ️ No active user session")
                st.write("You can sign in using the main dashboard")
                
    except Exception as e:
        st.error(f"❌ Auth client error: {e}")
        st.code(str(e))
        import traceback
        st.code(traceback.format_exc())

st.markdown("---")

# ==================== SESSION STATE ====================
st.header("6️⃣ Session State")

with st.expander("📦 View Session State"):
    st.write("**Session State Keys:**")
    if st.session_state:
        for key in st.session_state.keys():
            st.write(f"- `{key}`")
    else:
        st.info("Session state is empty")

st.markdown("---")

# ==================== FILE SYSTEM ====================
st.header("7️⃣ File System Check")

files_to_check = [
    "calmea.png",
    "supabase_auth_client.py",
    "supabase_api_client_somnomat.py",
    "calculate_dashboard.py",
    "somnomat_dashboard.py",
    ".env",
]

col1, col2 = st.columns(2)

for i, filename in enumerate(files_to_check):
    target_col = col1 if i % 2 == 0 else col2
    
    with target_col:
        filepath = os.path.join(os.path.dirname(__file__), filename)
        if os.path.exists(filepath):
            st.success(f"✅ {filename}")
        else:
            st.warning(f"⚠️ {filename} not found")

st.markdown("---")

# ==================== MANUAL TESTS ====================
st.header("8️⃣ Manual Tests")

st.subheader("Test Custom Code")

code_to_test = st.text_area(
    "Enter Python code to test:",
    value="# Test code here\nimport pandas as pd\ndf = pd.DataFrame({'col1': [1, 2], 'col2': [3, 4]})\ndf",
    height=150
)

if st.button("▶️ Run Code", use_container_width=True):
    try:
        # Create a safe execution environment
        exec_globals = {
            'st': st,
            'pd': None,
            'px': None,
        }
        
        # Try to import commonly used modules
        try:
            import pandas as pd
            exec_globals['pd'] = pd
        except:
            pass
            
        try:
            import plotly.express as px
            exec_globals['px'] = px
        except:
            pass
        
        # Execute the code
        exec(code_to_test, exec_globals)
        st.success("✅ Code executed successfully")
        
    except Exception as e:
        st.error(f"❌ Execution error: {e}")
        st.code(str(e))
        import traceback
        st.code(traceback.format_exc())

st.markdown("---")

# ==================== REFRESH ====================
st.header("9️⃣ Controls")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔄 Refresh Page", use_container_width=True):
        st.rerun()

with col2:
    if st.button("🗑️ Clear Cache", use_container_width=True):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.success("✅ Cache cleared")

with col3:
    if st.button("🔓 Clear Session", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.success("✅ Session cleared")
        st.rerun()

# ==================== FOOTER ====================
st.markdown("---")
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.caption("Somnomat Debug Dashboard v1.0")