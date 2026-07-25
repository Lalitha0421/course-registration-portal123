# COMPLETE PROJECT KNOWLEDGE — PART 3

# DEPLOYMENT, EMAIL, PDF, JINJA2, AND DESIGN DECISIONS

---

## 12. DOCKER DEPLOYMENT — COMPLETE DETAILS

### 12.1 Dockerfile (Flask Container)
```dockerfile
FROM python:3.9-slim
ENV PYTHONDONTWRITEBYTECODE 1    # Don't create .pyc files
ENV PYTHONUNBUFFERED 1           # Print output immediately (important for logs)

# Install Oracle Instant Client dependencies
RUN apt-get update && apt-get install -y libaio1 wget unzip

# Download and install Oracle Instant Client 21.4
WORKDIR /opt/oracle
RUN wget https://download.oracle.com/.../instantclient-basic-linux.x64-21.4.0.0.0dbru.zip
RUN unzip ... && ldconfig

# Install Python dependencies
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

EXPOSE 7860
CMD ["python", "app.py"]
```

**Why python:3.9-slim?** Slim images are smaller (~150MB vs ~900MB for full). We only install what we need.

**Why Oracle Instant Client?** The oracledb library needs native Oracle libraries to connect to Oracle DB in "thick mode". In thin mode (default), it doesn't need these, but we include them for compatibility.

**Why PYTHONDONTWRITEBYTECODE=1?** Prevents Python from writing .pyc bytecode files inside the container, keeping it clean.

**Why PYTHONUNBUFFERED=1?** Forces Python to print output immediately instead of buffering. Critical for seeing logs in Docker.

### 12.2 docker-compose.yml (Multi-Container)
```yaml
version: '3.8'
services:
  db:
    image: gvenzl/oracle-xe:21-slim       # Pre-built Oracle XE image
    container_name: course_portal_db
    ports:
      - "1521:1521"                        # Oracle listener port
    environment:
      - ORACLE_PASSWORD=${DB_PASSWORD}     # SYS/SYSTEM password
      - APP_USER=${DB_USER}               # Application user (e.g., c##vnit_user)
      - APP_USER_PASSWORD=${DB_PASSWORD}   # App user password
    volumes:
      - oracle_data:/opt/oracle/oradata   # Persist DB data across restarts
      - ./sql:/docker-entrypoint-initdb.d # Auto-run schema.sql on first boot

  web:
    build: .                               # Build from Dockerfile
    container_name: course_portal_web
    ports:
      - "5000:5000"
    depends_on:
      - db                                 # Start Oracle before Flask
    environment:
      - DB_USER=${DB_USER}
      - DB_PASSWORD=${DB_PASSWORD}
      - DB_DSN=db:1521/XE                 # 'db' = Docker service name (internal DNS)
      - FLASK_SECRET=${FLASK_SECRET}
    restart: always                        # Auto-restart on crash

volumes:
  oracle_data:                             # Named volume for data persistence
```

**Why gvenzl/oracle-xe:21-slim?** Gerald Venzl (Oracle PM) maintains this lightweight Oracle XE Docker image. It's only ~2GB vs official Oracle images at ~8GB+.

**Why depends_on?** Ensures the Oracle container starts before Flask. Without it, Flask might try to connect before Oracle is ready.

**Why DB_DSN=db:1521/XE?** In Docker Compose, services can reach each other by service name. 'db' resolves to the Oracle container's IP on the internal Docker network. 1521 is Oracle's default listener port. XE is the database SID.

**Why volumes?** Docker containers are ephemeral. Without volumes, all Oracle data (tables, rows) would be lost when you restart. The named volume `oracle_data` persists data on the host filesystem.

**Why ./sql:/docker-entrypoint-initdb.d?** The Oracle XE image automatically runs any .sql files in this directory on first boot. Our schema.sql creates all 21 tables, sequences, constraints, and seed data automatically.

### 12.3 Deployment on Hugging Face Spaces
1. Create a Hugging Face Space with "Docker" SDK
2. Push the entire repo (Dockerfile, docker-compose.yml, code)
3. HF builds and runs the Docker containers
4. Exposes port 7860 publicly (configured in Dockerfile EXPOSE)
5. Public URL: `https://huggingface.co/spaces/username/course-portal`

**Why Hugging Face?** Free Docker Compose hosting. Most free platforms (Render, Railway) only support single containers. We need two (Flask + Oracle).

### 12.4 How to Run Locally
```bash
# Option 1: With Docker Compose (full Oracle)
docker-compose up --build

# Option 2: Without Docker (SQLite fallback)
pip install -r requirements.txt
python create_demo_db.py    # Creates SQLite demo database
python app.py               # Runs on http://localhost:5000
```

---

## 13. EMAIL NOTIFICATION SYSTEM

### 13.1 Architecture
File: `utils/email_utils.py`

The system has a dual-mode email system:
- **Real mode:** Uses Gmail SMTP with App Password (for production)
- **Simulation mode:** Prints email content to terminal (for development)

