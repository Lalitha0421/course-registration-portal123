import sqlite3
import os

def create_demo_db():
    db_path = 'demo_database.db'
    if os.path.exists(db_path):
        os.remove(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("🛠️ Creating SQLite tables for Demo...")

    # 1. SYSTEM_CONFIG
    cursor.execute("CREATE TABLE system_config (config_key TEXT PRIMARY KEY, config_value TEXT, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    cursor.execute("INSERT INTO system_config (config_key, config_value) VALUES ('current_academic_session', 'W25')")
    cursor.execute("INSERT INTO system_config (config_key, config_value) VALUES ('registration_status', 'OPEN')")

    # 2. STUDENTS
    cursor.execute("""
        CREATE TABLE students (
            student_id INTEGER PRIMARY KEY AUTOINCREMENT,
            enrollment_no TEXT UNIQUE,
            name TEXT,
            email TEXT,
            mobile TEXT,
            semester INTEGER,
            program TEXT,
            advisor_id INTEGER,
            status TEXT,
            registration_date TIMESTAMP,
            address TEXT,
            is_hosteller TEXT
        )
    """)

    # 3. USERS
    cursor.execute("""
        CREATE TABLE users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            login_id TEXT UNIQUE,
            password_hash TEXT,
            role TEXT,
            student_id INTEGER,
            faculty_id INTEGER
        )
    """)

    # 4. COURSE_MASTER
    cursor.execute("""
        CREATE TABLE course_master (
            course_id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_code TEXT UNIQUE,
            course_title TEXT,
            course_type TEXT,
            program TEXT,
            L INTEGER, T INTEGER, P INTEGER,
            credits INTEGER
        )
    """)

    # 5. COURSE_INSTANCE
    cursor.execute("""
        CREATE TABLE course_instance (
            instance_id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER,
            faculty_id INTEGER,
            academic_session TEXT,
            semester INTEGER,
            section TEXT,
            batch TEXT,
            slot TEXT
        )
    """)

    # 6. FACULTY
    cursor.execute("""
        CREATE TABLE faculty (
            faculty_id INTEGER PRIMARY KEY AUTOINCREMENT,
            faculty_name TEXT,
            email TEXT,
            department TEXT
        )
    """)

    # 7. REGISTRATIONS
    cursor.execute("""
        CREATE TABLE student_registration (
            reg_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            semester INTEGER,
            academic_session TEXT,
            status TEXT,
            registration_date TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE student_registration_courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reg_id INTEGER,
            course_instance_id INTEGER,
            course_type TEXT
        )
    """)

    # 8. RESULTS & ATTENDANCE
    cursor.execute("CREATE TABLE results (result_id INTEGER PRIMARY KEY, student_id INTEGER, course_id INTEGER, academic_session TEXT, grade TEXT)")
    cursor.execute("CREATE TABLE attendance (attendance_id INTEGER PRIMARY KEY, student_id INTEGER, course_instance_id INTEGER, attendance_percentage REAL)")

    # 9. OBE TABLES
    cursor.execute("CREATE TABLE course_outcomes (outcome_id INTEGER PRIMARY KEY, course_id INTEGER, outcome_desc TEXT, print_seq INTEGER)")
    cursor.execute("CREATE TABLE course_objectives (obj_id INTEGER PRIMARY KEY, course_id INTEGER, description TEXT, print_seq INTEGER)")
    cursor.execute("CREATE TABLE program_outcomes (po_id INTEGER PRIMARY KEY, po_code TEXT, po_description TEXT)")
    cursor.execute("CREATE TABLE co_po_mapping (id INTEGER PRIMARY KEY, course_outcome_id INTEGER, program_outcome_id INTEGER, weightage INTEGER)")

    # --- SEED SAMPLE DATA ---
    print("🌱 Seeding sample data...")
    
    # Faculty
    cursor.execute("INSERT INTO faculty (faculty_name, email, department) VALUES ('Dr. Rajesh Gupta', 'rgupta@vnit.ac.in', 'CSE')")
    
    # Students (Password is 'password123')
    from werkzeug.security import generate_password_hash
    pw = generate_password_hash('password123')
    cursor.execute("INSERT INTO students (enrollment_no, name, program, semester, email, status) VALUES ('B21CS001', 'Lalitha', 'CSE', 6, 'lalitha@example.com', 'APPROVED')")
    cursor.execute("INSERT INTO users (login_id, password_hash, role, student_id) VALUES ('B21CS001', ?, 'student', 1)", (pw,))

    # Courses
    cursor.execute("INSERT INTO course_master (course_code, course_title, course_type, program, credits) VALUES ('CSL312', 'Database Management Systems', 'DC', 'CSE', 4)")
    cursor.execute("INSERT INTO course_master (course_code, course_title, course_type, program, credits) VALUES ('CSL313', 'Operating Systems', 'DC', 'CSE', 4)")
    cursor.execute("INSERT INTO course_master (course_code, course_title, course_type, program, credits) VALUES ('CSE401', 'Cloud Computing', 'DE', 'CSE', 3)")
    cursor.execute("INSERT INTO course_master (course_code, course_title, course_type, program, credits) VALUES ('CSE402', 'Machine Learning', 'DE', 'CSE', 3)")

    # Instance
    cursor.execute("INSERT INTO course_instance (course_id, faculty_id, academic_session, section) VALUES (1, 1, 'W25', 'A')")
    cursor.execute("INSERT INTO course_instance (course_id, faculty_id, academic_session, section) VALUES (2, 1, 'W25', 'B')")
    cursor.execute("INSERT INTO course_instance (course_id, faculty_id, academic_session, section) VALUES (3, 1, 'W25', 'A')")
    cursor.execute("INSERT INTO course_instance (course_id, faculty_id, academic_session, section) VALUES (4, 1, 'W25', 'B')")

    conn.commit()
    conn.close()
    print("✅ Demo database created successfully!")

if __name__ == "__main__":
    create_demo_db()
