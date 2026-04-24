from flask import Blueprint, render_template, session, redirect, request, flash, url_for, make_response
from config import get_connection
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

student_bp = Blueprint("student", __name__, url_prefix="/student")

def get_current_session():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT config_value 
            FROM system_config 
            WHERE config_key = 'current_academic_session'
        """)
        row = cursor.fetchone()
        return row[0] if row else "W25"  # fallback to what your DB has
    except:
        return "W25"
    finally:
        cursor.close()
        conn.close()

# ────────────────────────────────────────────────
# STUDENT DASHBOARD
# ────────────────────────────────────────────────
@student_bp.route("/dashboard")
def student_dashboard():
    if session.get("role") != "student":
        flash("Please login as student", "warning")
        return redirect(url_for("auth.login_page"))

    student_id = session.get("student_id")
    conn = get_connection()
    cursor = conn.cursor()

    available_sessions = []
    active_courses = []
    name = session.get("name", "Student")
    program = "Unknown"
    enrollment_no = "N/A"
    cgpa = "N.A."
    reg_status = "NONE"
    reg_session = "N/A"

    try:
        # 1. Fetch Student Details
        cursor.execute("SELECT program, enrollment_no, name FROM students WHERE student_id = :1", (student_id,))
        student_data = cursor.fetchone()
        if student_data:
            program = student_data[0]
            enrollment_no = student_data[1]
            name = student_data[2] or name

        # 2. Calculate CGPA
        try:
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
            if cgpa_row and cgpa_row[0]:
                cgpa = round(cgpa_row[0], 2)
        except:
            pass

        # 3. Last Registered Session info
        cursor.execute("""
            SELECT academic_session, status, reg_id FROM student_registration 
            WHERE student_id = :1 
            ORDER BY registration_date DESC FETCH FIRST 1 ROWS ONLY
        """, (student_id,))
        last_reg = cursor.fetchone()
        if last_reg:
            reg_session = last_reg[0]
            reg_status = last_reg[1]
            last_reg_id = last_reg[2]

            # 4. Fetch Active Courses (registered for latest session)
            if reg_status == 'APPROVED':
                cursor.execute("""
                    SELECT 
                        c.course_code, 
                        c.course_title, 
                        f.faculty_name, 
                        (SELECT ROUND((COUNT(CASE WHEN da.status = 'PRESENT' THEN 1 END) * 100.0) / NULLIF(COUNT(*), 0), 2) 
                         FROM daily_attendance da 
                         WHERE da.student_id = :sid AND da.course_instance_id = ci.instance_id) as percentage,
                        ci.instance_id
                    FROM student_registration_courses src
                    JOIN course_instance ci ON src.course_instance_id = ci.instance_id
                    JOIN course_master c ON ci.course_id = c.course_id
                    LEFT JOIN faculty f ON ci.faculty_id = f.faculty_id
                    WHERE src.reg_id = :rid
                """, sid=student_id, rid=last_reg_id)
                active_courses = cursor.fetchall()

        # 5. Fetch Available Sessions for Registration
        cursor.execute("SELECT DISTINCT academic_session FROM course_instance ORDER BY academic_session DESC")
        available_sessions = [row[0] for row in cursor.fetchall()]

    except Exception as e:
        print(f"Dashboard error: {str(e)}")
    finally:
        cursor.close()
        conn.close()

    return render_template("student_dashboard.html", 
                           name=name, 
                           program=program, 
                           cgpa=cgpa, 
                           enrollment_no=enrollment_no,
                           reg_status=reg_status,
                           reg_session=reg_session,
                           active_courses=active_courses,
                           available_sessions=available_sessions)

@student_bp.route("/attendance/<int:instance_id>")
def daily_attendance(instance_id):
    if session.get("role") != "student":
        return redirect(url_for("auth.login_page"))
    
    student_id = session.get("student_id")
    conn = get_connection()
    cursor = conn.cursor()

    # Fetch Course Info
    cursor.execute("""
        SELECT c.course_code, c.course_title, f.faculty_name
        FROM course_instance ci
        JOIN course_master c ON ci.course_id = c.course_id
        LEFT JOIN faculty f ON ci.faculty_id = f.faculty_id
        WHERE ci.instance_id = :1
    """, (instance_id,))
    course_info = cursor.fetchone()

    # Fetch Daily Records
    cursor.execute("""
        SELECT attendance_date, status
        FROM daily_attendance
        WHERE student_id = :sid AND course_instance_id = :inst
        ORDER BY attendance_date DESC
    """, sid=student_id, inst=instance_id)
    records = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("student_daily_attendance.html", 
                           course_info=course_info, 
                           records=records)

# ────────────────────────────────────────────────
# EXAMINATION RESULTS
# ────────────────────────────────────────────────
@student_bp.route("/examination", methods=["GET", "POST"])
def examination():
    print("[DEBUG] === ENTERED examination route ===")
    if session.get("role") != "student":
        return redirect(url_for("auth.login_page"))

    student_id = session.get("student_id")
    selected_semester = request.form.get("semester")
    selected_session = request.form.get("academic_session")

    conn = None
    cursor = None
    session_options = []
    cleared = []
    backlogs = []

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # 0. Performance Summary (All Time)
        cursor.execute("""
            SELECT NVL(SUM(cm.credits), 0)
            FROM results r
            JOIN course_master cm ON r.course_id = cm.course_id
            WHERE r.student_id = :sid AND r.grade NOT IN ('FF', 'W')
        """, sid=student_id)
        total_cleared_credits = cursor.fetchone()[0]

        # Get available registration history for sessions
        cursor.execute("""
            SELECT DISTINCT semester, academic_session 
            FROM student_registration 
            WHERE student_id = :sid
            ORDER BY semester DESC
        """, sid=student_id)
        session_options = cursor.fetchall()

        if selected_semester and selected_session:
            print(f"[DEBUG] Fetching results for Sem {selected_semester}, Session {selected_session}")
            # Fetch results
            cursor.execute("""
                SELECT cm.course_code, cm.course_title, cm.course_type, cm.credits, r.grade
                FROM results r
                JOIN course_master cm ON r.course_id = cm.course_id
                WHERE r.student_id = :sid 
                  AND r.academic_session = :sess
            """, sid=student_id, sess=selected_session)
            all_results = cursor.fetchall()
            
            # Logic: If grade is 'FF' or 'W', it's a backlog
            for r in all_results:
                if r[4] in ['FF', 'W']:
                    backlogs.append(r)
                else:
                    cleared.append(r)

    except Exception as e:
        print(f"[ERROR] examination failed: {str(e)}")
        flash(f"Error: {str(e)}", "danger")
        total_cleared_credits = 0
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

    return render_template(
        "examination.html",
        session_options=session_options,
        selected_semester=selected_semester,
        selected_session=selected_session,
        cleared=cleared,
        backlogs=backlogs,
        total_cleared_credits=total_cleared_credits
    )

# ────────────────────────────────────────────────
# STUDENT PROFILE SETTINGS
# ────────────────────────────────────────────────
@student_bp.route("/profile", methods=["GET", "POST"])
def profile():
    if session.get("role") != "student":
        return redirect(url_for("auth.login_page"))

    student_id = session.get("student_id")
    conn = get_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        email   = request.form.get("email")
        mobile  = request.form.get("mobile")
        address = request.form.get("address")
        pw      = request.form.get("password")

        try:
            # Update student info
            cursor.execute("""
                UPDATE students SET email = :1, mobile = :2, address = :3
                WHERE student_id = :4
            """, (email, mobile, address, student_id))

            # Update password if provided
            if pw and len(pw.strip()) >= 6:
                from werkzeug.security import generate_password_hash
                hashed = generate_password_hash(pw.strip())
                cursor.execute("UPDATE users SET password_hash = :1 WHERE student_id = :2", (hashed, student_id))

            conn.commit()
            flash("Profile updated successfully!", "success")
        except Exception as e:
            conn.rollback()
            flash(f"Update failed: {str(e)}", "danger")

    cursor.execute("SELECT * FROM students WHERE student_id = :1", (student_id,))
    student = cursor.fetchone()
    cursor.close()
    conn.close()

    return render_template("student_profile.html", student=student)

# ────────────────────────────────────────────────
# STUDENT REGISTRATION PAGE
# ────────────────────────────────────────────────
# ────────────────────────────────────────────────
# STUDENT REGISTRATION PAGE
# ────────────────────────────────────────────────
@student_bp.route("/register_courses", methods=["GET", "POST"])
def register_courses():
    if "user_id" not in session or session.get("role") != "student":
        flash("Please login as student", "danger")
        return redirect(url_for("auth.login_page"))

    student_id = session.get("student_id")
    
    # 1. Capture Session Parameters
    selected_session = request.args.get("session")
    if not selected_session:
        # Fallback to current session in config
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT config_value FROM system_config WHERE config_key = 'current_academic_session'")
        row = cursor.fetchone()
        selected_session = row[0] if row else "W25"
        cursor.close()
        conn.close()

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Check if registration is open
        cursor.execute("SELECT config_value FROM system_config WHERE config_key = 'registration_status'")
        status_row = cursor.fetchone()
        registration_open = (status_row[0] == 'OPEN') if status_row else False

        if not registration_open:
            flash("Course registration is currently CLOSED.", "warning")
            return redirect(url_for("student.student_dashboard"))

        # Status Check
        cursor.execute("""
            SELECT status FROM student_registration 
            WHERE student_id = :1 AND academic_session = :2
        """, (student_id, selected_session))
        reg_row = cursor.fetchone()
        reg_status = reg_row[0] if reg_row else "NOT_STARTED"

        # 1. Fetch Backlogs
        cursor.execute("""
            SELECT DISTINCT cm.course_code, cm.course_title, cm.credits, 'BACKLOG'
            FROM results r
            JOIN course_master cm ON r.course_id = cm.course_id
            WHERE r.student_id = :sid AND r.grade IN ('FF', 'W')
              AND NOT EXISTS (
                  SELECT 1 FROM results r2 
                  WHERE r2.student_id = r.student_id AND r2.course_id = r.course_id AND r2.grade NOT IN ('FF', 'W')
              )
        """, sid=student_id)
        backlogs = cursor.fetchall() or []

        # 2. Fetch DC Courses
        cursor.execute("""
            SELECT 
                cm.course_code, cm.course_title, cm.credits,
                LISTAGG(NVL(f.faculty_name, 'N/A'), ', ') WITHIN GROUP (ORDER BY f.faculty_name) as faculties,
                LISTAGG(NVL(ci.section, 'N/A'), ', ') WITHIN GROUP (ORDER BY ci.section) as sections,
                LISTAGG(NVL(ci.slot, 'N/A'), ', ') WITHIN GROUP (ORDER BY ci.slot) as slots
            FROM course_instance ci
            JOIN course_master cm ON ci.course_id = cm.course_id
            LEFT JOIN faculty f ON ci.faculty_id = f.faculty_id
            WHERE cm.course_type = 'DC' 
              AND UPPER(cm.program) = (SELECT UPPER(program) FROM students WHERE student_id = :sid)
              AND ci.academic_session = :sess
            GROUP BY cm.course_code, cm.course_title, cm.credits
        """, sid=student_id, sess=selected_session)
        dc_courses = cursor.fetchall() or []

        # 3. Fetch DE Courses
        cursor.execute("""
            SELECT 
                cm.course_code, cm.course_title, cm.credits,
                LISTAGG(NVL(f.faculty_name, 'N/A'), ', ') WITHIN GROUP (ORDER BY f.faculty_name) as faculties,
                LISTAGG(NVL(ci.section, 'N/A'), ', ') WITHIN GROUP (ORDER BY ci.section) as sections,
                LISTAGG(NVL(ci.slot, 'N/A'), ', ') WITHIN GROUP (ORDER BY ci.slot) as slots
            FROM course_instance ci
            JOIN course_master cm ON ci.course_id = cm.course_id
            LEFT JOIN faculty f ON ci.faculty_id = f.faculty_id
            WHERE cm.course_type = 'DE' 
              AND UPPER(cm.program) = (SELECT UPPER(program) FROM students WHERE student_id = :sid)
              AND ci.academic_session = :sess
            GROUP BY cm.course_code, cm.course_title, cm.credits
        """, sid=student_id, sess=selected_session)
        de_courses = cursor.fetchall() or []

        # saved_codes
        cursor.execute("""
            SELECT cm.course_code
            FROM student_registration_courses src
            JOIN course_instance ci ON src.course_instance_id = ci.instance_id
            JOIN course_master cm ON ci.course_id = cm.course_id
            JOIN student_registration sr ON src.reg_id = sr.reg_id
            WHERE sr.student_id = :1 AND sr.academic_session = :2
        """, (student_id, selected_session))
        saved_codes = {row[0] for row in cursor.fetchall()}

        if request.method == "POST":
            action = request.form.get("action", "submit")
            
            if reg_status == 'APPROVED' and action != 'generate_pdf':
                flash("Registration is already approved.", "warning")
                return redirect(url_for('student.register_courses', session=selected_session))

            if action == 'generate_pdf':
                return redirect(url_for('student.generate_registration_pdf', session_name=selected_session))

            dc_selected = request.form.getlist("dc_selected") or []
            de_selected = request.form.getlist("de_selected") or []
            
            if len(de_selected) != 2:
                flash("Select exactly 2 DE courses.", "danger")
                return redirect(url_for('student.register_courses', session=selected_session))

            # MERGE Header
            cursor.execute("""
                MERGE INTO student_registration sr
                USING (SELECT :sid as sid, :sess as sess FROM dual) src
                ON (sr.student_id = src.sid AND sr.academic_session = src.sess)
                WHEN MATCHED THEN
                    UPDATE SET sr.status = 'SUBMITTED', sr.registration_date = SYSDATE
                WHEN NOT MATCHED THEN
                    INSERT (student_id, academic_session, semester, status, registration_date)
                    VALUES (:sid, :sess, (SELECT semester FROM students WHERE student_id = :sid), 'SUBMITTED', SYSDATE)
            """, sid=student_id, sess=selected_session)

            # Get reg_id
            cursor.execute("SELECT reg_id FROM student_registration WHERE student_id = :1 AND academic_session = :2", 
                          (student_id, selected_session))
            reg_id = cursor.fetchone()[0]

            # Clear and Insert courses
            cursor.execute("DELETE FROM student_registration_courses WHERE reg_id = :1", (reg_id,))
            all_selected = dc_selected + de_selected
            for item in all_selected:
                cursor.execute("""
                    SELECT ci.instance_id, cm.course_type 
                    FROM course_instance ci
                    JOIN course_master cm ON ci.course_id = cm.course_id
                    WHERE cm.course_code = :1
                      AND ci.academic_session = :2 FETCH FIRST 1 ROWS ONLY
                """, (item, selected_session))
                inst = cursor.fetchone()
                if inst:
                    inst_id, c_type = inst
                    cursor.execute("""
                        INSERT INTO student_registration_courses (reg_id, course_instance_id, course_type)
                        VALUES (:1, :2, :3)
                    """, (reg_id, inst_id, c_type))
            
            conn.commit()
            flash("Registration submitted successfully!", "success")
            return redirect(url_for('student.register_courses', session=selected_session))

        return render_template("register_courses.html", 
                               dc_courses=dc_courses, 
                               de_courses=de_courses, 
                               backlogs=backlogs,
                               reg_status=reg_status,
                               current_session=selected_session,
                               saved_codes=saved_codes)

    except Exception as e:
        flash(f"Error: {str(e)}", "danger")
        return redirect(url_for('student.student_dashboard'))
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

# ────────────────────────────────────────────────
# VIEW / EDIT REGISTERED COURSES
# ────────────────────────────────────────────────
@student_bp.route("/view_registered_courses", methods=["GET", "POST"])
def view_registered_courses():
    print("[DEBUG] === ENTERED view_registered_courses route ===")
    
    if "student_id" not in session:
        print("[DEBUG] No student_id → redirecting to login")
        flash("Please login again", "danger")
        return redirect(url_for("auth.login_page"))

    student_id = session.get("student_id")
    current_session = get_current_session()
    print(f"[DEBUG] Student ID: {student_id} | Current session: {current_session}")

    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        print("[DEBUG] Database connection established")

        # 1. Get already saved/registered course codes
        print("[DEBUG] Fetching already saved course codes...")
        cursor.execute("""
            SELECT c.course_code
            FROM student_registration sr
            JOIN student_registration_courses src ON sr.reg_id = src.reg_id
            JOIN course_instance ci ON src.course_instance_id = ci.instance_id
            JOIN course_master c ON ci.course_id = c.course_id
            WHERE sr.student_id = :sid 
              AND sr.academic_session = :sess
        """, sid=student_id, sess=current_session)
        saved_codes = {row[0] for row in cursor.fetchall()}
        print(f"[DEBUG] Found {len(saved_codes)} already registered courses: {saved_codes}")

        # 2. Fetch DC courses for current session
        print("[DEBUG] Fetching DC courses...")
        cursor.execute("""
            SELECT DISTINCT 
                   c.course_code, 
                   c.course_title, 
                   c.credits,
                   LISTAGG(NVL(f.faculty_name, 'Not Assigned'), ', ') WITHIN GROUP (ORDER BY f.faculty_name) AS coordinator,
                   LISTAGG(NVL(ci.section, 'N/A'), ', ') WITHIN GROUP (ORDER BY ci.section) AS section,
                   LISTAGG(NVL(ci.batch, 'N/A'), ', ') WITHIN GROUP (ORDER BY ci.batch) AS batch,
                   LISTAGG(NVL(ci.slot, 'N/A'), ', ') WITHIN GROUP (ORDER BY ci.slot) AS slot
            FROM course_instance ci
            JOIN course_master c ON ci.course_id = c.course_id
            LEFT JOIN faculty f ON ci.faculty_id = f.faculty_id
            WHERE ci.academic_session = :sess
              AND c.course_type = 'DC'
            GROUP BY c.course_code, c.course_title, c.credits
            ORDER BY c.course_code
        """, sess=current_session)
        dc_courses = cursor.fetchall() or []
        print(f"[DEBUG] DC courses loaded: {len(dc_courses)} rows → { [row[0] for row in dc_courses] }")

        # 3. Fetch DE courses for current session (fixed parenthesis!)
        print("[DEBUG] Fetching DE courses...")
        cursor.execute("""
            SELECT DISTINCT 
                   c.course_code, 
                   c.course_title, 
                   c.credits,
                   LISTAGG(NVL(f.faculty_name, 'Not Assigned'), ', ') WITHIN GROUP (ORDER BY f.faculty_name) AS coordinator,
                   LISTAGG(NVL(ci.section, 'N/A'), ', ') WITHIN GROUP (ORDER BY ci.section) AS section,
                   LISTAGG(NVL(ci.batch, 'N/A'), ', ') WITHIN GROUP (ORDER BY ci.batch) AS batch,
                   LISTAGG(NVL(ci.slot, 'N/A'), ', ') WITHIN GROUP (ORDER BY ci.slot) AS slot
            FROM course_instance ci
            JOIN course_master c ON ci.course_id = c.course_id
            LEFT JOIN faculty f ON ci.faculty_id = f.faculty_id
            WHERE ci.academic_session = :sess
              AND c.course_type = 'DE'
            GROUP BY c.course_code, c.course_title, c.credits
            ORDER BY c.course_code
        """, sess=current_session)
        de_courses = cursor.fetchall() or []
        print(f"[DEBUG] DE courses loaded: {len(de_courses)} rows → { [row[0] for row in de_courses] }")

        # 4. Fetch backlogs (simple version – from results)
        print("[DEBUG] Fetching backlogs...")
        cursor.execute("""
            SELECT c.course_code, 
                   c.course_title, 
                   c.credits, 
                   'Backlog (Mandatory DC)' AS coordinator,
                   'Prev' AS section, 
                   'Prev' AS batch, 
                   'Prev' AS slot, 
                   NULL AS instance_id
            FROM results r
            JOIN course_master c ON r.course_id = c.course_id
            WHERE r.student_id = :sid 
              AND r.grade < 40   -- adjust passing threshold if needed
            ORDER BY c.course_code
        """, sid=student_id)
        backlogs = cursor.fetchall() or []
        print(f"[DEBUG] Backlogs found: {len(backlogs)}")

        # ── POST handling (update registration + PDF) ──
        if request.method == "POST":
            action = request.form.get("action", "submit")

            print("[DEBUG] POST request - updating registration")
            selected_dc = [int(x) for x in request.form.getlist("dc_selected") if x.isdigit()]
            selected_de = [int(x) for x in request.form.getlist("de_selected") if x.isdigit()]

            required_dc = len(dc_courses) + len(backlogs)
            print(f"[DEBUG] Required DC: {required_dc} | Selected DC: {len(selected_dc)} | Selected DE: {len(selected_de)}")

            if len(selected_dc) != required_dc:
                flash(f"You must select all {required_dc} DC courses (including backlogs)", "danger")
                return redirect(url_for("student.register_courses"))

            if len(selected_de) != 2:
                flash("You must select exactly 2 DE courses", "danger")
                return redirect(url_for("student.register_courses"))

            all_selected_codes = selected_dc + selected_de
            print(f"[DEBUG] All selected codes: {all_selected_codes}")

            # Delete old registrations
            cursor.execute("""
                DELETE FROM student_registration_courses
                WHERE reg_id IN (
                    SELECT reg_id FROM student_registration 
                    WHERE student_id = :sid AND academic_session = :sess
                )
            """, sid=student_id, sess=current_session)
            print("[DEBUG] Old registrations deleted")

            # Insert new registrations
            inserted = 0
            for code in all_selected_codes:
                cursor.execute("""
                    SELECT ci.instance_id 
                    FROM course_instance ci
                    JOIN course_master c ON ci.course_id = c.course_id
                    WHERE c.course_code = :code 
                      AND ci.academic_session = :sess
                    FETCH FIRST 1 ROW ONLY
                """, code=code, sess=current_session)
                instance = cursor.fetchone()
                if instance:
                    instance_id = instance[0]
                    # Ensure master entry exists for sync logic
                    cursor.execute("SELECT reg_id FROM student_registration WHERE student_id = :1 AND academic_session = :2", (student_id, current_session))
                    r_row = cursor.fetchone()
                    if not r_row:
                        cursor.execute("INSERT INTO student_registration (student_id, academic_session, status) VALUES (:1, :2, 'SUBMITTED')", (student_id, current_session))
                        cursor.execute("SELECT reg_id FROM student_registration WHERE student_id = :1 AND academic_session = :2", (student_id, current_session))
                        r_row = cursor.fetchone()
                    
                    reg_id = r_row[0]
                    cursor.execute("""
                        INSERT INTO student_registration_courses 
                        (reg_id, course_instance_id, course_type)
                        VALUES (:1, :2, 'DC') -- Dummy DC/DE check
                    """, (reg_id, instance_id))
                    inserted += 1
                    print(f"[DEBUG] Inserted: {code} (instance {instance_id})")
                else:
                    print(f"[WARNING] No instance found for {code} in {current_session}")
            
            conn.commit()
            flash("Registration updated successfully", "success")
            print("[DEBUG] COMMIT successful")

            if request.form.get("action") == "generate_pdf":
                return redirect(url_for("student.generate_registration_pdf", session_name=current_session))

            return redirect(url_for("student.register_courses"))

        print("[DEBUG] Rendering view_registered.html template")
        return render_template(
            "view_registered.html",
            dc_courses=dc_courses,
            de_courses=de_courses,
            backlogs=backlogs,
            saved_codes=saved_codes,
            current_session=current_session
        )

    except Exception as e:
        print(f"[CRITICAL ERROR] view_registered_courses failed: {str(e)}")
        import traceback
        print(traceback.format_exc())
        flash(f"Error: {str(e)}", "danger")
        return redirect(url_for("student.student_dashboard"))

    finally:
        print("[DEBUG] Cleaning up DB resources")
        if cursor:
            cursor.close()
        if conn:
            conn.close()
# ────────────────────────────────────────────────
# COURSE DETAILS
# ────────────────────────────────────────────────
@student_bp.route("/course_details/<course_code>")
def course_details(course_code):
    if session.get("role") != "student":
        return redirect(url_for("student.student_dashboard"))

    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT course_code, course_title, course_type, program, l, t, p, credits
            FROM course_master WHERE course_code = :code
        """, code=course_code)
        basic = cursor.fetchone()

        if not basic:
            flash("Course not found", "danger")
            return redirect(url_for("student.register_courses"))

        cursor.execute("""
            SELECT cm.course_code, cm.course_title
            FROM course_prerequisites cp
            JOIN course_master cm ON cp.prerequisite_course_id = cm.course_id
            WHERE cp.course_id = (SELECT course_id FROM course_master WHERE course_code = :code)
        """, code=course_code)
        prereqs = cursor.fetchall() or []

        cursor.execute("""
            SELECT description FROM course_objectives
            WHERE course_id = (SELECT course_id FROM course_master WHERE course_code = :code)
            ORDER BY print_seq
        """, code=course_code)
        objectives = [row[0] for row in cursor.fetchall()]

        cursor.execute("""
            SELECT outcome_desc FROM course_outcomes
            WHERE course_id = (SELECT course_id FROM course_master WHERE course_code = :code)
            ORDER BY print_seq
        """, code=course_code)
        outcomes = [row[0] for row in cursor.fetchall()]

        cursor.execute("""
            SELECT topic, duration_weeks FROM course_description
            WHERE course_id = (SELECT course_id FROM course_master WHERE course_code = :code)
            ORDER BY desc_id
        """, code=course_code)
        description = cursor.fetchall() or []

        cursor.execute("SELECT title, type FROM text_books WHERE course_id = (SELECT course_id FROM course_master WHERE course_code = :code)", code=course_code)
        text_books = cursor.fetchall() or []

        cursor.execute("SELECT title, type FROM reference_books WHERE course_id = (SELECT course_id FROM course_master WHERE course_code = :code)", code=course_code)
        ref_books = cursor.fetchall() or []

        # Evaluations
        cursor.execute("""
            SELECT eval_type, weightage, description
            FROM evaluation_details
            WHERE course_id = (SELECT course_id FROM course_master WHERE course_code = :code)
        """, code=course_code)
        evaluation = cursor.fetchall() or []

        # CO-PO Mapping
        cursor.execute("""
            SELECT po.po_code, m.weightage, co.outcome_desc
            FROM co_po_mapping m
            JOIN program_outcomes po ON m.program_outcome_id = po.po_id
            JOIN course_outcomes co ON m.course_outcome_id = co.outcome_id
            WHERE co.course_id = (SELECT course_id FROM course_master WHERE course_code = :code)
            ORDER BY co.print_seq, po.po_code
        """, code=course_code)
        po_mapping = cursor.fetchall() or []

        return render_template(
            "course_details.html",
            basic=basic,
            prereqs=prereqs,
            objectives=objectives,
            outcomes=outcomes,
            description=description,
            text_books=text_books,
            ref_books=ref_books,
            course_code=course_code,
            evaluation=evaluation,
            po_mapping=po_mapping
        )

    except Exception as e:
        print(f"ERROR in course_details: {str(e)}")
        flash(f"Error loading course details: {str(e)}", "danger")
        return redirect(url_for("student.register_courses"))

    finally:
        if cursor: cursor.close()
        if conn: conn.close()

