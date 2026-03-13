from flask import Blueprint, render_template, session, redirect, request, flash, make_response
from config import get_connection
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

student_bp = Blueprint("student", __name__)

# Helper: Get current academic session (make dynamic later, e.g., from DB or config)
def get_current_session():
    # For now match your PDF sample; later fetch from DB table or setting
    return "W25"  # Winter 2025 as per your sample PDF

# Student Dashboard
@student_bp.route("/dashboard")
def student_dashboard():
    if session.get("role") != "student":
        flash("Access denied – Student only", "danger")
        return redirect("/")
    return render_template("student_dashboard.html", name=session.get("name", "Student"))

# Examination - View cleared & backlog subjects (placeholder - expand later)
@student_bp.route("/examination", methods=["GET", "POST"])
def examination():
    if session.get("role") != "student":
        return redirect("/")
    if request.method == "POST":
        semester = request.form.get("semester")
        academic_session = request.form.get("academic_session")
        if not semester or not academic_session:
            flash("Please select semester and academic session", "danger")
            return redirect("/student/examination")
        # TODO: Real query for cleared/backlog subjects based on student_id, semester, session
        flash(f"Results would be shown here for semester {semester} session {academic_session}", "info")
        return redirect("/student/examination")
    return render_template("examination.html")

# Course Registration - DC + DE selection + PDF
@student_bp.route("/register_courses", methods=["GET", "POST"])
def register_courses():
    if session.get("role") != "student":
        flash("Access denied", "danger")
        return redirect("/student/dashboard")

    current_session = get_current_session()

    conn = get_connection()
    cursor = conn.cursor()
    try:
        # DC Courses (compulsory - all must be selected)
        cursor.execute("""
            SELECT c.course_code, c.course_title, c.credits, f.faculty_name AS coordinator
            FROM course_instance ci
            JOIN course_master c ON ci.course_id = c.course_id
            JOIN faculty f ON ci.faculty_id = f.faculty_id
            WHERE ci.offering_session = :1 AND c.course_type = 'DC'
        """, (current_session,))
        dc_courses = cursor.fetchall()

        # DE Courses (electives - exactly 2)
        cursor.execute("""
            SELECT c.course_code, c.course_title, c.credits, f.faculty_name AS coordinator
            FROM course_instance ci
            JOIN course_master c ON ci.course_id = c.course_id
            JOIN faculty f ON ci.faculty_id = f.faculty_id
            WHERE ci.offering_session = :1 AND c.course_type = 'DE'
        """, (current_session,))
        de_courses = cursor.fetchall()

        if request.method == "POST":
            selected_dc = request.form.getlist("dc_selected")
            selected_de = request.form.getlist("de_selected")

            # Validation
            if len(selected_dc) != len(dc_courses):
                flash("You must select ALL DC (compulsory) courses", "danger")
                return redirect("/student/register_courses")

            if len(selected_de) != 2:
                flash("You must select EXACTLY 2 DE (elective) courses", "danger")
                return redirect("/student/register_courses")

            # Combine for PDF
            all_selected_codes = selected_dc + selected_de

            flash("Courses registered successfully. Generating PDF...", "success")
            return generate_registration_pdf(
                session["student_id"],
                all_selected_codes,
                current_session  # pass it!
            )

        return render_template("register_courses.html",
                               dc_courses=dc_courses,
                               de_courses=de_courses,
                               current_session=current_session)

    except Exception as e:
        flash(f"Error loading courses: {str(e)}", "danger")
        return redirect("/student/dashboard")
    finally:
        cursor.close()
        conn.close()

# Course Details Page (fixed - now shows full details from multiple tables)
@student_bp.route("/course_details/<course_code>")
def course_details(course_code):
    if session.get("role") != "student":
        flash("Access denied", "danger")
        return redirect("/student/register_courses")

    current_session = get_current_session()
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Basic course info from course_master + instance
        cursor.execute("""
            SELECT cm.course_id, cm.course_code, cm.course_title, cm.course_type,
                   cm.l, cm.t, cm.p, cm.program_name,
                   ci.section, ci.batch, ci.slot, f.faculty_name AS faculty,
                   ci.offering_session
            FROM course_master cm
            JOIN course_instance ci ON cm.course_id = ci.course_id
            JOIN faculty f ON ci.faculty_id = f.faculty_id
            WHERE cm.course_code = :1 AND ci.offering_session = :2
        """, (course_code, current_session))
        course = cursor.fetchone()

        if not course:
            flash("Course not found or not offered this session", "danger")
            return redirect("/student/register_courses")

        # Fetch related data (examples - expand as needed)
        cursor.execute("SELECT prerequisite_id FROM prerequisites WHERE course_id = (SELECT course_id FROM course_master WHERE course_code = :1)", (course_code,))
        prerequisites = cursor.fetchall()

        cursor.execute("SELECT course_obj_desc FROM course_objective WHERE course_id = (SELECT course_id FROM course_master WHERE course_code = :1) ORDER BY printing_seq", (course_code,))
        objectives = cursor.fetchall()

        # ... similarly fetch outcomes, books, description, etc.

        return render_template("course_details.html",
                               course=course,
                               prerequisites=prerequisites,
                               objectives=objectives,
                               # add more
                               current_session=current_session)

    except Exception as e:
        flash(f"Error loading course details: {str(e)}", "danger")
        return redirect("/student/register_courses")
    finally:
        cursor.close()
        conn.close()

