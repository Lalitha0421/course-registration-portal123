import oracledb
import os
from dotenv import load_dotenv

# 1. Load Credentials
load_dotenv()
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASSWORD")
DB_DSN = os.getenv("DB_DSN")

def diagnose():
    print(f"--- DATABASE DIAGNOSTICS (Connecting to {DB_DSN} as {DB_USER}) ---")
    try:
        conn = oracledb.connect(user=DB_USER, password=DB_PASS, dsn=DB_DSN)
        cursor = conn.cursor()

        # 1. List all tables
        print("\n[1] Tables found in this schema:")
        cursor.execute("SELECT table_name FROM user_tables ORDER BY table_name")
        tables = [row[0] for row in cursor.fetchall()]
        for t in tables:
            print(f" - {t}")

        # 2. Check USERS, STUDENTS, & RESULTS
        for target in ["USERS", "STUDENTS", "RESULTS"]:
            print(f"\n[2] Attributes (Columns) for {target}:")
            cursor.execute(f"SELECT column_name, data_type FROM user_tab_columns WHERE table_name = '{target}'")
            cols = cursor.fetchall()
            if not cols:
                print(f" - WARNING: Table {target} not found or has no columns!")
            for col in cols:
                print(f" - {col[0]} ({col[1]})")

        # 3. Check Academic Sessions
        print("\n[3] Unique Sessions in COURSE_INSTANCE:")
        cursor.execute("SELECT DISTINCT academic_session FROM course_instance")
        for row in cursor.fetchall():
            print(f" - {row[0]}")

        # 5. Check System Config
        print("\n[5] System Configuration (SYSTEM_CONFIG):")
        cursor.execute("SELECT config_key, config_value FROM system_config")
        for row in cursor.fetchall():
            print(f" - {row[0]}: {row[1]}")

        cursor.close()
        conn.close()
    except Exception as e:
        print(f"\n[ERROR] Diagnostic script failed: {str(e)}")

if __name__ == "__main__":
    diagnose()
