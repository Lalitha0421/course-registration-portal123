import oracledb
import os
from dotenv import load_dotenv

# Load from .env file
load_dotenv()

def get_connection():
    """
    Establishes a connection to the Database.
    Supports Oracle (Thin Mode) and falls back to SQLite for easy deployment.
    """
    db_type = os.getenv("DB_TYPE", "ORACLE").upper()
    
    # --- ORACLE CONNECTION ---
    if db_type == "ORACLE":
        user = os.getenv("DB_USER")
        password = os.getenv("DB_PASSWORD")
        dsn = os.getenv("DB_DSN")
        
        if not user or not dsn:
            print("⚠️ Oracle credentials missing. Falling back to SQLite for Demo...")
            return get_sqlite_connection()

        try:
            connection = oracledb.connect(
                user=user,
                password=password,
                dsn=dsn,
                retry_count=5
            )
            return connection
        except Exception as e:
            print(f"❌ [Oracle Error] {str(e)}. Falling back to SQLite...")
            return get_sqlite_connection()
            
    # --- SQLITE CONNECTION (DEMO MODE) ---
    else:
        return get_sqlite_connection()

def get_sqlite_connection():
    import sqlite3
    db_path = os.path.join(os.path.dirname(__file__), 'demo_database.db')
    conn = sqlite3.connect(db_path, check_same_thread=False)
    # Enable Dictionary-like access
    conn.row_factory = sqlite3.Row
    return conn

# Mock cursor wrapper for SQLite to behave like Oracle cursor
class OracleCompatibleCursor:
    def __init__(self, sqlite_cursor):
        self.cursor = sqlite_cursor
    def execute(self, sql, params=()):
        # Convert Oracle :1, :sid placeholders to SQLite ?
        import re
        sql = re.sub(r':\w+', '?', sql)
        return self.cursor.execute(sql, params)
    def fetchone(self): return self.cursor.fetchone()
    def fetchall(self): return self.cursor.fetchall()
    def close(self): self.cursor.close()

if __name__ == "__main__":
    # Test connection if run directly
    try:
        conn = get_connection()
        print("✅ Database connection successful!")
        conn.close()
    except:
        print("🛑 Connection failed.")
