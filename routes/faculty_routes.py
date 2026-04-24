from flask import Blueprint, render_template, session, redirect, request, flash, url_for
from config import get_connection
import calendar
from datetime import datetime

faculty_bp = Blueprint("faculty", __name__, url_prefix="/faculty")

@faculty_bp.route("/dashboard")
def faculty_dashboard():
    if session.get("role") != "faculty":
        flash("Faculty access only", "danger")
        return redirect(url_for("auth.login_page"))

    faculty_id = session.get("faculty_id")
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Fetch Faculty Name
    cursor.execute("SELECT faculty_name FROM faculty WHERE faculty_id = :fid", fid=faculty_id)
    faculty_row = cursor.fetchone()
    faculty_name = faculty_row[0] if faculty_row else "Faculty"

    # 2. Fetch Assigned Courses with Stats
    # Includes: instance_id, code, title, semester, session, section, batch, slot, student_count, avg_attendance
    cursor.execute("""
        SELECT 
            ci.instance_id, 
            c.course_code, 
            c.course_title, 
            ci.semester, 
            ci.academic_session, 
            ci.section, 
            ci.batch, 
            ci.slot,
            (SELECT COUNT(*) FROM student_registration_courses src WHERE src.course_instance_id = ci.instance_id) as enrolled_count,
            (SELECT ROUND((COUNT(CASE WHEN da.status = 'PRESENT' THEN 1 END) * 100.0) / NULLIF(COUNT(*), 0), 2) 
             FROM daily_attendance da 
             WHERE da.course_instance_id = ci.instance_id) as avg_att,
            c.course_id
        FROM course_instance ci
        JOIN course_master c ON ci.course_id = c.course_id
        WHERE ci.faculty_id = :fid
    """, fid=faculty_id)
    courses = cursor.fetchall()

    # 3. Fetch Coordinated Students (Advisory)
    # Note: SEMESTER is NOT in STUDENTS table, we fetch it from registrations
    cursor.execute("""
        SELECT student_id, name, enrollment_no, program, 
               (SELECT semester FROM student_registration 
                WHERE student_id = students.student_id 
                ORDER BY registration_date DESC FETCH FIRST 1 ROWS ONLY) as semester, 
               email
        FROM students
        WHERE advisor_id = :fid
    """, fid=faculty_id)
    coordinated_students = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("faculty_dashboard.html", 
                           faculty_name=faculty_name, 
                           courses=courses, 
                           coordinated_students=coordinated_students)

@faculty_bp.route("/attendance/<int:course_id>", methods=["GET", "POST"])
def attendance(course_id):
    if session.get("role") != "faculty":
        return redirect(url_for("auth.login_page"))

    conn = get_connection()
    cursor = conn.cursor()

    # Get selected month and year
    year = int(request.args.get("year") or datetime.now().year)
    month = int(request.args.get("month") or datetime.now().month)
    
    # Calculate days in month
    num_days = calendar.monthrange(year, month)[1]
    days = list(range(1, num_days + 1))
    
    # Format month name for display
    month_name = calendar.month_name[month]

    if request.method == "POST":
        # Process grid submission
        # We expect fields like "att_{student_id}_{day}" for checked items
        # AND "student_ids[]" for all students involved
        student_ids = request.form.getlist("student_id[]")
        
        try:
            for sid in student_ids:
                for d in days:
                    # Check if this day/student was checked
                    field_name = f"att_{sid}_{d}"
                    status = 'PRESENT' if request.form.get(field_name) == 'on' else 'ABSENT'
                    
                    # Merge into daily_attendance
                    # Note: We only update if the date is not in the future (optional but good practice)
                    att_date_str = f"{year}-{month:02d}-{d:02d}"
                    
                    cursor.execute("""
                        MERGE INTO daily_attendance da
                        USING (SELECT :sid AS student_id, :cid AS course_instance_id, TO_DATE(:dt, 'YYYY-MM-DD') AS att_date FROM dual) src
                        ON (da.student_id = src.student_id AND da.course_instance_id = src.course_instance_id AND da.attendance_date = src.att_date)
                        WHEN MATCHED THEN
                            UPDATE SET da.status = :status
                        WHEN NOT MATCHED THEN
                            INSERT (student_id, course_instance_id, attendance_date, status)
                            VALUES (:sid, :cid, TO_DATE(:dt, 'YYYY-MM-DD'), :status)
                    """, sid=sid, cid=course_id, dt=att_date_str, status=status)
            
            conn.commit()
            flash(f"Attendance for {month_name} {year} updated successfully!", "success")
        except Exception as e:
            conn.rollback()
            flash(f"Error updating grid: {str(e)}", "danger")

    # 1. Fetch Students
    cursor.execute("""
        SELECT s.student_id, s.name, s.enrollment_no
        FROM student_registration_courses reg
        JOIN student_registration sr ON reg.reg_id = sr.reg_id
        JOIN students s ON sr.student_id = s.student_id
        WHERE reg.course_instance_id = :cid
        ORDER BY s.name
    """, cid=course_id)
    students_list = cursor.fetchall()

    # 2. Fetch existing attendance for the month
    cursor.execute("""
        SELECT student_id, EXTRACT(DAY FROM attendance_date), status
        FROM daily_attendance
        WHERE course_instance_id = :cid
          AND EXTRACT(MONTH FROM attendance_date) = :m
          AND EXTRACT(YEAR FROM attendance_date) = :y
    """, cid=course_id, m=month, y=year)
    
    att_data = {} # {student_id: {day: status}}
    for sid, day, status in cursor.fetchall():
        if sid not in att_data: att_data[sid] = {}
        att_data[sid][day] = status

    # 3. Fetch Course Info
    cursor.execute("""
        SELECT c.course_code, c.course_title 
        FROM course_instance ci 
        JOIN course_master c ON ci.course_id = c.course_id 
        WHERE ci.instance_id = :cid
    """, cid=course_id)
    course_info = cursor.fetchone() or ("Unknown", "Unknown")

    cursor.close()
    conn.close()

    return render_template("attendance_grid.html", 
                           students=students_list, 
                           days=days,
                           att_data=att_data,
                           course_id=course_id, 
                           course_info=course_info, 
                           year=year, 
                           month=month,
                           month_name=month_name,
                           calendar_mod=calendar,
                           now_day=datetime.now().day if datetime.now().month == month and datetime.now().year == year else 0)

