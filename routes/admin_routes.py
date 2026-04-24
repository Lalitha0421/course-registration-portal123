# course_portal/routes/admin_routes.py

from flask import Blueprint, render_template, request, session, flash, redirect, url_for, Response, make_response
from config import get_connection
import pandas as pd
import io
from werkzeug.security import generate_password_hash
from utils.email_utils import notify_student_approval, notify_registration_approval

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# ────────────────────────────────────────────────
# ADMIN DASHBOARD
# ────────────────────────────────────────────────
@admin_bp.route('/dashboard')
def dashboard():
    if session.get('role') != 'admin':
        flash('Access denied – Admin only', 'danger')
        return redirect(url_for('auth.login_page'))  # assuming login is in auth blueprint
    return render_template('admin_dashboard.html')


# ────────────────────────────────────────────────
# ADD COURSE
# ────────────────────────────────────────────────
@admin_bp.route('/add_course', methods=['GET', 'POST'])
def add_course():
    if session.get('role') != 'admin':
        flash('Admin access required', 'danger')
        return redirect(url_for('auth.login_page'))

    if request.method == 'GET':
        return render_template('add_course.html')

    # POST: process form
    conn = None
    cursor = None
    try:
        course_code   = request.form.get('course_code', '').strip().upper()
        course_title  = request.form.get('course_title', '').strip()
        credits_str   = request.form.get('credits', '0')
        credits       = int(credits_str) if credits_str.isdigit() else 0
        course_type   = request.form.get('course_type', '').strip().upper()
        year          = request.form.get('year', '1')
        semester      = request.form.get('semester', 'Summer')

        if not course_code or not course_title:
            flash('Course code and title are required', 'warning')
            return redirect(url_for('admin.add_course'))

        conn = get_connection()
        cursor = conn.cursor()

        # 0. Check if course already exists
        cursor.execute("SELECT course_id FROM course_master WHERE course_code = :1", (course_code,))
        if cursor.fetchone():
            flash(f'Course {course_code} already exists in Master.', 'warning')
            return redirect(url_for('admin.add_course'))

        # Build academic session string
        academic_session = f"Year {year} {semester}"
        
        # ORA-01722 Fix: semester in DB is a NUMBER. Map text to number.
        try:
            semester_num = (int(year) * 2 - 1) if semester == 'Summer' else (int(year) * 2)
        except:
            semester_num = 1

        # 1. Create Course Master (Manual ID as DB is not IDENTITY)
        cursor.execute("SELECT NVL(MAX(course_id), 0) + 1 FROM course_master")
        course_id = cursor.fetchone()[0]

        cursor.execute("""
            INSERT INTO course_master (
                course_id, course_code, course_title, course_type,
                program, L, T, P, credits
            ) VALUES (:1, :2, :3, :4, 'B.TECH', 0, 0, 0, :5)
        """, (course_id, course_code, course_title, course_type, credits))

        # 2. Create Course Instance (Manual ID)
        cursor.execute("SELECT NVL(MAX(instance_id), 0) + 1 FROM course_instance")
        instance_id = cursor.fetchone()[0]

        cursor.execute("""
            INSERT INTO course_instance (
                instance_id, course_id, academic_session, semester
            ) VALUES (:1, :2, :3, :4)
        """, (instance_id, course_id, academic_session, semester_num))

        conn.commit()
        flash(f'Course {course_code} added successfully!', 'success')

    except Exception as e:
        flash(f'Error adding course: {str(e)}', 'danger')
        if conn: conn.rollback()

    finally:
        if cursor: cursor.close()
        if conn: conn.close()

    return redirect(url_for('admin.dashboard'))


