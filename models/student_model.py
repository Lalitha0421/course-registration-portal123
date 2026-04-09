from flask import Blueprint, render_template, session, redirect, request
from config import get_connection

student_bp = Blueprint("student", __name__)


# -------------------------
# STUDENT DASHBOARD
# -------------------------
@student_bp.route("/student_dashboard")
def student_dashboard():

    if "user_id" not in session:
        return redirect("/")

    if session["role"] != "student":
        return "Unauthorized"

    return render_template("student_dashboard.html")


# -------------------------
# STUDENT PROFILE REGISTER
# -------------------------
@student_bp.route("/student_register", methods=["GET","POST"])
def student_register():

    if "user_id" not in session:
        return redirect("/")

    if session["role"] != "student":
        return "Unauthorized"

    if request.method == "GET":
        return render_template("student_register.html")

    name = request.form["name"]
    email = request.form["email"]
    program = request.form["program"]

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT NVL(MAX(student_id),0)+1 FROM students")
    sid = cursor.fetchone()[0]

    cursor.execute("""
        INSERT INTO students(
            student_id,
            user_id,
            name,
            email,
            program
        )
        VALUES(:1,:2,:3,:4,:5)
    """,(sid, session["user_id"], name, email, program))

    conn.commit()

    cursor.close()
    conn.close()

    return redirect("/student_dashboard")