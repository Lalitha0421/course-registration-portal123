import oracledb
import os
from dotenv import load_dotenv

# Load from .env file
load_dotenv()

def get_connection():
    try:
        connection = oracledb.connect(
            user=os.getenv("DB_USER", "LALITHA"),
            password=os.getenv("DB_PASSWORD", "MyNewPassword123"),
            dsn=os.getenv("DB_DSN", "localhost:1521/XEPDB1")
        )
        return connection
    except Exception as e:
        print(f"[FATAL] Could not connect to Oracle: {str(e)}")
        raise e