```python
def send_email(to_email, subject, body):
    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("SENDER_PASSWORD")
    
    if not sender_email or not sender_password:
        # SIMULATION: Print to terminal
        print(f"[EMAIL SIMULATION] TO: {to_email} SUBJECT: {subject}")
        return True
    
    # REAL: Use Gmail SMTP
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()          # Enable TLS encryption
        server.login(sender_email, sender_password)
        server.send_message(message)
```

**Why TLS?** Without TLS, email credentials are sent in plaintext. STARTTLS upgrades the connection to encrypted.

**Why App Password?** Google blocks less secure apps from using regular passwords. App Passwords are 16-char codes generated in Google Account settings specifically for third-party apps.

### 13.2 Two Email Functions
1. `notify_student_approval(name, email, enrollment_no, password)` — Sent when admin approves a student. Contains login credentials.
2. `notify_registration_approval(name, email, academic_session)` — Sent when admin approves course registration.

---

## 14. PDF GENERATION — ReportLab

### 14.1 How It Works
File: `routes/student_routes.py` (lines 768-922)

The PDF registration slip is generated on-the-fly (not stored on disk):

```python
buffer = BytesIO()                                    # In-memory file
doc = SimpleDocTemplate(buffer, pagesize=letter)      # A4-like page
elements = []

# 1. Logo
logo = Image("static/vnit_logo.jpeg", width=80, height=80)
elements.append(logo)

# 2. Headers
elements.append(Paragraph("Visvesvaraya National Institute of Technology", styles['Heading2']))

# 3. Student details (8 lines)
elements.append(Paragraph(f"Name: {name}", styles['Normal']))

# 4. Course table (9 columns)
table_data = [["Sr.", "Code", "Title", "Section", "Batch", "Slot", "Type", "Credits", "Coordinator"]]
for i, row in enumerate(courses, 1):
    table_data.append([str(i), row[0], row[1], ...])

table = Table(table_data, colWidths=[30, 60, 140, 45, 45, 45, 45, 45, 110])
table.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), colors.orange),   # Header row orange
    ('GRID', (0,0), (-1,-1), 1, colors.black),      # All cells have borders
]))

# 5. Dynamic totals
dc_count = sum(1 for r in courses if r[5] == 'DC')
total_credits = sum(r[6] for r in courses)

# 6. Signatures
# 7. Build and return
doc.build(elements)
buffer.seek(0)

response = make_response(buffer.getvalue())
response.headers['Content-Type'] = 'application/pdf'
response.headers['Content-Disposition'] = 'attachment; filename=registration_VNIT2025101.pdf'
```

**Why BytesIO?** Generates PDF in memory, not on disk. Cleaner — no temp files to manage or clean up. The buffer is sent directly as the HTTP response.

**Why on-the-fly?** PDF always reflects the latest data from the database. No stale cached PDFs.

---

## 15. JINJA2 TEMPLATING

### 15.1 Template Inheritance
All 28 pages extend a base template:
```html
<!-- base.html -->
<html>
  <head>...</head>
  <body>
    <nav>...</nav>
    {% block content %}{% endblock %}
  </body>
</html>

<!-- student_dashboard.html -->
{% extends 'base.html' %}
{% block content %}
  <h1>Welcome, {{ name }}</h1>
{% endblock %}
```

### 15.2 Key Jinja2 Features Used
- `{{ variable }}` — Output (auto-escaped for XSS prevention)
- `{% for course in courses %}...{% endfor %}` — Loops
- `{% if session.role == 'admin' %}...{% endif %}` — Conditionals
- `{% extends 'base.html' %}` — Template inheritance
- `{{ url_for('student.dashboard') }}` — URL generation
- `{% with messages = get_flashed_messages() %}` — Flash messages

---

## 16. KEY DESIGN DECISIONS AND WHY

### 16.1 Why Oracle MERGE over SELECT-then-INSERT/UPDATE?
**Problem:** Two faculty members submit attendance for the same student at the same time. With SELECT-then-INSERT:
1. Thread A: SELECT (no row found) -> decides to INSERT
2. Thread B: SELECT (no row found) -> decides to INSERT
3. Thread A: INSERT (success)
4. Thread B: INSERT (duplicate key error or duplicate row)

**MERGE solves this:** It's atomic — the database handles the check-and-insert/update in one operation. No race condition possible.

### 16.2 Why LISTAGG for course listings?
**Problem:** One course (CSL312) might have 3 faculty members across sections. Without LISTAGG, you'd get 3 rows. With LISTAGG:
```sql
LISTAGG(f.faculty_name, ', ') WITHIN GROUP (ORDER BY f.faculty_name)
-- Result: "Dr. A, Dr. B, Dr. C" in ONE row
```
This simplifies the frontend — one row per course, not one row per section.

### 16.3 Why Header-Detail pattern for registrations?
`student_registration` (header) + `student_registration_courses` (detail)

