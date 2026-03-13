from flask import Blueprint, render_template, request, session, redirect
from config import get_connection

admin_bp = Blueprint("admin", __name__)


# -------------------------
# ADMIN DASHBOARD
# -------------------------
@admin_bp.route("/admin_dashboard")
def admin_dashboard():

    if "role" not in session or session["role"] != "admin":
        return redirect("/")

    return render_template("admin_dashboard.html")


# -------------------------
# ADD COURSE
# -------------------------
@admin_bp.route("/admin/add_course", methods=["GET", "POST"])   # CHANGE: better route structure
def add_course():

    if "role" not in session or session["role"] != "admin":
        return redirect("/")

    if request.method == "GET":
        return render_template("add_course.html")

    course_code = request.form["course_code"]
    course_title = request.form["course_title"]
    credits = request.form["credits"]
    course_type = request.form["course_type"]

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT NVL(MAX(course_id),0)+1 FROM course_master")
    course_id = cursor.fetchone()[0]

    cursor.execute("""
    INSERT INTO course_master
    VALUES(:1,:2,:3,:4,'MTECH',0,0,0,:5)
    """,
    (course_id, course_code, course_title, course_type, credits))

    conn.commit()

    cursor.close()
    conn.close()

    return redirect("/admin_dashboard")     # CHANGE: redirect instead of plain text


# -------------------------
# ADD FACULTY
# -------------------------
@admin_bp.route("/admin/add_faculty", methods=["GET", "POST"])   # CHANGE
def add_faculty():

    if "role" not in session or session["role"] != "admin":
        return redirect("/")

    if request.method == "GET":
        return render_template("add_faculty.html")

    faculty_name = request.form["faculty_name"]
    email = request.form["email"]
    department = request.form["department"]

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT NVL(MAX(faculty_id),0)+1 FROM faculty")
    faculty_id = cursor.fetchone()[0]

    cursor.execute("""
    INSERT INTO faculty(faculty_id, faculty_name, email, department)
    VALUES(:1,:2,:3,:4)
    """,
    (faculty_id, faculty_name, email, department))

    conn.commit()

    cursor.close()
    conn.close()

    return redirect("/admin_dashboard")     # CHANGE


# -------------------------
# CREATE COURSE INSTANCE
# -------------------------
@admin_bp.route("/admin/create_course_instance", methods=["GET", "POST"])   # CHANGE
def create_course_instance():

    if "role" not in session or session["role"] != "admin":
        return redirect("/")

    conn = get_connection()
    cursor = conn.cursor()

    if request.method == "GET":

        cursor.execute("SELECT course_id,course_code FROM course_master")
        courses = cursor.fetchall()

        cursor.execute("SELECT faculty_id,faculty_name FROM faculty")
        faculty = cursor.fetchall()

        cursor.close()
        conn.close()

        return render_template(
            "create_course_instance.html",
            courses=courses,
            faculty=faculty
        )

    course_id = request.form["course_id"]
    faculty_id = request.form["faculty_id"]
    semester = request.form["semester"]
    academic_session = request.form["academic_session"]

    cursor.execute("SELECT NVL(MAX(instance_id),0)+1 FROM course_instance")
    instance_id = cursor.fetchone()[0]

    cursor.execute("""
    INSERT INTO course_instance(
        instance_id,
        course_id,
        faculty_id,
        academic_session,
        semester
    )
    VALUES(:1,:2,:3,:4,:5)
    """,
    (instance_id, course_id, faculty_id, academic_session, semester))   # CHANGE: correct order

    conn.commit()

    cursor.close()
    conn.close()

    return redirect("/admin_dashboard")     # CHANGE


# -------------------------
# VIEW STUDENTS
# -------------------------
@admin_bp.route("/admin/view_students")    # CHANGE
def view_students():

    if "role" not in session or session["role"] != "admin":
        return redirect("/")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT student_id, name, email, program
    FROM students
    """)   # CHANGE: column name based on your schema

    students = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("view_students.html", students=students)

@admin_bp.route("/pending_students")
def pending_students():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT student_id,name,email
    FROM students
    WHERE status='PENDING'
    """)

    students = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("pending_students.html",students=students)

@admin_bp.route("/approve_student/<int:sid>")
def approve_student(sid):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("UPDATE students SET status='APPROVED' WHERE student_id=:1",[sid])

    cursor.execute("SELECT NVL(MAX(user_id),0)+1 FROM users")
    uid = cursor.fetchone()[0]

    login_id = f"student{sid}"
    password = "123456"

    cursor.execute("""
    INSERT INTO users
    VALUES(:1,:2,:3,'student',:4)
    """,(uid,login_id,password,sid))

    conn.commit()

    cursor.close()
    conn.close()

    return "Student Approved"

# routes/admin_routes.py
from flask import Blueprint, Response, make_response
from config import get_connection  # your oracle connection function
import pandas as pd
import io

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/export_students', methods=['GET'])
def export_students():
    conn = get_connection()
    try:
        # Query all students (you can add WHERE clauses later, e.g. by program/session)
        query = """
            SELECT 
                student_id,
                name,
                email,
                mobile,
                program,
                aadhar,
                dob,
                address,
                enrollment_no,
                faculty_advisor,
                is_hosteller,
                registration_date,
                status
            FROM students
            ORDER BY registration_date DESC
        """

        df = pd.read_sql(query, conn)

        # Optional: nicer column names for the Excel
        df.columns = [
            'Student ID', 'Full Name', 'Email', 'Mobile', 'Program', 'Aadhaar',
            'DOB', 'Address', 'Enrollment No', 'Faculty Advisor', 'Hosteller (Y/N)',
            'Registration Date', 'Status'
        ]

        # Create Excel in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Registered Students')

        output.seek(0)

        # Prepare response for download
        response = make_response(output.read())
        response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response.headers['Content-Disposition'] = 'attachment; filename=students_registered.xlsx'

        return response

    except Exception as e:
        return f"Error generating file: {str(e)}", 500

    finally:
        conn.close()