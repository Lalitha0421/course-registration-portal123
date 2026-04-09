from flask import Blueprint, render_template, request, session, redirect, send_file
from config import get_connection
from reportlab.pdfgen import canvas
import io

course_bp = Blueprint("course", __name__)


# -------------------------
# REGISTER COURSES
# -------------------------
@course_bp.route("/register_courses", methods=["POST"])
def register_courses():

    if "user_id" not in session:
        return redirect("/")

    selected_courses = request.form.getlist("course_ids")

    conn = get_connection()
    cursor = conn.cursor()

    dc_count = 0
    de_count = 0

    # -------------------------
    # COUNT DC / DE
    # -------------------------
    for instance_id in selected_courses:

        cursor.execute("""
        SELECT cm.course_type
        FROM course_instance ci
        JOIN course_master cm
        ON ci.course_id = cm.course_id
        WHERE ci.instance_id = :1
        """, [instance_id])

        row = cursor.fetchone()

        if not row:
            continue

        course_type = row[0]

        if course_type == "DC":
            dc_count += 1
        elif course_type == "DE":
            de_count += 1


    # -------------------------
    # VALIDATION
    # -------------------------

    if dc_count < 3:
        cursor.close()
        conn.close()
        return "Minimum 3 DC courses required"

    if de_count > 2:
        cursor.close()
        conn.close()
        return "Maximum 2 DE courses allowed"


    # -------------------------
    # GET STUDENT ID
    # -------------------------

    cursor.execute("""
    SELECT student_id
    FROM users
    WHERE user_id = :1
    """,[session["user_id"]])

    student_id = cursor.fetchone()[0]
    # student_id = cursor.fetchone()[0]

    semester = session.get("semester")
    academic_session = session.get("academic_session")


    # -------------------------
    # CREATE REGISTRATION
    # -------------------------

    cursor.execute("SELECT NVL(MAX(reg_id),0)+1 FROM student_registration")
    reg_id = cursor.fetchone()[0]

    cursor.execute("""
    INSERT INTO student_registration
    VALUES (:1,:2,:3,:4,SYSDATE)
    """, (reg_id, student_id, semester, academic_session))


    # -------------------------
    # INSERT COURSES
    # -------------------------

    cursor.execute("SELECT NVL(MAX(id),0)+1 FROM registration_courses")
    insert_id = cursor.fetchone()[0]

    for instance_id in selected_courses:

        cursor.execute("""
        SELECT cm.course_type
        FROM course_instance ci
        JOIN course_master cm
        ON ci.course_id = cm.course_id
        WHERE ci.instance_id = :1
        """, [instance_id])

        course_type = cursor.fetchone()[0]

        cursor.execute("""
        INSERT INTO registration_courses
        VALUES (:1,:2,:3,:4)
        """, (insert_id, reg_id, instance_id, course_type))

        insert_id += 1

    conn.commit()

    cursor.close()
    conn.close()

    return redirect(f"/registration_pdf/{reg_id}")


# -------------------------
# COURSE DETAILS
# -------------------------
@course_bp.route("/course_details/<int:instance_id>")
def course_details(instance_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT cm.course_code,
           cm.course_title,
           cm.credits,
           cm.course_type,
           f.faculty_name,
           cm.course_id
    FROM course_instance ci
    JOIN course_master cm
    ON ci.course_id = cm.course_id
    JOIN faculty f
    ON ci.faculty_id = f.faculty_id
    WHERE ci.instance_id = :1
    """, [instance_id])

    course = cursor.fetchone()
    course_id = course[5]

    cursor.execute("""
    SELECT description
    FROM course_objectives
    WHERE course_id = :1
    ORDER BY print_seq
    """, [course_id])
    objectives = cursor.fetchall()

    cursor.execute("""
    SELECT outcome_desc
    FROM course_outcomes
    WHERE course_id = :1
    ORDER BY print_seq
    """, [course_id])
    outcomes = cursor.fetchall()

    cursor.execute("""
    SELECT topic,duration_weeks
    FROM course_description
    WHERE course_id = :1
    """, [course_id])
    description = cursor.fetchall()

    cursor.execute("""
    SELECT title
    FROM text_books
    WHERE course_id = :1
    """, [course_id])
    textbooks = cursor.fetchall()

    cursor.execute("""
    SELECT title
    FROM reference_books
    WHERE course_id = :1
    """, [course_id])
    refbooks = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "course_details.html",
        course=course,
        objectives=objectives,
        outcomes=outcomes,
        description=description,
        textbooks=textbooks,
        refbooks=refbooks
    )


# -------------------------
# REGISTRATION PDF
# -------------------------
@course_bp.route("/registration_pdf/<int:reg_id>")
def registration_pdf(reg_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT cm.course_code,
           cm.course_title,
           cm.credits
    FROM registration_courses rc
    JOIN course_instance ci
    ON rc.course_instance_id = ci.instance_id
    JOIN course_master cm
    ON ci.course_id = cm.course_id
    WHERE rc.reg_id = :1
    """, [reg_id])

    courses = cursor.fetchall()

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer)

    y = 800
    pdf.drawString(200, 820, "Course Registration")

    for c in courses:
        line = f"{c[0]}   {c[1]}   Credits:{c[2]}"
        pdf.drawString(50, y, line)
        y -= 20

    pdf.save()
    buffer.seek(0)

    cursor.close()
    conn.close()

    return send_file(
        buffer,
        as_attachment=True,
        download_name="registration.pdf",
        mimetype="application/pdf"
    )

@course_bp.route("/all")
def all_courses():
    from flask import jsonify
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT cm.course_id, cm.course_code, cm.course_title, cm.course_type, cm.credits, ci.academic_session
        FROM course_master cm
        LEFT JOIN course_instance ci ON cm.course_id = ci.course_id
        ORDER BY ci.academic_session DESC, cm.course_code
    """)
    rows = cursor.fetchall()
    courses = []
    for r in rows:
        courses.append({
            "course_id": r[0],
            "course_code": r[1],
            "course_title": r[2],
            "course_type": r[3],
            "credits": r[4],
            "session": r[5] or "Unassigned"
        })
    cursor.close()
    conn.close()
    return jsonify(courses)