@faculty_bp.route("/student-details/<int:student_id>")
def student_details(student_id):
    if session.get("role") != "faculty":
        return redirect(url_for("auth.login_page"))
    
    faculty_id = session.get("faculty_id")
    conn = get_connection()
    cursor = conn.cursor()

    # Verify this faculty is the advisor for this student
    cursor.execute("SELECT 1 FROM students WHERE advisor_id = :fid AND student_id = :sid", fid=faculty_id, sid=student_id)
    if not cursor.fetchone():
        flash("You are not authorized to view this student's details.", "danger")
        return redirect(url_for("faculty.faculty_dashboard"))

    # Fetch student info (SEMESTER is in STUDENT_REGISTRATION)
    cursor.execute("""
        SELECT name, enrollment_no, email, mobile, 
               (SELECT semester FROM student_registration sr WHERE sr.student_id = :sid ORDER BY reg_id DESC FETCH FIRST 1 ROWS ONLY) as semester, 
               program 
        FROM students WHERE student_id = :sid
    """, sid=student_id)
    student = cursor.fetchone()

    # Fetch registered courses for current session
    cursor.execute("""
        SELECT 
            c.course_code, 
            c.course_title, 
            ci.academic_session, 
            (SELECT ROUND((COUNT(CASE WHEN da.status = 'PRESENT' THEN 1 END) * 100.0) / NULLIF(COUNT(*), 0), 2) 
             FROM daily_attendance da 
             WHERE da.student_id = :sid AND da.course_instance_id = ci.instance_id) as percentage
        FROM student_registration_courses src
        JOIN student_registration sr ON src.reg_id = sr.reg_id
        JOIN course_instance ci ON src.course_instance_id = ci.instance_id
        JOIN course_master c ON ci.course_id = c.course_id
        WHERE sr.student_id = :sid
    """, sid=student_id)
    registrations = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("coordinated_student_details.html", student=student, registrations=registrations)

@faculty_bp.route("/manage-syllabus/<int:course_id>")
def manage_syllabus(course_id):
    if session.get("role") != "faculty":
        return redirect(url_for("auth.login_page"))
    
    faculty_id = session.get("faculty_id")
    conn = get_connection()
    cursor = conn.cursor()

    # Verify faculty is teaching this course (any instance)
    cursor.execute("SELECT 1 FROM course_instance WHERE faculty_id = :fid AND course_id = :cid", fid=faculty_id, cid=course_id)
    if not cursor.fetchone():
        flash("You are not authorized to manage the syllabus for this course.", "danger")
        return redirect(url_for("faculty.faculty_dashboard"))

    # Fetch Course Info
    cursor.execute("SELECT course_code, course_title FROM course_master WHERE course_id = :cid", cid=course_id)
    course = cursor.fetchone()

    # Fetch Details
    cursor.execute("SELECT obj_id, description, print_seq FROM course_objectives WHERE course_id = :cid ORDER BY print_seq", cid=course_id)
    objectives = cursor.fetchall()
    
    cursor.execute("SELECT outcome_id, outcome_desc, print_seq FROM course_outcomes WHERE course_id = :cid ORDER BY print_seq", cid=course_id)
    outcomes = cursor.fetchall()
    
    cursor.execute("SELECT desc_id, topic, duration_weeks FROM course_description WHERE course_id = :cid", cid=course_id)
    syllabus = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("manage_syllabus.html", course=course, course_id=course_id, objectives=objectives, outcomes=outcomes, syllabus=syllabus)

