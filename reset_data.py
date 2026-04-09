import oracledb
import os
from dotenv import load_dotenv

load_dotenv()

def cleanup():
    try:
        conn = oracledb.connect(
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            dsn=os.getenv("DB_DSN")
        )
        cursor = conn.cursor()
        
        print("--- CLEANING DATABASE FOR FRESH COURSE POPULATION ---")
        
        # 1. Delete all current registrations (to avoid foreign key issues during instance cleanup)
        cursor.execute("DELETE FROM student_registration_courses")
        cursor.execute("DELETE FROM student_registration")
        print("Deleted all registrations")
        
        # 2. Delete all course instances
        cursor.execute("DELETE FROM course_instance")
        print("Deleted all course instances")
        
        # 3. Clean Course Master (optional, but good to keep it strictly to what we want)
        # cursor.execute("DELETE FROM course_master") 
        # print("Deleted all course masters")
        
        conn.commit()
        print("Database cleaned. Now running population...")
        
    except Exception as e:
        print(f"Error during cleanup: {e}")
    finally:
        if 'conn' in locals(): conn.close()

if __name__ == "__main__":
    cleanup()
    # Now trigger population
    from populate_data import populate
    populate()
