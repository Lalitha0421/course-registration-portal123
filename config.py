import oracledb
import os
from dotenv import load_dotenv

# Load from .env file
load_dotenv()

def get_connection():
    """
    Establishes a connection to the Oracle Database.
    Automatically handles Thin mode for OCI Cloud/Local XE.
    """
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    dsn = os.getenv("DB_DSN")

    try:
        # oracledb.connect automatically detects Thin mode (no Wallet/Instant Client needed for most Cloud setups)
        connection = oracledb.connect(
            user=user,
            password=password,
            dsn=dsn,
            retry_count=5,     # Essential for cloud stability
            retry_delay=3
        )
        return connection
    except Exception as e:
        print(f"❌ [DB ERROR] {str(e)}")
        # Provide helpful hint for Cloud users
        if "TCPS" in dsn or "oraclecloud.com" in dsn:
            print("💡 Hint: Ensure your OCI Security List allows outbound traffic on port 1522.")
        raise e

if __name__ == "__main__":
    # Test connection if run directly
    try:
        conn = get_connection()
        print("✅ Database connection successful!")
        conn.close()
    except:
        print("🛑 Connection failed.")