@faculty_bp.route("/update-syllabus/<int:course_id>", methods=["POST"])
def update_syllabus_action(course_id):
    if session.get("role") != "faculty":
        return redirect(url_for("auth.login_page"))
    
    faculty_id = session.get("faculty_id")
    conn = get_connection()
    cursor = conn.cursor()

    # Verify authorization
    cursor.execute("SELECT 1 FROM course_instance WHERE faculty_id = :fid AND course_id = :cid", fid=faculty_id, cid=course_id)
    if not cursor.fetchone():
        flash("Unauthorized", "danger")
        return redirect(url_for("faculty.faculty_dashboard"))

    type = request.form.get("type")

    try:
        if type == "objectives":
            cursor.execute("DELETE FROM course_objectives WHERE course_id = :cid", cid=course_id)
            descs = request.form.getlist("description[]")
            for i, d in enumerate(descs, 1):
                if d.strip():
                    cursor.execute("INSERT INTO course_objectives (course_id, description, print_seq) VALUES (:cid, :d, :seq)", 
                                   cid=course_id, d=d, seq=i)
        
        elif type == "outcomes":
            cursor.execute("DELETE FROM course_outcomes WHERE course_id = :cid", cid=course_id)
            descs = request.form.getlist("outcome_desc[]")
            for i, d in enumerate(descs, 1):
                if d.strip():
                    cursor.execute("INSERT INTO course_outcomes (course_id, outcome_desc, print_seq) VALUES (:cid, :d, :seq)", 
                                   cid=course_id, d=d, seq=i)

        elif type == "syllabus":
            cursor.execute("DELETE FROM course_description WHERE course_id = :cid", cid=course_id)
            topics = request.form.getlist("topic[]")
            weeks = request.form.getlist("duration_weeks[]")
            for t, w in zip(topics, weeks):
                if t.strip():
                    cursor.execute("INSERT INTO course_description (course_id, topic, duration_weeks) VALUES (:cid, :t, :w)", 
                                   cid=course_id, t=t, w=w)

        conn.commit()
        flash(f"{type.capitalize()} updated successfully!", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error: {str(e)}", "danger")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for("faculty.manage_syllabus", course_id=course_id))

# STUDENT GRADING / RESULTS
# ────────────────────────────────────────────────
@faculty_bp.route("/grading/<int:instance_id>", methods=["GET", "POST"])
def grading(instance_id):
    if session.get("role") != "faculty":
        return redirect(url_for("auth.login_page"))

    conn = get_connection()
    cursor = conn.cursor()

    # 1. Fetch Course Info
    cursor.execute("""
        SELECT c.course_code, c.course_title, ci.academic_session 
        FROM course_instance ci 
        JOIN course_master c ON ci.course_id = c.course_id 
        WHERE ci.instance_id = :1
    """, (instance_id,))
    course_info = cursor.fetchone()

    if request.method == "POST":
        student_ids = request.form.getlist("student_id[]")
        marks = request.form.getlist("numeric_marks[]")
        grades = request.form.getlist("grade[]")
        
        try:
            for sid, m, g in zip(student_ids, marks, grades):
                if not g and not m: continue
                val_m = float(m) if m else 0
                grade_to_save = g if g else str(val_m)
                # Upsert Results (Merge)
                cursor.execute("""
                    MERGE INTO results r
                    USING (SELECT :1 as sid, :2 as inst, :3 as sess FROM dual) src
                    ON (r.student_id = src.sid 
                        AND r.course_id = (SELECT course_id FROM course_instance WHERE instance_id = src.inst) 
                        AND r.academic_session = src.sess)
                    WHEN MATCHED THEN
                        UPDATE SET r.grade = :4
                    WHEN NOT MATCHED THEN
                        INSERT (result_id, student_id, course_id, academic_session, grade)
                        VALUES (RESULTS_SEQ.NEXTVAL, :1, (SELECT course_id FROM course_instance WHERE instance_id = src.inst), :3, :4)
                """, (sid, instance_id, course_info[2], grade_to_save))
            
            conn.commit()
            flash("Grades submitted successfully!", "success")
        except Exception as e:
            flash(f"Error: {str(e)}", "danger")
            conn.rollback()

    # 2. Fetch Enrolled Students & Existing Grades
    cursor.execute("""
        SELECT s.student_id, s.name, s.enrollment_no, r.grade, r.grade
        FROM student_registration_courses src
        JOIN student_registration sr ON src.reg_id = sr.reg_id
        JOIN students s ON sr.student_id = s.student_id
        LEFT JOIN results r ON s.student_id = r.student_id 
                           AND r.course_id = (SELECT course_id FROM course_instance WHERE instance_id = :1)
        WHERE src.course_instance_id = :1
        ORDER BY s.name
    """, (instance_id,))
    students = cursor.fetchall() or []

    cursor.close()
    conn.close()

    return render_template("enter_grades.html", students=students, course_info=course_info, instance_id=instance_id)