# ────────────────────────────────────────────────
# ADD FACULTY
# ────────────────────────────────────────────────
@admin_bp.route('/add_faculty', methods=['GET', 'POST'])
def add_faculty():
    if session.get('role') != 'admin':
        flash('Admin access required', 'danger')
        return redirect(url_for('auth.login_page'))

    if request.method == 'GET':
        return render_template('add_faculty.html')

    conn = None
    cursor = None
    try:
        faculty_name = request.form.get('faculty_name', '').strip()
        email        = request.form.get('email', '').strip()
        department   = request.form.get('department', '').strip()

        if not faculty_name or not email:
            flash('Faculty name and email are required', 'warning')
            return redirect(url_for('admin.add_faculty'))

        conn = get_connection()
        cursor = conn.cursor()

        # Create user
        cursor.execute("SELECT USERS_SEQ.NEXTVAL FROM dual")
        user_id = cursor.fetchone()[0]
        
        login_id = email.split('@')[0]
        temp_pass = "faculty123"
        hashed_pass = generate_password_hash(temp_pass)

        cursor.execute("""
            INSERT INTO users (user_id, login_id, password_hash, role)
            VALUES (:1, :2, :3, 'faculty')
        """, (user_id, login_id, hashed_pass))

        # Create faculty
        cursor.execute("SELECT FACULTY_SEQ.NEXTVAL FROM dual")
        faculty_id = cursor.fetchone()[0]

        cursor.execute("""
            INSERT INTO faculty (faculty_id, user_id, faculty_name, email, department)
            VALUES (:1, :2, :3, :4, :5)
        """, (faculty_id, user_id, faculty_name, email, department))

        # Link back to user record
        cursor.execute("UPDATE users SET faculty_id = :1 WHERE user_id = :2", (faculty_id, user_id))

        conn.commit()
        flash(f'Faculty added. Login: {login_id} | Pass: {temp_pass}', 'success')

    except Exception as e:
        flash(f'Error adding faculty: {str(e)}', 'danger')
        if conn: conn.rollback()

    finally:
        if cursor: cursor.close()
        if conn: conn.close()

    return redirect(url_for('admin.dashboard'))


# ────────────────────────────────────────────────
# CREATE COURSE INSTANCE (offer course + assign faculty)
# ────────────────────────────────────────────────
@admin_bp.route('/create_course_instance', methods=['GET', 'POST'])
def create_course_instance():
    if session.get('role') != 'admin':
        flash('Admin access required', 'danger')
        return redirect(url_for('auth.login_page'))

    conn = get_connection()
    cursor = conn.cursor()

    try:
        if request.method == 'GET':
            cursor.execute("SELECT course_id, course_code, course_title FROM course_master ORDER BY course_code")
            courses = cursor.fetchall()

            cursor.execute("SELECT faculty_id, faculty_name FROM faculty ORDER BY faculty_name")
            faculty_list = cursor.fetchall()

            return render_template(
                'create_course_instance.html',
                courses=courses,
                faculty_list=faculty_list
            )

        # POST
        course_id         = int(request.form['course_id'])
        faculty_id        = int(request.form['faculty_id'])
        semester          = request.form['semester'].strip()
        academic_session  = request.form['academic_session'].strip()  # e.g. W25, M25

        cursor.execute("SELECT NVL(MAX(instance_id), 0) + 1 FROM course_instance")
        instance_id = cursor.fetchone()[0]

        cursor.execute("""
            INSERT INTO course_instance (
                instance_id, course_id, faculty_id,
                semester, academic_session
            ) VALUES (:1, :2, :3, :4, :5)
        """, (instance_id, course_id, faculty_id, semester, academic_session))

        conn.commit()
        flash('Course instance created successfully', 'success')

    except Exception as e:
        flash(f'Error creating course instance: {str(e)}', 'danger')
        conn.rollback()

    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('admin.dashboard'))


# ────────────────────────────────────────────────
# EDIT COURSE & DETAILS
# ────────────────────────────────────────────────
@admin_bp.route('/edit_course/<int:course_id>', methods=['GET', 'POST'])
def edit_course(course_id):
    if session.get('role') != 'admin':
        return redirect(url_for('auth.login_page'))

    conn = get_connection()
    cursor = conn.cursor()

    if request.method == 'GET':
        cursor.execute("SELECT * FROM course_master WHERE course_id = :1", (course_id,))
        course = cursor.fetchone()
        
        # Fetch related details
        cursor.execute("SELECT * FROM course_objectives WHERE course_id = :1 ORDER BY print_seq", (course_id,))
        objectives = cursor.fetchall()
        
        cursor.execute("SELECT * FROM course_outcomes WHERE course_id = :1 ORDER BY print_seq", (course_id,))
        outcomes = cursor.fetchall()
        
        cursor.execute("SELECT * FROM evaluation_details WHERE course_id = :1", (course_id,))
        evaluations = cursor.fetchall()

        return render_template('edit_course.html', course=course, objectives=objectives, outcomes=outcomes, evaluations=evaluations)

    # POST: Update Course
    try:
        title   = request.form['course_title']
        credits = int(request.form['credits'])
        ctype   = request.form['course_type'].upper()

        cursor.execute("""
            UPDATE course_master 
            SET course_title = :title, credits = :credits, course_type = :ctype
            WHERE course_id = :cid
        """, {"title": title, "credits": credits, "ctype": ctype, "cid": course_id})

        # Update Evaluation Weights
        cursor.execute("DELETE FROM evaluation_details WHERE course_id = :1", (course_id,))
        components = request.form.getlist('component_name[]')
        weights = request.form.getlist('weightage[]')
        for comp, weight in zip(components, weights):
            if comp.strip() and weight:
                # Use columns matching dump: EVAL_TYPE, WEIGHTAGE
                # Check dump again: EVAL_TYPE, WEIGHTAGE, COURSE_ID
                cursor.execute("""
                    INSERT INTO evaluation_details (course_id, eval_type, weightage) 
                    VALUES (:cid, :comp, :weight)
                """, {"cid": course_id, "comp": comp, "weight": weight})

        conn.commit()
        flash('Course updated successfully', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('admin.dashboard'))


