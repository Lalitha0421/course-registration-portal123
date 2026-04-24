from config import get_connection
from werkzeug.security import generate_password_hash
import random

def seed_faculty_and_data():
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        pw_hash = generate_password_hash("password")
        
        # 0. Get current session
        cursor.execute("SELECT config_value FROM system_config WHERE config_key = 'current_academic_session'")
        row = cursor.fetchone()
        current_session = row[0] if row else "Year 1 Winter"
        print(f"Current Academic Session: {current_session}")

        sample_faculty = [
            (1, 'gaurav@vnit.ac.in', 'Dr. Gaurav Mishra'),
            (2, 'sathe@vnit.ac.in', 'Dr. Sathe'),
            (3, 'tiwari@vnit.ac.in', 'Dr. Tiwari'),
            (10, 'rajesh@vnit.ac.in', 'Dr. Rajesh Kumar'),
            (11, 'anita@vnit.ac.in', 'Dr. Anita Sharma'),
            (12, 'sp@vnit.ac.in', 'P. S. Deshpande')
        ]

        print("Creating Faculty and Users...")
        for fid, email, name in sample_faculty:
            cursor.execute("SELECT user_id FROM users WHERE login_id = :1 AND role = 'faculty'", (email,))
            user_row = cursor.fetchone()
            if not user_row:
                uid = 5000 + fid
                cursor.execute("INSERT INTO users (user_id, login_id, password_hash, role, faculty_id) VALUES (:1, :2, :3, 'faculty', :4)", 
                               (uid, email, pw_hash, fid))
                user_id = uid
            else:
                user_id = user_row[0]
                cursor.execute("UPDATE users SET password_hash = :1, faculty_id = :2 WHERE user_id = :3", (pw_hash, fid, user_id))

            cursor.execute("SELECT faculty_id FROM faculty WHERE faculty_id = :1", (fid,))
            if not cursor.fetchone():
                cursor.execute("INSERT INTO faculty (faculty_id, faculty_name, user_id) VALUES (:1, :2, :3)", (fid, name, user_id))
            else:
                cursor.execute("UPDATE faculty SET faculty_name = :1, user_id = :2 WHERE faculty_id = :3", (name, user_id, fid))
            print(f"  - {name} ({email}) linked.")

        cursor.execute("SELECT course_id, course_code FROM course_master FETCH FIRST 10 ROWS ONLY")
        available_courses = cursor.fetchall()
        
        if not available_courses:
            print("No courses found in course_master.")
            return

        print("\nAssigning Courses to Faculty...")
        base_iid = 1000
        for i, (fid, email, name) in enumerate(sample_faculty):
            for j in range(2):
                course_idx = (i * 2 + j) % len(available_courses)
                cid, ccode = available_courses[course_idx]
                cursor.execute("SELECT instance_id FROM course_instance WHERE faculty_id = :1 AND course_id = :2 AND academic_session = :3", 
                               (fid, cid, current_session))
                if not cursor.fetchone():
                    iid = base_iid + (i * 10) + j
                    cursor.execute("""
                        INSERT INTO course_instance (instance_id, faculty_id, course_id, academic_session, semester, section, batch, slot)
                        VALUES (:1, :2, :3, :4, :5, :6, 'All', :7)
                    """, (iid, fid, cid, current_session, 6, 'A' if j==0 else 'B', str(j+1)))
                    print(f"  - Assigned {ccode} to {name} (Inst: {iid})")

        print("\nRegistering Students to Courses...")
        cursor.execute("SELECT student_id FROM students WHERE status IN ('APPROVED', 'ACTIVE') FETCH FIRST 20 ROWS ONLY")
        student_ids = [r[0] for r in cursor.fetchall()]
        
        if not student_ids:
            print("No approved students found.")
        else:
            cursor.execute("SELECT instance_id FROM course_instance WHERE academic_session = :1", (current_session,))
            instance_ids = [r[0] for r in cursor.fetchall()]

            for sid in student_ids:
                cursor.execute("SELECT reg_id FROM student_registration WHERE student_id = :1 AND academic_session = :2", (sid, current_session))
                reg_row = cursor.fetchone()
                if not reg_row:
                    try:
                        cursor.execute("""
                            INSERT INTO student_registration (student_id, academic_session, semester, status, registration_date)
                            VALUES (:1, :2, 6, 'APPROVED', SYSDATE)
                        """, (sid, current_session))
                        cursor.execute("SELECT reg_id FROM student_registration WHERE student_id = :1 AND academic_session = :2", (sid, current_session))
                        reg_id = cursor.fetchone()[0]
                    except Exception as e:
                        print(f"Failed to insert registration for student {sid}: {e}")
                        continue
                else:
                    reg_id = reg_row[0]
                    cursor.execute("UPDATE student_registration SET status = 'APPROVED' WHERE reg_id = :1", (reg_id,))

                for k in range(3):
                    iid = instance_ids[(sid + k) % len(instance_ids)]
                    cursor.execute("SELECT 1 FROM student_registration_courses WHERE reg_id = :1 AND course_instance_id = :2", (reg_id, iid))
                    if not cursor.fetchone():
                        cursor.execute("INSERT INTO student_registration_courses (reg_id, course_instance_id, course_type) VALUES (:1, :2, 'DC')", (reg_id, iid))

            print(f"  - Registered {len(student_ids)} students to course instances.")

        print("\nInitializing Attendance...")
        cursor.execute("""
            SELECT sr.student_id, src.course_instance_id 
            FROM student_registration_courses src
            JOIN student_registration sr ON src.reg_id = sr.reg_id
            WHERE sr.academic_session = :1
        """, (current_session,))
        registrations = cursor.fetchall()

        att_id = 9000
        for sid, iid in registrations:
            if random.random() > 0.3:
                # Manual upsert to handle missing identity/sequence
                cursor.execute("SELECT attendance_id FROM attendance WHERE student_id = :1 AND course_instance_id = :2", (sid, iid))
                row = cursor.fetchone()
                perc = random.randint(60, 100)
                if row:
                    cursor.execute("UPDATE attendance SET attendance_percentage = :1 WHERE attendance_id = :2", (perc, row[0]))
                else:
                    try:
                        # Try without ID first (in case it is identity)
                        cursor.execute("INSERT INTO attendance (student_id, course_instance_id, attendance_percentage) VALUES (:1, :2, :3)", (sid, iid, perc))
                    except:
                        # Try with manual ID
                        cursor.execute("INSERT INTO attendance (attendance_id, student_id, course_instance_id, attendance_percentage) VALUES (:1, :2, :3, :4)", (att_id, sid, iid, perc))
                        att_id += 1

        conn.commit()
        print("\nDatabase Seeded Successfully!")
        print("\n--- TEST LOGINS ---")
        for fid, email, name in sample_faculty:
            print(f"Faculty: {name:20} | Login: {email:20} | Password: password")

    except Exception as e:
        print(f"Error seeding database: {e}")
        import traceback
        traceback.print_exc()
        if conn: conn.rollback()
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

if __name__ == "__main__":
    seed_faculty_and_data()
