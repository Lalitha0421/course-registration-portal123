from config import get_connection

def check_dropdown_data():
    conn = get_connection()
    cursor = conn.cursor()
    
    print("--- Sessions in COURSE_INSTANCE ---")
    cursor.execute("SELECT DISTINCT academic_session FROM course_instance")
    print(cursor.fetchall())
    
    print("\n--- Sessions in STUDENT_REGISTRATION ---")
    cursor.execute("SELECT DISTINCT academic_session FROM student_registration")
    print(cursor.fetchall())
    
    print("\n--- Students Count ---")
    cursor.execute("SELECT count(*) FROM students")
    print(cursor.fetchone())
    
    conn.close()

if __name__ == "__main__":
    check_dropdown_data()