# PDF Generation - fixed & enhanced
def generate_registration_pdf(student_id, selected_course_codes):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Student info
        cursor.execute("""
            SELECT name, enrollment_no, faculty_advisor, mobile, address, email, 
                   is_hosteller, registration_date
            FROM students WHERE student_id = :1
        """, (student_id,))
        student = cursor.fetchone()

        if not student:
            flash("Student record not found", "danger")
            return redirect("/student/register_courses")

        name, enrollment_no, advisor, mobile, address, email, hosteller, reg_date = student
        hosteller_text = 'Yes' if hosteller == 'Y' else 'No'
        reg_date_str = reg_date.strftime('%d/%m/%Y') if reg_date else 'Not Available'

        # Course details
        placeholders = ','.join([':course'+str(i) for i in range(len(selected_course_codes))])
        cursor.execute(f"""
            SELECT c.course_code, c.course_title, ci.section, ci.batch, ci.slot,
                   c.course_type, c.credits, f.faculty_name AS coordinator
            FROM course_master c
            JOIN course_instance ci ON c.course_id = ci.course_id
            JOIN faculty f ON ci.faculty_id = f.faculty_id
            WHERE c.course_code IN ({placeholders})
            ORDER BY c.course_type DESC, c.course_code
        """, {f'course{i}': code for i, code in enumerate(selected_course_codes)})

        courses = cursor.fetchall()

        # Totals
        dc_count = len([c for c in courses if c[5] == 'DC'])
        de_count = len([c for c in courses if c[5] == 'DE'])
        total_credits = sum(c[6] for c in courses)
        total_courses = len(courses)
        theory_credits = sum(c[6] for c in courses if 'LAB' not in c[1].upper() and 'PRACTICAL' not in c[1].upper())
        practical_credits = total_credits - theory_credits

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=80, bottomMargin=36)
        styles = getSampleStyleSheet()

        elements = []

        # VNIT Logo (save your logo as static/images/vnit_logo.png)
        try:
            logo = Image("static/images/vnit_logo.png", width=80, height=80)
            elements.append(logo)
        except:
            pass  # skip if no logo

        elements.append(Spacer(1, 6))

        # Header - exact match
        elements.append(Paragraph("Visvesvaraya National Institute of Technology", styles['Heading2']))
        elements.append(Paragraph("Nagpur", styles['Heading4']))
        elements.append(Paragraph("DEPARTMENT OF COMPUTER SCIENCE & ENGINEERING", styles['Heading4']))
        elements.append(Paragraph("Name of PG Program: COMPUTER SCIENCE & ENGG(MTech)", styles['Normal']))
        elements.append(Spacer(1, 12))
        elements.append(Paragraph("FINAL SUBMITTED", styles['Heading3']))
        elements.append(Paragraph(f"Date: {datetime.now().strftime('%d/%m/%Y')}", styles['Normal']))
        elements.append(Paragraph(f"Page 1 of 1", styles['Normal']))
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(f"{current_session}", styles['Heading3']))

        elements.append(Spacer(1, 18))

        # Student info - exact labels
        student_lines = [
            f"Name: {name}",
            f"ID No./Enrl. No.: {enrollment_no}",
            f"Name of Fac. Adv.: {advisor or 'Not Assigned'}",
            f"Contact No.: {mobile or 'Not Provided'}",
            f"Current Address: {address or 'Not Provided'}",
            f"Email: {email}",
            f"Hosteller: {hosteller_text}",
            f"Dt. of Registration: {reg_date_str}"
        ]
        for line in student_lines:
            elements.append(Paragraph(line, styles['Normal']))

        elements.append(Spacer(1, 24))

        # Course table - 9 columns, orange header
        table_data = [["Sr. No.", "Course code", "Course Title", "Section", "Batch", "Slot", "Course", "Credits", "Co-ordinator"]]
        for i, course in enumerate(courses, 1):
            table_data.append([
                str(i),
                course[0],
                course[1],
                course[2] or "DEFAULT",
                course[3] or "-",
                course[4] or "-",
                course[5],
                str(course[6]),
                course[7] or "Not Assigned"
            ])

        table = Table(table_data, colWidths=[35, 65, 145, 50, 50, 50, 50, 50, 115])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.orange),
            ('TEXTCOLOR', (0,0), (-1,0), colors.black),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 10),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND', (0,1), (-1,-1), colors.whitesmoke),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('FONTSIZE', (0,1), (-1,-1), 9),
        ]))

        elements.append(table)

        elements.append(Spacer(1, 24))

        # Totals - exact wording and placement
        elements.append(Paragraph("Details regarding registered Courses for the Session :", styles['Normal']))
        elements.append(Paragraph(f"DC : {dc_count}   DE : {de_count}", styles['Normal']))
        elements.append(Paragraph(f"Theory : {theory_credits}   Practical : {practical_credits}", styles['Normal']))
        elements.append(Paragraph(f"Total Credit registered : {total_credits}", styles['Normal']))
        elements.append(Paragraph(f"Total No. of courses registered in the session : {total_courses}", styles['Normal']))

        elements.append(Spacer(1, 48))

        # Signatures - two columns
        sig_table = Table([
            ["Signature of Student", "Signature of Faculty Advisor"],
            [name, "____________________"]
        ], colWidths=[250, 250])
        sig_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ]))
        elements.append(sig_table)

        elements.append(Spacer(1, 24))
        elements.append(Paragraph(f"Printed By {name}   Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", styles['Italic']))

        doc.build(elements)

        buffer.seek(0)
        response = make_response(buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=registration_{enrollment_no}_{datetime.now().strftime("%Y%m%d")}.pdf'
        return response

    except Exception as e:
        flash(f"PDF generation failed: {str(e)}", "danger")
        return redirect("/student/register_courses")

    finally:
        cursor.close()
        conn.close()