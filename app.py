from flask import Flask, render_template, redirect, url_for, request, session, flash
from routes.auth_routes import auth_bp
from routes.student_routes import student_bp
# Add these if you have them (or create empty files later)
from routes.admin_routes import admin_bp
from routes.course_routes import course_bp
# from routes.faculty_routes import faculty_bp   # optional

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-12345'  # must have for sessions/flash

# Register all blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(student_bp, url_prefix='/student')   # ← this was missing!
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(course_bp, url_prefix='/course')     # for course_details

# Optional: faculty if you have it
# app.register_blueprint(faculty_bp, url_prefix='/faculty')

if __name__ == '__main__':
    app.run(debug=True)