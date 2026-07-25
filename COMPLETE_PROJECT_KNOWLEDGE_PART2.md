# COMPLETE PROJECT KNOWLEDGE — PART 2

# ROUTES, WORKFLOWS, SQL FUNCTIONS, AND SECURITY

---

## 7. APPLICATION ENTRY POINT — app.py

```python
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET', 'super-secret-key-fallback')

app.register_blueprint(auth_bp)                          # /login, /logout, /student_application
app.register_blueprint(student_bp, url_prefix='/student') # /student/dashboard, /student/register_courses
app.register_blueprint(admin_bp, url_prefix='/admin')     # /admin/dashboard, /admin/add_course
app.register_blueprint(course_bp, url_prefix='/course')   # /course/list, /course/details
app.register_blueprint(faculty_bp)                        # /faculty/dashboard, /faculty/attendance
```

**Why Blueprints?** Flask Blueprints are like mini-applications. Each role (student, faculty, admin) has its own blueprint with its own routes. This keeps code organized — admin_routes.py has 829 lines, student_routes.py has 922 lines. Without blueprints, app.py would be 2500+ lines.

**Why url_prefix?** Student routes are prefixed with `/student/`, admin with `/admin/`. This means `/student/dashboard` and `/admin/dashboard` are separate routes even though both end in `/dashboard`. It also makes RBAC cleaner — you can tell from the URL which role the page is for.

---

## 8. DATABASE CONNECTION — config.py

```python
def get_connection():
    db_type = os.getenv("DB_TYPE", "ORACLE").upper()
    if db_type == "ORACLE":
        connection = oracledb.connect(user=user, password=password, dsn=dsn, retry_count=5)
        return connection
    else:
        return get_sqlite_connection()
```

**Dual-database strategy:** The system tries Oracle first. If Oracle credentials are missing or connection fails, it falls back to SQLite. This means:
- **Development:** Works anywhere without Oracle installed (uses SQLite)
- **Production:** Uses Oracle for full enterprise features
- **Demo (Hugging Face):** Uses Docker Compose with Oracle XE

**oracledb thin mode:** The `oracledb` library can connect to Oracle in "thin mode" — pure Python, no Oracle Client installation needed. This simplifies deployment.

**retry_count=5:** If the Oracle connection fails (e.g., network hiccup), it retries up to 5 times before failing.

---

## 9. ALL ROUTES AND WORKFLOWS

### 9.1 AUTH ROUTES (auth_routes.py — 189 lines)

**POST /login** — Login flow:
1. Receives login_id, password, role from form
2. Queries `users` table: `SELECT user_id, password_hash, role FROM users WHERE login_id = :1 AND role = :2`
3. Verifies password using `check_password_hash(stored_hash, entered_password)`
4. On success: stores user_id, role, login_id in Flask session
5. If student: also fetches and stores student_id, name from students table
6. If faculty: also fetches and stores faculty_id, name from faculty table
7. Redirects to role-specific dashboard

**POST /student_application** — New student registration:
1. Collects name, email, mobile, program, aadhar, dob, address, is_hosteller
2. Checks duplicate email: `SELECT 1 FROM students WHERE email = :1`
3. Inserts into students with status='PENDING' using STUDENTS_SEQ.NEXTVAL
4. Student has NO login credentials yet — these are created by admin on approval

**GET /logout** — Clears Flask session, redirects to login

### 9.2 ADMIN ROUTES (admin_routes.py — 829 lines)

**GET /admin/dashboard** — Admin dashboard page

**POST /admin/add_course** — Add new course:
1. Validates course_code uniqueness
2. Generates course_id: `SELECT NVL(MAX(course_id), 0) + 1 FROM course_master`
3. Inserts into course_master
4. Creates course_instance with academic session and semester

**POST /admin/add_faculty** — Add new faculty:
1. Creates user record: `USERS_SEQ.NEXTVAL` for user_id
2. Login ID = email prefix (before @)
3. Temporary password = "faculty123", hashed with PBKDF2
4. Creates faculty record: `FACULTY_SEQ.NEXTVAL` for faculty_id
5. Links user and faculty: `UPDATE users SET faculty_id = :1 WHERE user_id = :2`

**GET /admin/approve_student/<sid>** — Approve pending student:
1. Generates enrollment_no: `VNIT{year}{student_id}` (e.g., VNIT2025101)
2. Creates temporary password "VNIT@123", hashes it
3. Creates user login: INSERT into users with role='student'
4. Updates student: SET status='APPROVED', enrollment_no, user_id
5. Sends email notification via `notify_student_approval()`
6. All 4 operations in one transaction — COMMIT at end, ROLLBACK on any failure

**POST /admin/edit_course/<course_id>** — Update course details:
1. Updates course_master (title, credits, type)
2. Deletes and re-inserts evaluation_details (full replacement pattern)

