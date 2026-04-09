from flask import make_response
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from io import BytesIO

# ─── ADD THIS LINE ────────────────────────────────────────
from config import get_connection   # or correct path/module
# ──────────────────────────────────────────────────────────

def generate_registration_pdf(student_id, selected_courses):
    conn = get_connection()
    cursor = conn.cursor()

    # Your existing student query
    cursor.execute("""
        SELECT name, enrollment_no, faculty_advisor, mobile, address, email, is_hosteller, registration_date
        FROM students
        WHERE student_id = :1
    """, (student_id,))
    student = cursor.fetchone()

    if not student:
        raise ValueError("Student not found")

    # Course query - FIXED: use tuple for IN clause properly
    placeholders = ','.join([f':{i+1}' for i in range(len(selected_courses))])
    query = f"""
        SELECT c.course_code, c.course_title, ci.section, ci.batch, ci.slot, 
               c.course_type, c.credits, f.faculty_name AS co_ordinator
        FROM course_master c
        JOIN course_instance ci ON c.course_id = ci.course_id
        JOIN faculty f ON ci.faculty_id = f.faculty_id
        WHERE c.course_code IN ({placeholders})
    """
    cursor.execute(query, selected_courses)   # pass list/tuple directly

    courses = cursor.fetchall()

    cursor.close()
    conn.close()   # Consider using context manager in production

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()

    elements = []

    # Header - match your PDF sample more closely
    elements.append(Paragraph("Visvesvaraya National Institute of Technology", styles['Heading1']))
    elements.append(Paragraph("Nagpur", styles['Normal']))
    elements.append(Paragraph("W25", styles['Normal']))  # Winter 2025?
    elements.append(Spacer(1, 12))

    elements.append(Paragraph(f"Name: {student[0] or 'N/A'}", styles['Normal']))
    elements.append(Paragraph(f"ID No./Enrl. No.: {student[1] or 'N/A'}", styles['Normal']))
    elements.append(Paragraph(f"Name of Fac. Adv.: {student[2] or 'N/A'}", styles['Normal']))
    elements.append(Paragraph(f"Contact No.: {student[3] or 'N/A'}", styles['Normal']))
    elements.append(Paragraph(f"Current Address: {student[4] or 'N/A'}", styles['Normal']))
    elements.append(Paragraph(f"Email: {student[5] or 'N/A'}", styles['Normal']))
    elements.append(Paragraph(f"Hosteller: {'Yes' if student[6] == 'Y' else 'No'}", styles['Normal']))
    reg_date = student[7].strftime('%d/%m/%Y') if student[7] else 'N/A'
    elements.append(Paragraph(f"Dt. of Registration: {reg_date}", styles['Normal']))

    elements.append(Spacer(1, 24))

    # Course table header - match your sample columns exactly
    data = [["Sr. No.", "Course code", "Course Title", "Section", "Batch", "Slot", "Course", "Credits", "Co-ordinator"]]

    for i, course in enumerate(courses, 1):
        data.append([
            str(i),
            course[0] or '',
            course[1] or '',
            course[2] or '',
            course[3] or '',
            course[4] or '',
            course[5] or '',      # DC/DE
            str(course[6]) or '', # credits
            course[7] or ''       # faculty_name as Co-ordinator
        ])

    table = Table(data, colWidths=[40, 70, 160, 50, 50, 40, 50, 50, 120])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.black),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('BACKGROUND', (0,1), (-1,-1), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))

    elements.append(table)

    # Summary section (add this to match your PDF)
    elements.append(Spacer(1, 36))
    elements.append(Paragraph("Details regarding registered Courses for the Session :", styles['Normal']))
    # You can compute these dynamically later (DC count, DE count, total credits, theory/practical split)
    elements.append(Paragraph("DC : 11   DE : 12   Theory : 5   Practical : 2", styles['Normal']))
    elements.append(Paragraph("Total Credit registered : 23", styles['Normal']))
    elements.append(Paragraph("Total No. of courses registered in the session : 7", styles['Normal']))

    elements.append(Spacer(1, 48))
    elements.append(Paragraph("Signature of Student ___________________________   Date: ________", styles['Normal']))
    elements.append(Paragraph("Signature of Faculty Advisor ______________________   Date: ________", styles['Normal']))

    doc.build(elements)

    buffer.seek(0)
    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=registration_{student[1] or "student"}.pdf'
    return response