# ────────────────────────────────────────────────
# MANAGE COURSE OUTCOMES (Dynamic Lists)
# ────────────────────────────────────────────────
@admin_bp.route('/update_outcomes/<int:course_id>', methods=['POST'])
def update_outcomes(course_id):
    if session.get('role') != 'admin': return "Access Denied", 403
    
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM course_outcomes WHERE course_id = :1", (course_id,))
        outcomes = request.form.getlist('outcome_desc[]')
        for i, desc in enumerate(outcomes, 1):
            if desc.strip():
                cursor.execute("SELECT NVL(MAX(outcome_id), 0) + 1 FROM course_outcomes")
                new_id = cursor.fetchone()[0]
                cursor.execute("""
                    INSERT INTO course_outcomes (outcome_id, course_id, outcome_desc, print_seq) 
                    VALUES (:1, :2, :3, :4)
                """, (new_id, course_id, desc, i))
        conn.commit()
        flash('Outcomes updated!', 'success')
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('admin.edit_course', course_id=course_id))


# ────────────────────────────────────────────────
# MANAGE COURSE OBJECTIVES
# ────────────────────────────────────────────────
@admin_bp.route('/update_objectives/<int:course_id>', methods=['POST'])
def update_objectives(course_id):
    if session.get('role') != 'admin': return "Access Denied", 403
    
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM course_objectives WHERE course_id = :1", (course_id,))
        objectives = request.form.getlist('objective_desc[]')
        for i, desc in enumerate(objectives, 1):
            if desc.strip():
                cursor.execute("SELECT NVL(MAX(obj_id), 0) + 1 FROM course_objectives")
                new_id = cursor.fetchone()[0]
                cursor.execute("""
                    INSERT INTO course_objectives (obj_id, course_id, description, print_seq) 
                    VALUES (:1, :2, :3, :4)
                """, (new_id, course_id, desc, i))
        conn.commit()
        flash('Objectives updated!', 'success')
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('admin.edit_course', course_id=course_id))


# ────────────────────────────────────────────────
# CO-PO MAPPING MATRIX
# ────────────────────────────────────────────────
@admin_bp.route('/copo_mapping/<int:course_id>', methods=['GET', 'POST'])
def copo_mapping(course_id):
    if session.get('role') != 'admin':
        return redirect(url_for('auth.login_page'))

    conn = get_connection()
    cursor = conn.cursor()

    if request.method == 'GET':
        # 1. Fetch Course & Outcomes
        cursor.execute("SELECT course_id, course_code, course_title FROM course_master WHERE course_id = :1", (course_id,))
        course = cursor.fetchone()
        
        cursor.execute("SELECT outcome_id, outcome_desc, print_seq FROM course_outcomes WHERE course_id = :1 ORDER BY print_seq", (course_id,))
        cos = cursor.fetchall()
        
        # 2. Fetch Program Outcomes
        cursor.execute("SELECT po_id, po_code, po_description FROM program_outcomes ORDER BY po_code")
        pos = cursor.fetchall()

        # 3. Fetch Existing Mapping
        cursor.execute("SELECT course_outcome_id, program_outcome_id, weightage FROM co_po_mapping WHERE course_outcome_id IN (SELECT outcome_id FROM course_outcomes WHERE course_id = :1)", (course_id,))
        mappings = cursor.fetchall()
        
        # Convert mapping to a dict for easy lookup: mapping_dict[(co_id, po_id)] = weight
        map_dict = {(m[0], m[1]): m[2] for m in mappings}

        return render_template('copo_mapping.html', course=course, cos=cos, pos=pos, map_dict=map_dict)

    # POST: Save Mapping Matrix
    try:
        # Form naming convention: weight_{co_id}_{po_id}
        for key in request.form:
            if key.startswith('weight_'):
                parts = key.split('_')
                co_id = int(parts[1])
                po_id = int(parts[2])
                val = request.form[key]
                weight = int(val) if val.isdigit() else 0

                # Upsert logic (Named parameters fix DPY-4009)
                cursor.execute("""
                    MERGE INTO co_po_mapping m
                    USING (SELECT :co_id as co_id, :po_id as po_id FROM dual) src
                    ON (m.course_outcome_id = src.co_id AND m.program_outcome_id = src.po_id)
                    WHEN MATCHED THEN 
                        UPDATE SET m.weightage = :weight
                    WHEN NOT MATCHED THEN 
                        INSERT (course_outcome_id, program_outcome_id, weightage)
                        VALUES (src.co_id, src.po_id, :weight)
                """, {"co_id": co_id, "po_id": po_id, "weight": weight})

        conn.commit()
        flash('CO-PO Mapping Matrix updated successfully!', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('admin.edit_course', course_id=course_id))