**POST /admin/update_outcomes/<course_id>** — Update course outcomes:
1. DELETE all existing outcomes for course
2. INSERT new outcomes with sequential print_seq

**POST /admin/copo_mapping/<course_id>** — CO-PO mapping matrix:
Uses Oracle MERGE for upsert:
```sql
MERGE INTO co_po_mapping m
USING (SELECT :co_id as co_id, :po_id as po_id FROM dual) src
ON (m.course_outcome_id = src.co_id AND m.program_outcome_id = src.po_id)
WHEN MATCHED THEN UPDATE SET m.weightage = :weight
WHEN NOT MATCHED THEN INSERT (...) VALUES (...)
```

**GET /admin/view_results** — CGPA calculation using CTE:
```sql
WITH grade_points AS (
    SELECT student_id, course_id, grade,
           CASE grade 
               WHEN 'AA' THEN 10 WHEN 'AB' THEN 9 WHEN 'BB' THEN 8 
               WHEN 'BC' THEN 7 WHEN 'CC' THEN 6 WHEN 'CD' THEN 5 
               WHEN 'DD' THEN 4 ELSE 0 END as points
    FROM results
)
SELECT s.enrollment_no, s.name,
       ROUND(SUM(gp.points * cm.credits) / NULLIF(SUM(cm.credits), 0), 2) as cgpa
FROM students s
LEFT JOIN grade_points gp ON s.student_id = gp.student_id
LEFT JOIN course_master cm ON gp.course_id = cm.course_id
GROUP BY s.enrollment_no, s.name
```

**GET /admin/analytics** — Dashboard analytics:
- Registration status breakdown: `GROUP BY status`
- Grade distribution: `GROUP BY grade` with CASE-based ordering
- Department stats: `GROUP BY program`

**GET /admin/export_students** — Excel export using pandas:
```python
df = pd.read_sql(query, conn)
output = io.BytesIO()
with pd.ExcelWriter(output, engine='openpyxl') as writer:
    df.to_excel(writer, index=False, sheet_name='Registered Students')
```

**GET /admin/approve_registration/<reg_id>** — Approve course registration:
1. Updates student_registration status to 'APPROVED'
2. Fetches student details via JOIN
3. Sends email via `notify_registration_approval()`

**POST /admin/settings** — Update system config:
```sql
UPDATE system_config SET config_value = :1 WHERE config_key = :2
```

### 9.3 STUDENT ROUTES (student_routes.py — 922 lines)

**GET /student/dashboard** — Student dashboard:
1. Fetches student profile (program, enrollment_no)
2. Calculates CGPA using subquery with CASE for grade-to-point conversion
3. Fetches last registration status using `FETCH FIRST 1 ROWS ONLY`
4. If registration APPROVED, fetches active courses with real-time attendance percentage
5. Attendance calculated via correlated subquery:
```sql
SELECT ROUND(
    (COUNT(CASE WHEN da.status = 'PRESENT' THEN 1 END) * 100.0) / NULLIF(COUNT(*), 0), 2
) FROM daily_attendance da WHERE da.student_id = :sid AND da.course_instance_id = ci.instance_id
```

**POST /student/register_courses** — Course registration:
1. Checks if registration is OPEN via system_config
2. Fetches backlogs: courses where student got 'FF' or 'W' grade and hasn't cleared yet
3. Fetches DC courses using LISTAGG for aggregating faculty/section/slot:
```sql
LISTAGG(NVL(f.faculty_name, 'N/A'), ', ') WITHIN GROUP (ORDER BY f.faculty_name)
```
4. Fetches DE courses similarly
5. On POST: Uses MERGE to create/update student_registration header
6. Clears old registration_courses, inserts new selections
7. Validates: exactly 2 DE courses required

**GET /student/course_details/<code>** — Full course info:
Fetches from 8 tables: course_master, course_prerequisites, course_objectives, course_outcomes, course_description, text_books, reference_books, evaluation_details, co_po_mapping

**GET /student/generate_registration_pdf/<session>** — PDF generation:
Uses ReportLab to build PDF with:
- VNIT logo, institution header
- Student personal details (8 fields)
- Course table with 9 columns
- Dynamic totals (DC count, DE count, theory, practical, total credits)
- Signature lines
- Print timestamp

**POST /student/examination** — View results by semester:
- Fetches session history for dropdown
- Separates results into cleared (grade not FF/W) and backlogs (grade FF/W)
- Shows total cleared credits

**POST /student/profile** — Update profile:
- Updates email, mobile, address in students table
- Optionally updates password in users table (minimum 6 chars)

### 9.4 FACULTY ROUTES (faculty_routes.py — 369 lines)

**GET /faculty/dashboard** — Faculty dashboard:
- Lists assigned courses with enrolled student count and average attendance
- Lists coordinated (advised) students with semester info via subquery

