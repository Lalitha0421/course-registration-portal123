import oracledb
import os
from dotenv import load_dotenv

load_dotenv()

def normalize():
    try:
        conn = oracledb.connect(
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            dsn=os.getenv("DB_DSN")
        )
        cursor = conn.cursor()

        # Normalize Course Master
        cursor.execute("UPDATE course_master SET program = 'B.TECH' WHERE UPPER(program) LIKE 'B%TECH%' OR UPPER(program) LIKE 'BTECH%'")
        print(f"Updated {cursor.rowcount} courses to B.TECH")
        
        cursor.execute("UPDATE course_master SET program = 'M.TECH' WHERE UPPER(program) LIKE 'M%TECH%' OR UPPER(program) LIKE 'MTECH%'")
        print(f"Updated {cursor.rowcount} courses to M.TECH")

        # Normalize Students
        cursor.execute("UPDATE students SET program = 'B.TECH' WHERE UPPER(program) LIKE 'B%TECH%' OR UPPER(program) LIKE 'BTECH%'")
        print(f"Updated {cursor.rowcount} students to B.TECH")
        
        cursor.execute("UPDATE students SET program = 'M.TECH' WHERE UPPER(program) LIKE 'M%TECH%' OR UPPER(program) LIKE 'MTECH%'")
        print(f"Updated {cursor.rowcount} students to M.TECH")

        conn.commit()
        print("Normalization complete.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'conn' in locals(): conn.close()

if __name__ == "__main__":
    normalize()