# ────────────────────────────────────────────────
# VIEW ALL STUDENTS
# ────────────────────────────────────────────────
@admin_bp.route('/view_students')
def view_students():
    if session.get('role') != 'admin':
        flash('Admin access required', 'danger')
        return redirect(url_for('auth.login_page'))

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT enrollment_no, name, email, program, status, registration_date, student_id
            FROM students
            ORDER BY registration_date DESC
        """)
        students = cursor.fetchall()
    except Exception as e:
        flash(f'Error fetching students: {str(e)}', 'danger')
        students = []
    finally:
        cursor.close()
        conn.close()

    return render_template('view_students.html', students=students)


# ────────────────────────────────────────────────
# PENDING STUDENTS + APPROVE
# ────────────────────────────────────────────────
@admin_bp.route('/pending_students')
def pending_students():
    if session.get('role') != 'admin':
        return redirect(url_for('auth.login_page'))

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT student_id, name, email, registration_date
            FROM students
            WHERE status = 'PENDING'
            ORDER BY registration_date DESC
        """)
        students = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

    return render_template('pending_students.html', students=students)


@admin_bp.route('/approve_student/<int:sid>')
def approve_student(sid):
    if session.get('role') != 'admin':
        return redirect(url_for('auth.login_page'))

    conn = get_connection()
    try:
        cursor = conn.cursor()

        # 1. Generate Credentials
        # Format: VNIT + Current Year + Student ID (e.g. VNIT2024101)
        import datetime
        year = datetime.datetime.now().year
        enrollment_no = f"VNIT{year}{sid}"
        
        temp_password = "VNIT@123" # In production, generate random and send email
        hashed_password = generate_password_hash(temp_password)

        # 2. Get Next User ID
        cursor.execute("SELECT USERS_SEQ.NEXTVAL FROM dual")
        user_id = cursor.fetchone()[0]

        # 3. Create User Login
        cursor.execute("""
            INSERT INTO users (user_id, login_id, password_hash, role, student_id)
            VALUES (:1, :2, :3, 'student', :4)
        """, (user_id, enrollment_no, hashed_password, sid))

        # 4. Update Student Record
        cursor.execute("""
            UPDATE students 
            SET status = 'APPROVED', 
                enrollment_no = :1,
                user_id = :2
            WHERE student_id = :3
        """, (enrollment_no, user_id, sid))

        # 5. Fetch details for email
        cursor.execute("SELECT name, email FROM students WHERE student_id = :1", (sid,))
        s_name, s_email = cursor.fetchone()

        conn.commit()
        
        # 6. Notify Student
        notify_student_approval(s_name, s_email, enrollment_no, temp_password)
        
        flash(f'Student approved! Enrollment: {enrollment_no} | Credentials sent to {s_email}', 'success')

    except Exception as e:
        flash(f'Error approving student: {str(e)}', 'danger')
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('admin.pending_students'))


