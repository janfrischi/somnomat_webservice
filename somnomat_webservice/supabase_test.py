import os
from dotenv import load_dotenv
import psycopg2
from sqlalchemy import create_engine, text

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

print("=" * 60)
print("Testing Supabase Connection")
print("=" * 60)

# Test 1: Direct psycopg2 connection
print("\n1. Testing direct connection with psycopg2...")
try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()
    print(f"✅ Connected successfully!")
    print(f"   PostgreSQL version: {version[0][:50]}...")
    cursor.close()
    conn.close()
except Exception as e:
    print(f"❌ Connection failed: {e}")
    exit(1)

# Test 2: SQLAlchemy engine connection
print("\n2. Testing SQLAlchemy engine...")
try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT current_database();"))
        db_name = result.fetchone()[0]
        print(f"✅ SQLAlchemy connected!")
        print(f"   Database: {db_name}")
except Exception as e:
    print(f"❌ SQLAlchemy connection failed: {e}")
    exit(1)

print("\n" + "=" * 60)
print("🎉 All connection tests passed!")
print("=" * 60)