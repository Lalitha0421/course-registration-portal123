import oracledb
import os
from dotenv import load_dotenv

# 1. Load Credentials
load_dotenv()
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASSWORD")
DB_DSN = os.getenv("DB_DSN")

def sync():
    print("--- SYNCING USER_ID LINKS ---")
    try:
        conn = oracledb.connect(user=DB_USER, password=DB_PASS, dsn=DB_DSN)
        cursor = conn.cursor()

        # Get all users (student role)
        cursor.execute("SELECT user_id, login_id FROM users WHERE role = 'student'")
        users = cursor.fetchall()
        
        updated_count = 0
        for user_id, login_id in users:
            # Attempt to find the matching student. 
            # In your system, login_id is usually the enrollment_no for approved students
            print(f"Propagating link: User {login_id} (ID: {user_id})")
            
            # Update STUDENTS where enrollment_no matches login_id
            cursor.execute("""
                UPDATE students 
                SET user_id = :1 
                WHERE enrollment_no = :2 OR email = :3
            """, (user_id, login_id, login_id))
            
            if cursor.rowcount > 0:
                print(f" - Successfully linked to student record.")
                updated_count += cursor.rowcount
            else:
                print(f" - No matching student found for this login ID.")

        conn.commit()
        print(f"\n[DONE] Linked {updated_count} student records to their user accounts.")
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Sync failed: {str(e)}")

if __name__ == "__main__":
    sync()
