import os
from flask import Flask, redirect, url_for
from dotenv import load_dotenv
from routes.auth_routes import auth_bp
from routes.student_routes import student_bp
from routes.admin_routes import admin_bp
from routes.course_routes import course_bp
from routes.faculty_routes import faculty_bp

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET', 'super-secret-key-fallback')

app.register_blueprint(auth_bp)
app.register_blueprint(student_bp, url_prefix='/student')
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(course_bp, url_prefix='/course')
app.register_blueprint(faculty_bp)
@app.route('/')
def index():
    return redirect(url_for('auth.login_page'))  # or '/login' if you have it

@app.route('/er_diagram')
def er_diagram():
    import os
    diagram_path = os.path.join(os.path.dirname(__file__), 'er_diagram.html')
    with open(diagram_path, 'r', encoding='utf-8') as f:
        content = f.read()
    from flask import Response
    return Response(content, mimetype='text/html')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)