# ────────────────────────────────────────────────
# EXPORT STUDENTS TO EXCEL
# ────────────────────────────────────────────────
@admin_bp.route('/export_students')
def export_students():
    if session.get('role') != 'admin':
        flash('Admin access required', 'danger')
        return redirect(url_for('auth.login_page'))

    conn = get_connection()
    try:
        query = """
            SELECT 
                student_id, name, email, mobile, program, aadhar, dob,
                address, enrollment_no, faculty_advisor, is_hosteller,
                registration_date, status
            FROM students
            ORDER BY registration_date DESC
        """

        df = pd.read_sql(query, conn)

        # Human-friendly column names
        df.columns = [
            'Student ID', 'Full Name', 'Email', 'Mobile', 'Program', 'Aadhaar',
            'Date of Birth', 'Address', 'Enrollment No', 'Faculty Advisor',
            'Hosteller (Y/N)', 'Registration Date', 'Status'
        ]

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Registered Students')

        output.seek(0)

        response = make_response(output.read())
        response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response.headers['Content-Disposition'] = 'attachment; filename=vnit_registered_students.xlsx'

        return response

    except Exception as e:
        return f"Error generating Excel file: {str(e)}", 500

    finally:
        conn.close()

@admin_bp.route('/student_registrations')
def student_registrations():
    if session.get('role') != 'admin':
        flash('Admin access required', 'danger')
        return redirect(url_for('auth.login_page'))

    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Query to get unique student registrations and current counts
        cursor.execute("""
            SELECT sr.reg_id, s.enrollment_no, s.name, sr.academic_session, sr.status, sr.registration_date,
                   (SELECT COUNT(*) FROM student_registration_courses src WHERE src.reg_id = sr.reg_id) AS course_count
            FROM student_registration sr
            JOIN students s ON sr.student_id = s.student_id
            ORDER BY sr.registration_date DESC
            """)
        registrations = cursor.fetchall()

        return render_template('admin_student_registrations.html', registrations=registrations)

    except Exception as e:
        flash(f"Error loading registrations: {str(e)}", "danger")
        return redirect(url_for('admin.dashboard'))

    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_bp.route('/approve_registration/<int:reg_id>')
def approve_registration(reg_id):
    if session.get('role') != 'admin':
        return redirect(url_for('auth.login_page'))

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE student_registration SET status = 'APPROVED' WHERE reg_id = :1", (reg_id,))
        
        # Notify
        cursor.execute("""
            SELECT s.name, s.email, sr.academic_session
            FROM student_registration sr
            JOIN students s ON sr.student_id = s.student_id
            WHERE sr.reg_id = :1
        """, (reg_id,))
        s_name, s_email, sess_name = cursor.fetchone()
        
        conn.commit()
        
        notify_registration_approval(s_name, s_email, sess_name)
        
        flash(f"Registration #{reg_id} for {s_name} APPROVED and student notified.", "success")
    except Exception as e:
        flash(f"Error approving registration: {str(e)}", "danger")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('admin.student_registrations'))


# ────────────────────────────────────────────────
# VIEW ALL RESULTS & GPA
# ────────────────────────────────────────────────
@admin_bp.route('/view_results')
def view_results():
    if session.get('role') != 'admin': return redirect(url_for('auth.login_page'))

    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Fetch Students with their cumulative performance
    # Formula: SGPA = sum(grade_point * credits) / sum(credits)
    cursor.execute("""
        WITH grade_points AS (
            SELECT student_id, course_id, academic_session, grade,
                   CASE grade 
                       WHEN 'AA' THEN 10 WHEN 'AB' THEN 9 WHEN 'BB' THEN 8 
                       WHEN 'BC' THEN 7 WHEN 'CC' THEN 6 WHEN 'CD' THEN 5 
                       WHEN 'DD' THEN 4 ELSE 0 END as points
            FROM results
        )
        SELECT s.enrollment_no, s.name, s.program,
               NVL(SUM(gp.points * cm.credits), 0) as total_grade_points,
               NVL(SUM(cm.credits), 0) as total_credits,
               ROUND(SUM(gp.points * cm.credits) / NULLIF(SUM(cm.credits), 0), 2) as cgpa
        FROM students s
        LEFT JOIN grade_points gp ON s.student_id = gp.student_id
        LEFT JOIN course_master cm ON gp.course_id = cm.course_id
        GROUP BY s.enrollment_no, s.name, s.program
        HAVING SUM(cm.credits) IS NOT NULL
        ORDER BY cgpa DESC
    """)
    student_performance = cursor.fetchall()

    # 2. Fetch Detailed Results for Table
    cursor.execute("""
        SELECT s.enrollment_no, s.name, cm.course_code, cm.course_title, 
               '' as numeric_grade, r.grade, r.academic_session
        FROM results r
        JOIN students s ON r.student_id = s.student_id
        JOIN course_master cm ON r.course_id = cm.course_id
        ORDER BY r.academic_session DESC, s.enrollment_no
    """)
    detailed_results = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('view_results.html', performance=student_performance, results=detailed_results)


