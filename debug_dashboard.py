from config import get_connection

def test_dashboard_logic(student_id):
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # 1. Fetch Student Details
        cursor.execute("SELECT program, enrollment_no, name FROM students WHERE student_id = :1", (student_id,))
        student_data = cursor.fetchone()
        print(f"Student Data: {student_data}")

        # 2. CGPA
        cursor.execute("""
            SELECT SUM(points * credits) / NULLIF(SUM(credits), 0)
            FROM (
                SELECT r.grade, cm.credits,
                CASE r.grade
                    WHEN 'AA' THEN 10 WHEN 'AB' THEN 9 WHEN 'BB' THEN 8
                    WHEN 'BC' THEN 7 WHEN 'CC' THEN 6 WHEN 'CD' THEN 5
                    WHEN 'DD' THEN 4 ELSE 0 END AS points
                FROM results r
                JOIN course_master cm ON r.course_id = cm.course_id
                WHERE r.student_id = :1
            )
        """, (student_id,))
        cgpa_row = cursor.fetchone()
        print(f"CGPA Row: {cgpa_row}")

        # 4. Fetch Active Courses
        cursor.execute("""
            SELECT academic_session, status, reg_id FROM student_registration 
            WHERE student_id = :1 
            ORDER BY registration_date DESC FETCH FIRST 1 ROWS ONLY
        """, (student_id,))
        last_reg = cursor.fetchone()
        print(f"Last Reg: {last_reg}")

        # 5. available_sessions
        cursor.execute("SELECT DISTINCT academic_session FROM course_instance ORDER BY academic_session DESC")
        available_sessions = [row[0] for row in cursor.fetchall()]
        print(f"Available Sessions: {available_sessions}")

    except Exception as e:
        print(f"Logic Failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    test_dashboard_logic(113)