**GET/POST /faculty/attendance/<course_id>** — Monthly attendance grid:
- Renders calendar grid: rows=students, columns=days of month
- Uses Python `calendar.monthrange(year, month)` for days
- On POST: loops through every student x day combination
- Uses Oracle MERGE for each attendance record:
```sql
MERGE INTO daily_attendance da
USING (SELECT :sid AS student_id, :cid AS course_instance_id, TO_DATE(:dt, 'YYYY-MM-DD') AS att_date FROM dual) src
ON (da.student_id = src.student_id AND da.course_instance_id = src.course_instance_id AND da.attendance_date = src.att_date)
WHEN MATCHED THEN UPDATE SET da.status = :status
WHEN NOT MATCHED THEN INSERT (...) VALUES (...)
```
- Fetches existing attendance using EXTRACT(DAY FROM attendance_date) for grid pre-population

**GET/POST /faculty/grading/<instance_id>** — Enter student grades:
- Lists enrolled students with existing grades
- On POST: Uses MERGE into results table for upsert
- Supports letter grades: AA(10), AB(9), BB(8), BC(7), CC(6), CD(5), DD(4), FF(0)

**GET /faculty/manage-syllabus/<course_id>** — View/edit syllabus:
- Fetches objectives, outcomes, and syllabus topics
- Verifies faculty authorization: `SELECT 1 FROM course_instance WHERE faculty_id = :fid AND course_id = :cid`

**POST /faculty/update-syllabus/<course_id>** — Update syllabus:
- Handles three types: objectives, outcomes, syllabus
- Delete-and-reinsert pattern for each type

---

## 10. ORACLE SQL FUNCTIONS AND FEATURES USED

| SQL Feature | Where Used | Why |
|---|---|---|
| **MERGE (Upsert)** | Attendance, CO-PO mapping, Registration, Grading | Single atomic INSERT-or-UPDATE. Eliminates race conditions. One DB round-trip |
| **LISTAGG** | Course listing | Aggregates multiple faculty names/sections into one comma-separated string |
| **NVL** | Throughout | Oracle's COALESCE for 2 args. Replaces NULL with default value |
| **CASE WHEN** | CGPA calc, Grade distribution, Attendance % | Conditional logic inside SQL. Maps grades to points |
| **FETCH FIRST N ROWS ONLY** | Latest registration | Oracle 12c+ row-limiting clause. Alternative to ROWNUM |
| **WITH (CTE)** | CGPA calculation | Common Table Expression for readable complex queries |
| **EXTRACT** | Attendance grid | Extracts DAY/MONTH/YEAR from DATE column |
| **TO_DATE** | Attendance INSERT | Converts string to Oracle DATE type |
| **GROUP BY + aggregate** | Analytics, CGPA | COUNT, SUM, ROUND, NULLIF for safe division |
| **Correlated Subquery** | Dashboard courses | Calculates attendance % per course inline |
| **Sequences (NEXTVAL)** | User/Student/Faculty creation | Thread-safe unique ID generation |
| **CHECK constraints** | users.role, students.status | Database-level data validation |
| **ON DELETE CASCADE** | CO-PO, Evaluation | Automatically deletes child rows when parent is deleted |
| **SYSDATE** | Default timestamps | Oracle's current timestamp function |

---

## 11. SECURITY IMPLEMENTATION

### 11.1 Password Hashing
```python
from werkzeug.security import generate_password_hash, check_password_hash
hashed = generate_password_hash(plain_password)  # PBKDF2-HMAC-SHA256 + random salt
check_password_hash(stored_hash, entered_password)  # Returns True/False
```
**Why PBKDF2 over MD5/SHA256?** PBKDF2 applies the hash 260,000+ times (iterations), making brute-force attacks computationally expensive. MD5/SHA256 are designed to be fast — an attacker can try billions per second.

### 11.2 SQL Injection Prevention
All queries use parameterized binding:
```python
cursor.execute("SELECT * FROM students WHERE email = :1", (email,))  # SAFE
# NEVER: cursor.execute(f"SELECT * FROM students WHERE email = '{email}'")  # VULNERABLE
```

### 11.3 Session-Based Authentication
```python
session["user_id"] = user[0]
session["role"] = user[2]
# Flask signs the session cookie with SECRET_KEY — tamper-proof
```

### 11.4 Role-Based Access Control (RBAC)
Every route checks:
```python
if session.get('role') != 'admin':
    flash('Access denied', 'danger')
    return redirect(url_for('auth.login_page'))
```

### 11.5 XSS Prevention
Jinja2 auto-escapes all `{{ variable }}` output by default. User input rendered in HTML is HTML-encoded.

### 11.6 CSRF Protection
Flask-WTF provides CSRF token validation on form submissions.

---

*Continued in PART 3...*