**Alternative:** One table with (student_id, session, course1, course2, ..., course10). Why bad? Fixed columns. What if a student takes 11 courses? What about variable course counts?

**Our approach:** One header row per registration, N detail rows for N courses. Standard relational modeling. Supports any number of courses.

### 16.4 Why DELETE-then-INSERT for syllabus updates?
When faculty updates course objectives, we DELETE all existing ones and INSERT new ones. Why not UPDATE?

Because the number of objectives can change (3 objectives might become 5). With UPDATE, you'd need to handle: update existing, insert new, delete removed. The DELETE-then-INSERT pattern is simpler and correct — the print_seq ensures ordering.

### 16.5 Why Session-Based Auth over JWT?
- Server-rendered pages (Jinja2) naturally work with cookies/sessions
- No separate frontend (no React/Vue that would need JWT)
- Simpler implementation — Flask session works out of the box
- Session data is server-side — client only has a signed cookie

---

## 17. NORMALIZATION IN OUR SCHEMA

### 1NF (First Normal Form)
Every column has atomic values. We don't store "CSL312,CSL313" in one field — each course registration is a separate row in student_registration_courses.

### 2NF (Second Normal Form)
No partial dependencies. In student_registration_courses, the PK is 'id'. reg_id and course_instance_id are both FKs, not part of a composite key. All non-key attributes depend on the full PK.

### 3NF (Third Normal Form)
No transitive dependencies. Student's department/program info is in students table. Faculty's department is in faculty table. Course details are in course_master, not duplicated in course_instance.

**Example:** course_instance does NOT contain course_title — it has course_id FK pointing to course_master where the title lives. This means if a course title changes, you update ONE row in course_master, not hundreds in course_instance.

---

## 18. ERROR HANDLING PATTERN

Every route follows this pattern:
```python
conn = None
cursor = None
try:
    conn = get_connection()
    cursor = conn.cursor()
    # ... business logic ...
    conn.commit()
except Exception as e:
    if conn: conn.rollback()    # Undo partial changes
    flash(f"Error: {str(e)}", "danger")
finally:
    if cursor: cursor.close()   # Always close cursor
    if conn: conn.close()       # Always close connection
```

**Why try-except-finally?** Database connections are limited resources. If an error occurs mid-transaction:
- `rollback()` ensures data consistency (no half-completed operations)
- `finally` ensures cursor and connection are ALWAYS closed, even if an exception occurs
- Without this, connection leaks would eventually exhaust the connection pool

---

## 19. SCALABILITY IMPROVEMENTS (If Asked)

| Current | Improvement | Why |
|---|---|---|
| Single Flask process | Multiple workers behind Nginx | Handle concurrent users |
| Server-side sessions | Redis sessions | Share sessions across workers |
| New connection per request | Connection pooling (oracledb.SessionPool) | Reuse connections, faster response |
| Synchronous email | Celery + Redis background tasks | Don't block HTTP response for SMTP |
| No caching | Redis cache for course lists | Reduce DB load for read-heavy data |
| Monolithic Flask | REST API + React frontend | Better separation, mobile app support |
| SQLite fallback | Oracle Autonomous DB | Auto-scaling, managed backups |

---

## 20. COMPLETE LIST OF ALL 28 TEMPLATES

| Template | Role | Purpose |
|---|---|---|
| login.html | All | Login page with role selector |
| student_application.html | Public | New student registration form |
| admin_dashboard.html | Admin | Main admin control panel |
| student_dashboard.html | Student | Student home with CGPA, courses, attendance |
| faculty_dashboard.html | Faculty | Assigned courses, advised students |
| add_course.html | Admin | Form to add new course |
| edit_course.html | Admin | Edit course details, evaluation weights |
| pending_students.html | Admin | List of pending student applications |
| view_students.html | Admin | All students with status |
| manage_faculty.html | Admin | Faculty CRUD list |
| edit_faculty.html | Admin | Edit faculty details |
| admin_settings.html | Admin | System configuration editor |
| admin_analytics.html | Admin | Charts and statistics |
| admin_student_registrations.html | Admin | Registration approval queue |
| register_courses.html | Student | Course selection with DC/DE/backlog |
| view_registered.html | Student | View/edit registered courses |
| course_details.html | Student | Full course info (objectives, outcomes, syllabus, books) |
| course_list.html | Student | Browse available courses |
| student_profile.html | Student | Edit profile and password |
| student_daily_attendance.html | Student | View attendance records per course |
| examination.html | Student | View results by semester, backlogs |
| view_results.html | Admin | All student results with CGPA |
| attendance.html | Faculty | Basic attendance view |
| attendance_grid.html | Faculty | Monthly calendar attendance grid |
| enter_grades.html | Faculty | Grade entry form per course |
| manage_syllabus.html | Faculty | Edit objectives, outcomes, topics |
| copo_mapping.html | Admin | CO-PO mapping matrix editor |
| coordinated_student_details.html | Faculty | Advised student's full details |

---

*Continued in PART 4 (Interview Q&A)...*