# ────────────────────────────────────────────────
# PDF GENERATION – always reads latest from DB
# ────────────────────────────────────────────────
@student_bp.route("/generate_registration_pdf/<session_name>")
def generate_registration_pdf(session_name):
    if "student_id" not in session:
        return redirect(url_for("auth.login_page"))
    student_id = session.get("student_id")
    current_session = session_name
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Get student info
        cursor.execute("""
            SELECT name, enrollment_no, faculty_advisor, mobile, address, email, is_hosteller, registration_date
            FROM students WHERE student_id = :sid
        """, sid=student_id)
        student = cursor.fetchone()
        if not student:
            raise ValueError("Student not found")

        name, enrl_no, advisor, mobile, address, email, hosteller, reg_date = student
        hosteller_str = "Yes" if hosteller == 'Y' else "No"
        reg_date_str = reg_date.strftime("%d/%m/%Y") if reg_date else datetime.now().strftime("%d/%m/%Y")

        # Get registered courses
        cursor.execute("""
            SELECT 
                c.course_code,
                c.course_title,
                NVL(ci.section, 'N/A'),
                NVL(ci.batch, 'N/A'),
                NVL(ci.slot, 'N/A'),
                c.course_type,
                c.credits,
                LISTAGG(DISTINCT NVL(f.faculty_name, 'Not Assigned'), ', ') WITHIN GROUP (ORDER BY f.faculty_name),
                NVL(c.L, 0),
                NVL(c.T, 0),
                NVL(c.P, 0)
            FROM student_registration_courses reg
            JOIN student_registration sr ON reg.reg_id = sr.reg_id
            JOIN course_instance ci ON reg.course_instance_id = ci.instance_id
            JOIN course_master c ON ci.course_id = c.course_id
            LEFT JOIN faculty f ON ci.faculty_id = f.faculty_id
            WHERE sr.student_id = :sid AND sr.academic_session = :sess
            GROUP BY c.course_code, c.course_title, ci.section, ci.batch, ci.slot, 
                     c.course_type, c.credits, c.L, c.T, c.P
            ORDER BY c.course_type, c.course_code
        """, sid=student_id, sess=current_session)
        courses = cursor.fetchall() or []

        if not courses:
            flash("No registered courses found for PDF", "warning")
            return redirect(url_for("student.register_courses"))

        # Calculate real values
        dc_count = sum(1 for r in courses if r[5] == 'DC')
        de_count = sum(1 for r in courses if r[5] == 'DE')
        total_credits = sum(r[6] for r in courses)
        total_courses = len(courses)
        theory_count = sum(1 for r in courses if r[8] > 0 or r[9] > 0)
        practical_count = sum(1 for r in courses if r[10] > 0)

        # Build PDF (same layout as your reference)
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=60, bottomMargin=40)
        styles = getSampleStyleSheet()
        elements = []

        # Logo & Header
        logo_path = r"C:\Users\DELL\OneDrive\Desktop\course_portal\static\vnit_logo.jpeg"
        try:
            logo = Image(logo_path, width=80, height=80)
            elements.append(logo)
        except:
            elements.append(Paragraph("VNIT", styles['Heading2']))

        elements.append(Paragraph("Visvesvaraya National Institute of Technology", styles['Heading2']))
        elements.append(Paragraph("Nagpur", styles['Heading4']))
        elements.append(Spacer(1, 6))
        elements.append(Paragraph("DEPARTMENT OF COMPUTER SCIENCE & ENGINEERING", styles['Heading3']))
        elements.append(Spacer(1, 12))
        elements.append(Paragraph("FINAL SUBMITTED", styles['Heading4']))
        elements.append(Spacer(1, 12))

        # Student details
        student_lines = [
            f"Name: {name or 'N/A'}",
            f"ID No./Enrl. No.: {enrl_no or 'N/A'}",
            f"Name of Fac. Adv.: {advisor or 'Not Assigned'}",
            f"Contact No.: {mobile or 'Not Provided'}",
            f"Current Address: {address or 'Not Provided'}",
            f"Email: {email or 'N/A'}",
            f"Hosteller: {hosteller_str}",
            f"Dt. of Registration: {reg_date_str}"
        ]
        for line in student_lines:
            elements.append(Paragraph(line, styles['Normal']))

        elements.append(Spacer(1, 18))

        # Course table
        table_data = [["Sr. No.", "Course code", "Course Title", "Section", "Batch", "Slot", "Course", "Credits", "Co-ordinator"]]
        for i, row in enumerate(courses, 1):
            table_data.append([str(i), row[0], row[1], row[2], row[3], row[4], row[5], str(row[6]), row[7]])

        table = Table(table_data, colWidths=[30, 60, 140, 45, 45, 45, 45, 45, 110])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.orange),
            ('TEXTCOLOR', (0,0), (-1,0), colors.black),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        elements.append(table)

        elements.append(Spacer(1, 18))

        # Real dynamic totals (this is what was missing)
        elements.append(Paragraph(f"DC : {dc_count}   DE : {de_count}   Theory : {theory_count}   Practical : {practical_count}", styles['Normal']))
        elements.append(Paragraph(f"Total Credit registered : {total_credits}", styles['Normal']))
        elements.append(Paragraph(f"Total No. of courses registered in the session : {total_courses}", styles['Normal']))

        elements.append(Spacer(1, 36))

        # Signatures
        sig_table = Table([
            ["Signature of Student", "Signature of Faculty Advisor"],
            [name or "____________________", advisor or "____________________"]
        ], colWidths=[250, 250])
        sig_table.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER')]))
        elements.append(sig_table)

        elements.append(Spacer(1, 24))
        elements.append(Paragraph(f"Printed By {name or 'Student'}   Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", styles['Italic']))

        doc.build(elements)
        buffer.seek(0)

        response = make_response(buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename="registration_{enrl_no or student_id}_{datetime.now().strftime("%Y%m%d")}.pdf"'
        return response

    except Exception as e:
        print(f"PDF ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        flash(f"Failed to generate PDF: {str(e)}", "danger")
        return redirect(url_for("student.register_courses"))

    finally:
        if cursor: cursor.close()
        if conn: conn.close()