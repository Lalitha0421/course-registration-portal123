from config import get_connection
import random

def populate_all_students_history():
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Get all approved students
        cursor.execute("SELECT student_id, name FROM students WHERE enrollment_no IS NOT NULL")
        students = cursor.fetchall()
        print(f"Found {len(students)} approved students.")

        # Get some course IDs for results
        cursor.execute("SELECT course_id FROM course_master FETCH FIRST 10 ROWS ONLY")
        course_ids = [r[0] for r in cursor.fetchall()]
        
        if len(course_ids) < 3:
            print("Not enough courses.")
            return

        sessions = [('Year 1 Summer', 1), ('Year 1 Winter', 2)]

        for sid, name in students:
            print(f"Processing student: {name} (ID: {sid})")
            
            for sess, sem in sessions:
                # 1. Add registration history
                cursor.execute("SELECT reg_id FROM student_registration WHERE student_id = :1 AND academic_session = :2", (sid, sess))
                if not cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO student_registration (student_id, academic_session, semester, status, registration_date)
                        VALUES (:1, :2, :3, 'APPROVED', SYSDATE - 200)
                    """, (sid, sess, sem))
            
            # 2. Add some results
            # Every student gets 1 pass, 1 backlog (FF), 1 backlog (W)
            # Pass
            cursor.execute("SELECT 1 FROM results WHERE student_id = :1 AND course_id = :2", (sid, course_ids[0]))
            if not cursor.fetchone():
                cursor.execute("INSERT INTO results (result_id, student_id, course_id, grade, academic_session, semester) VALUES (RESULTS_SEQ.NEXTVAL, :1, :2, 'BC', 'Year 1 Summer', 1)", (sid, course_ids[0]))
            
            # Backlog FF
            cursor.execute("SELECT 1 FROM results WHERE student_id = :1 AND course_id = :2", (sid, course_ids[1]))
            if not cursor.fetchone():
                cursor.execute("INSERT INTO results (result_id, student_id, course_id, grade, academic_session, semester) VALUES (RESULTS_SEQ.NEXTVAL, :1, :2, 'FF', 'Year 1 Winter', 2)", (sid, course_ids[1]))

            # Backlog W
            cursor.execute("SELECT 1 FROM results WHERE student_id = :1 AND course_id = :2", (sid, course_ids[2]))
            if not cursor.fetchone():
                cursor.execute("INSERT INTO results (result_id, student_id, course_id, grade, academic_session, semester) VALUES (RESULTS_SEQ.NEXTVAL, :1, :2, 'W', 'Year 1 Winter', 2)", (sid, course_ids[2]))

        conn.commit()
        print("\nAll students populated with history and backlogs.")

    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    populate_all_students_history()
