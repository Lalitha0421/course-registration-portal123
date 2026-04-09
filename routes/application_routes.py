from flask import Blueprint, render_template, request
from config import get_connection

application_bp = Blueprint("application", __name__)

@application_bp.route("/register", methods=["GET","POST"])
def register():

    if request.method == "GET":
        return render_template("student_application.html")

    name = request.form.get("name")
    email = request.form.get("email")
    mobile = request.form.get("mobile")
    program = request.form.get("program")
    aadhar = request.form.get("aadhar")
    dob = request.form.get("dob")
    address = request.form.get("address")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT NVL(MAX(student_id),0)+1 FROM students")
    sid = cursor.fetchone()[0]

    cursor.execute("""
        INSERT INTO students
        (student_id,name,email,mobile,program,aadhar,dob,address,status)
        VALUES(:1,:2,:3,:4,:5,:6,TO_DATE(:7,'YYYY-MM-DD'),:8,'PENDING')
    """,
    (sid,name,email,mobile,program,aadhar,dob,address))

    conn.commit()

    cursor.close()
    conn.close()

    return "Application Submitted Successfully"