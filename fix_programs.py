import oracledb
import os
from dotenv import load_dotenv

load_dotenv()

def fix():
    try:
        conn = oracledb.connect(
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            dsn=os.getenv("DB_DSN")
        )
        cursor = conn.cursor()
        
        # Set Lalitha to B.TECH
        cursor.execute("UPDATE students SET program = 'B.TECH' WHERE LOWER(name) LIKE '%lalitha%'")
        print(f"Updated {cursor.rowcount} students named Lalitha to B.TECH")
        
        # Ensure all existing courses match exactly 'B.TECH' or 'M.TECH'
        cursor.execute("UPDATE course_master SET program = 'B.TECH' WHERE UPPER(program) LIKE 'B%TECH%'")
        cursor.execute("UPDATE course_master SET program = 'M.TECH' WHERE UPPER(program) LIKE 'M%TECH%'")
        
        conn.commit()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'conn' in locals(): conn.close()

if __name__ == "__main__": fix()
