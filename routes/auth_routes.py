from flask import Blueprint, render_template, request, redirect, session, flash, url_for
from config import get_connection
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint("auth", __name__)

# ──────────────────────────────────────────────
# LOGIN PAGE
# ──────────────────────────────────────────────
@auth_bp.route("/")
def login_page():
    return render_template("login.html")


# ──────────────────────────────────────────────
# PROCESS LOGIN
# ──────────────────────────────────────────────
@auth_bp.route("/login", methods=["POST"])
def login():
    login_id = request.form.get("login_id")
    password = request.form.get("password")
    role     = request.form.get("role")

    if not login_id or not password or role not in ["student", "admin", "faculty"]:
        flash("Login ID, Password and Role are required.", "danger")
        return redirect("/")

    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT user_id, password_hash, role
            FROM users
            WHERE login_id = :1 AND role = :2
        """, (login_id, role))

        user = cursor.fetchone()

        if not user:
            flash("No account found for this Login ID and Role", "danger")
            return redirect("/")

        stored_password = user[1]
        if not check_password_hash(stored_password, password):
            # Fallback for plain text if any old ones exist during migration (optional)
            if stored_password != password:
                flash("Incorrect password", "danger")
                return redirect("/")

        # Success
        session["user_id"]  = user[0]
        session["role"]     = user[2]
        session["login_id"] = login_id

        if role == "student":
            cursor.execute("""
                SELECT student_id, name 
                FROM students 
                WHERE user_id = :1
            """, (user[0],))
            student = cursor.fetchone()
            if student:
                session["student_id"] = student[0]
                session["name"] = student[1]
        
        elif role == "faculty":
            cursor.execute("""
                SELECT faculty_id, faculty_name 
                FROM faculty 
                WHERE user_id = :1
            """, (user[0],))
            faculty = cursor.fetchone()
            if faculty:
                session["faculty_id"] = faculty[0]
                session["name"] = faculty[1]

        flash("Login successful as " + role.capitalize(), "success")

        if role == "admin":
            return redirect(url_for("admin.dashboard"))
        elif role == "faculty":
            return redirect(url_for("faculty.faculty_dashboard"))
        else:
            return redirect(url_for("student.student_dashboard"))

    except Exception as e:
        flash(f"Login failed: {str(e)}", "danger")
        return redirect("/")

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ──────────────────────────────────────────────
# NEW STUDENT REGISTRATION
# ──────────────────────────────────────────────
@auth_bp.route("/student_application", methods=["GET", "POST"])
def student_application():
    if request.method == "GET":
        return render_template("student_application.html")

    conn = None
    cursor = None
    try:
        # Get form values
        name            = request.form.get("name")
        email           = request.form.get("email")
        mobile          = request.form.get("mobile") or None
        program         = request.form.get("program")
        aadhar          = request.form.get("aadhar") or None
        dob_str         = request.form.get("dob")
        address         = request.form.get("address") or None
        is_hosteller    = request.form.get("is_hosteller", "N")

        if not all([name, email, program]):
            flash("Name, Email, and Program are required.", "danger")
            return redirect("/student_application")

        # Parse DOB
        dob = None
        if dob_str:
            try:
                dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
            except ValueError:
                flash("Invalid DOB format", "danger")
                return redirect("/student_application")

        conn = get_connection()
        cursor = conn.cursor()

        # Check duplicate application by email
        cursor.execute("SELECT 1 FROM students WHERE email = :1", (email,))
        if cursor.fetchone():
            flash("An application with this email already exists.", "danger")
            return redirect("/student_application")

        # Insert student application (status PENDING)
        # Note: Enrollment NO and USER record are created by ADMIN later
        cursor.execute("""
            INSERT INTO students (
                STUDENT_ID, NAME, EMAIL, MOBILE, AADHAR, PROGRAM, DOB, ADDRESS,
                IS_HOSTELLER, REGISTRATION_DATE, STATUS
            ) VALUES (
                STUDENTS_SEQ.NEXTVAL, :name, :email, :mobile, :aadhar, :program,
                :dob, :address, :is_hosteller, SYSDATE, 'PENDING'
            )
        """, {
            'name': name,
            'email': email,
            'mobile': mobile,
            'aadhar': aadhar,
            'program': program,
            'dob': dob,
            'address': address,
            'is_hosteller': is_hosteller
        })

        conn.commit()
        flash("Application submitted successfully! Admin will review your details and send your credentials to your email.", "success")
        return redirect("/")

    except Exception as e:
        if conn:
            conn.rollback()
        flash(f"Registration failed: {str(e)}", "danger")
        return redirect("/student_application")

    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


# ──────────────────────────────────────────────
# LOGOUT
# ──────────────────────────────────────────────
@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Successfully logged out", "info")
    return redirect(url_for("auth.login_page"))