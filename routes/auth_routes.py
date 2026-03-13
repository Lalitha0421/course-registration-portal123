from flask import Blueprint, render_template, request, redirect, session, flash
from config import get_connection
from datetime import datetime

auth_bp = Blueprint("auth", __name__)

# ──────────────────────────────────────────────
# LOGIN PAGE
# ──────────────────────────────────────────────
@auth_bp.route("/")
def login_page():
    return render_template("login.html")


# ──────────────────────────────────────────────
# PROCESS LOGIN - PLAIN TEXT COMPARISON (temporary)
# ──────────────────────────────────────────────
@auth_bp.route("/login", methods=["POST"])
def login():
    login_id = request.form.get("login_id")
    password = request.form.get("password")
    role     = request.form.get("role")

    if not login_id or not password or role not in ["student", "admin", "faculty"]:
        flash("Login ID, Password and Role are required.", "danger")
        return redirect("/")

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT user_id, password_hash, role
            FROM users
            WHERE login_id = :1 AND role = :2
        """, (login_id, role))

        user = cursor.fetchone()

        if not user:
            flash("No account found for this Login ID and Role", "danger")
            return redirect("/")

        # Temporary plain text comparison (bypass bcrypt issue)
        stored_password = user[1]
        if stored_password != password:
            flash("Incorrect password", "danger")
            return redirect("/")

        # Login success
        session["user_id"]   = user[0]
        session["role"]      = user[2]
        session["login_id"]  = login_id

        # For students: fetch name and student_id
        if role == "student":
            cursor.execute("""
                SELECT student_id, name 
                FROM students 
                WHERE enrollment_no = :1
            """, (login_id,))
            student = cursor.fetchone()
            if student:
                session["student_id"] = student[0]
                session["name"] = student[1]

        flash(f"Login successful as {role.capitalize()}", "success")

        if role == "student":
            return redirect("/student/dashboard")
        elif role == "admin":
            return redirect("/admin_dashboard")
        elif role == "faculty":
            return redirect("/faculty_dashboard")

    except Exception as e:
        flash(f"Login error: {str(e)}", "danger")
        return redirect("/")

    finally:
        cursor.close()
        conn.close()


# ──────────────────────────────────────────────
# LOGOUT
# ──────────────────────────────────────────────
@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully", "info")
    return redirect("/")


# ──────────────────────────────────────────────
# STUDENT REGISTRATION (fixed column names - uppercase)
# ──────────────────────────────────────────────
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("student_application.html")

    # Form data
    name            = request.form.get("name")
    email           = request.form.get("email")
    mobile          = request.form.get("mobile")
    program         = request.form.get("program")
    aadhar          = request.form.get("aadhar")
    dob             = request.form.get("dob")  # YYYY-MM-DD
    address         = request.form.get("address")
    enrollment_no   = request.form.get("enrollment_no")
    faculty_advisor = request.form.get("faculty_advisor")
    is_hosteller    = request.form.get("is_hosteller", "N")
    password        = request.form.get("password")
    confirm_pw      = request.form.get("confirm_password")

    # Validation
    errors = []
    if not all([name, email, enrollment_no, password]):
        errors.append("Required: Name, Email, Enrollment No, Password")
    if password != confirm_pw:
        errors.append("Passwords do not match")
    if len(password) < 8:
        errors.append("Password must be at least 8 characters")
    if len(enrollment_no) < 5 or len(enrollment_no) > 20:
        errors.append("Enrollment No should be 5–20 characters")

    if errors:
        for err in errors:
            flash(err, "danger")
        return redirect("/register")

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT user_id FROM users WHERE login_id = :1", (enrollment_no,))
        if cursor.fetchone():
            flash("Enrollment number already registered", "danger")
            return redirect("/register")

        # For development: store plain text password
        # Later we will add hashing + reset page
        cursor.execute("""
            INSERT INTO users (login_id, password_hash, role, email, name, created_at)
            VALUES (:1, :2, 'student', :3, :4, SYSDATE)
        """, (enrollment_no, password, email, name))  # plain text for now

        # Get the user_id just inserted
        cursor.execute("SELECT user_id FROM users WHERE login_id = :1", (enrollment_no,))
        user_id = cursor.fetchone()[0]

        # Insert into students - UPPERCASE columns
        cursor.execute("""
            INSERT INTO students (
                STUDENT_ID, NAME, EMAIL, MOBILE, PROGRAM, AADHAR, DOB, ADDRESS,
                ENROLLMENT_NO, FACULTY_ADVISOR, IS_HOSTELLER, REGISTRATION_DATE, STATUS
            ) VALUES (
                STUDENTS_SEQ.NEXTVAL, :1, :2, :3, :4, :5, 
                TO_DATE(:6, 'YYYY-MM-DD'), :7, :8, :9, :10, SYSDATE, 'APPROVED'
            )
        """, (name, email, mobile, program, aadhar, dob, address,
              enrollment_no, faculty_advisor, is_hosteller))

        conn.commit()
        flash("Registration successful! You can now login.", "success")
        return redirect("/")

    except Exception as e:
        conn.rollback()
        flash(f"Registration failed: {str(e)}", "danger")
        return redirect("/register")

    finally:
        cursor.close()
        conn.close()


# ──────────────────────────────────────────────
# DASHBOARD ROUTES (protected)
# ──────────────────────────────────────────────
@auth_bp.route("/admin_dashboard")
def admin_dashboard():
    if session.get("role") != "admin":
        flash("Access denied – Admin only", "danger")
        return redirect("/")
    return render_template("admin_dashboard.html")


@auth_bp.route("/faculty_dashboard")
def faculty_dashboard():
    if session.get("role") != "faculty":
        flash("Access denied – Faculty only", "danger")
        return redirect("/")
    return render_template("faculty_dashboard.html")