with open('routes/student_routes.py', 'a') as f:
    f.write("""

# ────────────────────────────────────────────────
# PPT GENERATION
# ────────────────────────────────────────────────
@student_bp.route("/generate_ppt/<session_name>")
def generate_ppt(session_name):
    if "student_id" not in session:
        return redirect(url_for("auth.login_page"))
    student_id = session.get("student_id")
    try:
        from utils.ppt_gen import generate_registration_ppt
        ppt_stream = generate_registration_ppt(student_id, session_name)
        filename = f"Registration_{student_id}_{session_name.replace(' ', '_')}.pptx"
        response = make_response(ppt_stream.getvalue())
        response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    except Exception as e:
        print(f"PPT ERROR: {str(e)}")
        flash(f"Failed to generate PPT: {str(e)}", "danger")
        return redirect(url_for("student.student_dashboard"))
""")