# ────────────────────────────────────────────────
# SYSTEM SETTINGS (Session & Portal Control)
# ────────────────────────────────────────────────
@admin_bp.route('/settings', methods=['GET', 'POST'])
def settings():
    if session.get('role') != 'admin': return redirect(url_for('auth.login_page'))

    conn = get_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        key = request.form.get('config_key')
        val = request.form.get('config_value')
        
        try:
            cursor.execute("UPDATE system_config SET config_value = :1 WHERE config_key = :2", (val, key))
            conn.commit()
            flash(f"System configuration '{key}' updated to '{val}'", "success")
        except Exception as e:
            flash(f"Update failed: {str(e)}", "danger")

    # Fetch all configs
    cursor.execute("SELECT config_key, config_value FROM system_config ORDER BY config_key")
    configs = {row[0]: row[1] for row in cursor.fetchall()}
    
    cursor.close()
    conn.close()

    return render_template('admin_settings.html', configs=configs)


# ────────────────────────────────────────────────
# ANALYTICS & INSIGHTS
# ────────────────────────────────────────────────
@admin_bp.route('/analytics')
def analytics():
    if session.get('role') != 'admin': return redirect(url_for('auth.login_page'))

    conn = get_connection()
    cursor = conn.cursor()

    # 1. Registration Status Breakdown
    cursor.execute("""
        SELECT status, COUNT(*) as count 
        FROM student_registration 
        GROUP BY status
    """)
    reg_stats = cursor.fetchall()

    # 2. Grade Distribution
    cursor.execute("""
        SELECT grade, COUNT(*) as count 
        FROM results 
        GROUP BY grade
        ORDER BY CASE grade 
            WHEN 'AA' THEN 1 WHEN 'AB' THEN 2 WHEN 'BB' THEN 3 
            WHEN 'BC' THEN 4 WHEN 'CC' THEN 5 WHEN 'CD' THEN 6 
            WHEN 'DD' THEN 7 WHEN 'FF' THEN 8 ELSE 9 END
    """)
    grade_dist = cursor.fetchall()

    # 3. Departmental Registration Count
    cursor.execute("""
        SELECT program, COUNT(*) as count 
        FROM students 
        GROUP BY program
    """)
    dept_stats = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('admin_analytics.html', reg_stats=reg_stats, grades=grade_dist, depts=dept_stats)


# ────────────────────────────────────────────────
# FACULTY MANAGEMENT (CRUD)
# ────────────────────────────────────────────────
@admin_bp.route('/manage_faculty')
def manage_faculty():
    if session.get('role') != 'admin': return redirect(url_for('auth.login_page'))
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT f.faculty_id, f.faculty_name, f.email, f.department, u.login_id
        FROM faculty f
        LEFT JOIN users u ON f.faculty_id = u.faculty_id
        ORDER BY f.faculty_name
    """)
    faculties = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('manage_faculty.html', faculties=faculties)


@admin_bp.route('/edit_faculty/<int:fid>', methods=['GET', 'POST'])
def edit_faculty(fid):
    if session.get('role') != 'admin': return redirect(url_for('auth.login_page'))
    
    conn = get_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        dept = request.form.get('department')
        
        cursor.execute("""
            UPDATE faculty SET faculty_name = :1, email = :2, department = :3
            WHERE faculty_id = :4
        """, (name, email, dept, fid))
        conn.commit()
        flash("Faculty details updated successfully!", "success")
        return redirect(url_for('admin.manage_faculty'))

    cursor.execute("SELECT faculty_name, email, department FROM faculty WHERE faculty_id = :1", (fid,))
    faculty = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template('edit_faculty.html', faculty=faculty, fid=fid)


@admin_bp.route('/delete_faculty/<int:fid>')
def delete_faculty(fid):
    if session.get('role') != 'admin': return redirect(url_for('auth.login_page'))
    
    conn = get_connection()
    try:
        cursor = conn.cursor()
        # 1. Delete associated user login
        cursor.execute("DELETE FROM users WHERE faculty_id = :1", (fid,))
        # 2. Delete faculty record
        cursor.execute("DELETE FROM faculty WHERE faculty_id = :1", (fid,))
        conn.commit()
        flash("Faculty record and login credentials deleted.", "warning")
    except Exception as e:
        flash(f"Error: {str(e)}", "danger")
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('admin.manage_faculty'))
