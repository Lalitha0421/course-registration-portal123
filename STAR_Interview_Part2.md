# STAR Interview Preparation — Course Registration Portal
## Part 2: Technical Details, Challenges, Solutions & Results

---

## TECHNICAL DETAILS

### Architecture Overview

```
Browser (HTML/CSS/JS)
        ↓ HTTP Request
Flask App (app.py)
        ↓ Blueprint routing
Routes Layer (auth/student/admin/faculty routes)
        ↓ SQL via oracledb
Oracle XE Database (21 tables)
        ↓ Fallback
SQLite (demo_database.db)
```

### Frontend
- **Language:** HTML5 + Vanilla CSS + JavaScript
- **Templating:** Jinja2 (Flask's default engine)
- **Template Inheritance:** All 28 pages extend a base template using `{% extends 'base.html' %}`
- **Why Jinja2 over React/Vue?** Server-rendered pages don't need a separate API layer. Flask renders HTML on the server and sends it. Simpler, fewer moving parts.

### Backend
- **Framework:** Flask (Python micro-framework)
- **Why Flask over Django?** Django's ORM generates SQL automatically — it does NOT support Oracle MERGE, LISTAGG, or analytical functions natively. Flask lets us write raw SQL via `oracledb`, giving full control over Oracle-specific features.
- **Why Flask over FastAPI?** Server-rendered HTML pages don't need a REST API. FastAPI is designed for JSON APIs. Flask's `render_template` is the right tool here.
- **Blueprint Architecture:** Each role has its own blueprint
  - `auth_routes.py` — 189 lines — login, logout, student application
  - `admin_routes.py` — 829 lines — all admin functions
  - `student_routes.py` — 922 lines — registration, attendance, PDF, results
  - `faculty_routes.py` — 369 lines — attendance grid, grading, syllabus
  - `course_routes.py` — course catalog views

### Database
- **Primary:** Oracle XE / Oracle Autonomous DB
- **Fallback:** SQLite (for demo without Oracle)
- **Driver:** `oracledb` (Oracle's official thin-mode Python driver — no Oracle Client installation required)
- **Why Oracle over PostgreSQL/MySQL?**
  - MERGE statement (atomic upsert) — PostgreSQL has INSERT ON CONFLICT but with different syntax
  - LISTAGG function — no direct equivalent in MySQL
  - Sequences (NEXTVAL) — fine-grained ID control across tables in one transaction
  - Enterprise learning goal — Oracle is used in most large institutions and enterprises
  - FETCH FIRST N ROWS ONLY, EXTRACT, NVL, analytical functions — richer SQL toolkit

---

### All 21 Tables — Complete Reference

| Table | Purpose | Key Columns |
|---|---|---|
| `SYSTEM_CONFIG` | Portal settings (session, registration open/closed) | config_key PK, config_value |
| `USERS` | Authentication for all 3 roles | user_id, login_id UNIQUE, password_hash, role CHECK |
| `STUDENTS` | Student profile + application | student_id IDENTITY PK, enrollment_no UNIQUE, status CHECK |
| `FACULTY` | Faculty profile | faculty_id PK via FACULTY_SEQ, department |
| `COURSE_MASTER` | Course catalog (permanent definitions) | course_id, course_code UNIQUE, L/T/P/credits |
| `COURSE_INSTANCE` | Course offering per semester+session+faculty | instance_id, course_id FK, faculty_id FK, academic_session |
| `COURSE_PREREQUISITES` | Self-referencing FK: course needs another course | course_id FK, prerequisite_course_id FK |
| `COURSE_OBJECTIVES` | Learning objectives per course | obj_id, course_id FK, description, print_seq |
| `COURSE_OUTCOMES` | Course outcomes (COs) for OBE | outcome_id, course_id FK, outcome_desc, print_seq |
| `COURSE_DESCRIPTION` | Syllabus topics with weekly duration | desc_id, course_id FK, topic, duration_weeks |
| `TEXT_BOOKS` | Textbooks per course | book_id, course_id FK, title, type |
| `REFERENCE_BOOKS` | Reference materials per course | book_id, course_id FK, title, type |
| `STUDENT_REGISTRATION` | Header — one row per student per session | reg_id IDENTITY PK, student_id FK, academic_session, status CHECK |
| `STUDENT_REGISTRATION_COURSES` | Detail — one row per course per registration | id, reg_id FK, course_instance_id FK, course_type |
| `RESULTS` | Grades per student per course per session | result_id, student_id FK, course_id FK, grade, grade_letter |
| `ATTENDANCE` | Aggregate attendance % (summary) | attendance_id, student_id FK, course_instance_id FK, attendance_percentage |
| `DAILY_ATTENDANCE` | Day-by-day attendance records | student_id FK, course_instance_id FK, attendance_date, status |
| `COORDINATOR` | Faculty-student advisory mapping | faculty_id FK, student_id FK, academic_session |
| `PROGRAM_OUTCOMES` | Institution-level program outcomes (POs) | po_id PK, po_code UNIQUE, po_description |
| `CO_PO_MAPPING` | Junction: Course Outcome → Program Outcome | course_outcome_id FK, program_outcome_id FK, weightage 0-3 |
| `EVALUATION_DETAILS` | Assessment weights per course | eval_id, course_id FK ON DELETE CASCADE, eval_type, weightage |

---

### Normalization — How It's Achieved

**1NF (First Normal Form) — Atomic Values**
- We never store multiple courses as `"CSL312, CSL313"` in one column
- Each course registration is a separate row in `STUDENT_REGISTRATION_COURSES`
- Each attendance record is a separate row in `DAILY_ATTENDANCE`

**2NF (Second Normal Form) — No Partial Dependencies**
- `STUDENT_REGISTRATION_COURSES` has PK = `id` (surrogate). All non-key columns (`reg_id`, `course_instance_id`, `course_type`) depend on the full PK.
- No partial dependencies since we avoid composite PKs where possible.

**3NF (Third Normal Form) — No Transitive Dependencies**
- `COURSE_INSTANCE` does NOT store `course_title` — it stores `course_id` FK pointing to `COURSE_MASTER`
- If a course title changes, ONE row in `COURSE_MASTER` is updated, not hundreds of `COURSE_INSTANCE` rows
- `STUDENT_REGISTRATION` does NOT store student's program — it stores `student_id` FK
- Faculty department is in `FACULTY` table, not duplicated in `COURSE_INSTANCE`

**Why course_master + course_instance separation?**
- A course "DBMS (CSL312)" is a permanent entity in the catalog
- But it's offered differently each semester: W25 by Dr. A in Section A, M25 by Dr. B in Section B
- `COURSE_MASTER` = what the course is; `COURSE_INSTANCE` = when/who/where it's offered
- This is the standard **master-detail design pattern**

**Why student_registration + student_registration_courses (Header-Detail)?**
- Alternative (bad): one row with columns course1, course2, ..., course10 — what if student takes 11?
- Our approach: one header row per registration, N detail rows for N courses — fully flexible

---

### DBMS Principles Applied

**1. Data Integrity — Constraints**
- `CHECK` on `users.role` — only `'student'`, `'faculty'`, `'admin'` allowed
- `CHECK` on `students.status` — only `'PENDING'`, `'APPROVED'`, `'REJECTED'`
- `CHECK` on `student_registration.status` — only `'SUBMITTED'`, `'APPROVED'`, `'REJECTED'`
- `UNIQUE` on `users.login_id` — no two users with same login
- `UNIQUE` on `students.enrollment_no` — no duplicate enrollment numbers
- `NOT NULL` on all critical FK columns

**2. Referential Integrity — Foreign Keys**
- `STUDENTS.user_id → USERS.user_id`
- `COURSE_INSTANCE.course_id → COURSE_MASTER.course_id`
- `COURSE_INSTANCE.faculty_id → FACULTY.faculty_id`
- `STUDENT_REGISTRATION.student_id → STUDENTS.student_id`
- `STUDENT_REGISTRATION_COURSES.reg_id → STUDENT_REGISTRATION.reg_id`
- `CO_PO_MAPPING → COURSE_OUTCOMES ON DELETE CASCADE`
- `EVALUATION_DETAILS → COURSE_MASTER ON DELETE CASCADE`

**3. Atomicity — Transactions**
- Student approval: 4 SQL operations (generate enrollment, hash password, INSERT user, UPDATE student) in ONE transaction. COMMIT only if all succeed; ROLLBACK if any fail.
- Every route follows `try → conn.commit() / except → conn.rollback() / finally → conn.close()`

**4. Concurrency Control — Oracle MERGE**
- MERGE is atomic at the DB level — handles INSERT-or-UPDATE without race conditions
- Used in 4 places: attendance, CO-PO mapping, registration header, grading
- Oracle uses row-level locking for concurrent MERGE on same row

**5. Sequence-Based ID Generation**
- `USERS_SEQ.NEXTVAL` — thread-safe unique user_id generation
- `STUDENTS_SEQ.NEXTVAL` — unique student_id
- `FACULTY_SEQ.NEXTVAL` — unique faculty_id
- Why sequences? You can call `SELECT USERS_SEQ.NEXTVAL FROM dual` BEFORE the INSERT, use the same ID to link user and student in the same transaction

**6. Security**
- **SQL Injection Prevention:** All queries use parameterized binding (`:1`, `:name` named params). Never f-string SQL.
- **Password Hashing:** Werkzeug PBKDF2-HMAC-SHA256 with automatic salt. 260,000+ iterations makes brute force impractical.
- **Session Security:** Flask signs cookies with SECRET_KEY using HMAC-SHA1. Tamper-proof.
- **RBAC:** Every route checks `session.get('role')`. Wrong role → redirect to login.
- **XSS Prevention:** Jinja2 auto-escapes all `{{ variable }}` output.

---

### Key SQL Features Used — Why Each One

| Feature | Where Used | Why Not Alternative |
|---|---|---|
| `MERGE` | Attendance, grades, registration | Atomic upsert. SELECT-then-INSERT/UPDATE has race conditions. |
| `LISTAGG` | Course listing | Aggregates 3 faculty into "Dr. A, Dr. B, Dr. C" in ONE row. Without it: 3 duplicate rows per course. |
| `CTE (WITH clause)` | CGPA calculation | Readable complex query. Avoids repeating subquery 3 times. |
| `NULLIF` | Attendance %, CGPA | Prevents division by zero safely. `SUM(credits)` could be 0 for new students. |
| `CASE WHEN` | Grade-to-points mapping | In-SQL conditional logic. Maps 'AA'→10, 'AB'→9 etc. |
| `FETCH FIRST 1 ROWS ONLY` | Last registration | Oracle 12c+ row limiter. Cleaner than ROWNUM. |
| `EXTRACT(DAY FROM date)` | Attendance grid pre-fill | Pulls day number from DATE for grid column mapping. |
| `NVL` | Throughout | Oracle's 2-arg COALESCE. Replaces NULL with default. |
| `NOT EXISTS` | Backlog query | Anti-join — finds failed courses not subsequently cleared. |
| `LEFT JOIN` | Dashboard courses | Students with no attendance still appear (null → 0%). |
| `GROUP BY + LISTAGG` | Course listing | One row per course even with multiple sections. |

---

### Every File — What It Does

| File | Lines | What It Implements |
|---|---|---|
| `app.py` | 35 | Creates Flask app, registers 5 blueprints, defines ER diagram route, sets secret key from env |
| `config.py` | 70 | `get_connection()` — tries Oracle first, falls back to SQLite. `OracleCompatibleCursor` converts `:name` params to `?` for SQLite. |
| `.env` | — | `DB_USER`, `DB_PASSWORD`, `DB_DSN`, `FLASK_SECRET`, `SENDER_EMAIL`, `SENDER_PASSWORD` — never hardcoded |
| `requirements.txt` | — | All pinned dependencies: flask, oracledb, werkzeug, reportlab, pandas, openpyxl, python-dotenv |
| `Dockerfile` | — | `python:3.9-slim` base, installs Oracle Instant Client libs, copies app, EXPOSE 7860, CMD python app.py |
| `docker-compose.yml` | — | Two services: `db` (gvenzl/oracle-xe:21-slim) + `web` (Flask). Named volume for Oracle data persistence. Auto-runs schema.sql on first boot. |
| `routes/auth_routes.py` | 189 | Login (PBKDF2 verify, session set), student application (INSERT with PENDING status), logout (session.clear) |
| `routes/admin_routes.py` | 829 | Add/edit course, add/edit faculty, approve student (4-op transaction), CO-PO MERGE, CGPA CTE query, analytics GROUP BY, Excel export, system settings |
| `routes/student_routes.py` | 922 | Dashboard (CGPA subquery, attendance %), register courses (LISTAGG, MERGE header), PDF generation (ReportLab BytesIO), examination results, profile update |
| `routes/faculty_routes.py` | 369 | Dashboard (enrolled count subquery), attendance grid (MERGE per student per day), grading (MERGE results), syllabus management (DELETE-INSERT) |
| `routes/course_routes.py` | — | Course catalog list and detail views |
| `models/student_model.py` | — | Early-stage model (legacy; business logic now in routes) |
| `services/pdf_service.py` | 117 | ReportLab PDF builder — reads student + courses from DB, builds document elements, returns BytesIO response |
| `utils/email_utils.py` | — | `notify_student_approval()` + `notify_registration_approval()`. Gmail SMTP with TLS. Falls back to terminal simulation if no SENDER_EMAIL set. |
| `utils/ppt_gen.py` | — | PowerPoint generation utility |
| `sql/schema.sql` | — | Complete Oracle DDL: 21 tables, 3 sequences, CHECK constraints, FK constraints, seed data. Auto-runs in Docker. |
| `create_demo_db.py` | — | Creates SQLite equivalent schema with seeded demo data for local development |
| `populate_sample_data.py` | — | Seeds realistic sample students, faculty, courses, registrations, results, attendance into DB |
| `templates/` | 28 files | Jinja2 HTML templates for all 28 pages across 3 roles |
| `static/` | — | CSS stylesheets, JS files, VNIT logo for PDF header |
| `demo_database.db` | 80KB | Pre-seeded SQLite file for instant demo without Oracle |

---

## CHALLENGES FACED

### Challenge 1: MERGE with Named Parameters — `DPY-4009` Error

**What happened:** When implementing CO-PO mapping (the matrix where admin sets weightage for each CO→PO pair), I used Oracle MERGE with named parameters:
```python
cursor.execute("""
    MERGE INTO co_po_mapping m
    USING (SELECT :co_id as co_id, :po_id as po_id FROM dual) src
    ON (m.course_outcome_id = src.co_id AND m.program_outcome_id = src.po_id)
    WHEN MATCHED THEN UPDATE SET m.weightage = :weight
    WHEN NOT MATCHED THEN INSERT (...) VALUES (src.co_id, src.po_id, :weight)
""", {"co_id": co_id, "po_id": po_id, "weight": weight})
```
**Error:** `DPY-4009: named bind variables are not allowed in this context`

**Why it happened:** The `oracledb` library has a constraint — inside `MERGE`'s `USING (SELECT ... FROM dual)` subquery, named parameters (`:co_id`) conflict with the driver's parsing. The driver gets confused about where the named param is bound.

**How identified:** Hit the error during testing. Read oracledb documentation and GitHub issues. Found that the USING clause treats the subquery as a separate context from the main MERGE.

**How fixed:** Separated the approach — bind parameters at the WHEN MATCHED / WHEN NOT MATCHED level and pre-select the values, or restructure parameter passing order precisely. Tested multiple orderings until the driver accepted it.

---

### Challenge 2: Oracle/SQLite Dual-Mode Compatibility

**What happened:** Oracle uses `:1`, `:name` bind params. SQLite uses `?`. Oracle uses `SYSDATE`, `NVL`, `LISTAGG`, `MERGE`, `FETCH FIRST N ROWS ONLY`, `IDENTITY` columns. SQLite uses `CURRENT_TIMESTAMP`, `COALESCE`, no `LISTAGG`, no `MERGE`, `AUTOINCREMENT`.

**Why it happened:** We needed the app to run without Oracle installed (for demos, local development, Hugging Face without Oracle). But Oracle-specific SQL breaks on SQLite.

**How identified:** Running locally with SQLite — every Oracle-specific query crashed. `LISTAGG` — function not found. `FETCH FIRST 1 ROWS ONLY` — syntax error. `SYSDATE` — unknown function.

**How fixed:**
- Created `OracleCompatibleCursor` wrapper in `config.py` that uses regex to convert `:name` → `?`
- In `create_demo_db.py`, rewrote schema using SQLite syntax (`AUTOINCREMENT`, `CURRENT_TIMESTAMP`, `COALESCE`)
- Replaced `LISTAGG` in SQLite mode with Python-level aggregation
- Used `DB_TYPE` environment variable to switch modes
- Kept Oracle as primary, SQLite as demo-only fallback

---

### Challenge 3: Attendance Grid at Scale — Race Condition & Performance

**What happened:** Initially implemented attendance using SELECT-then-INSERT/UPDATE:
```python
# VULNERABLE APPROACH:
cursor.execute("SELECT id FROM daily_attendance WHERE student_id=:1 AND ...", ...)
if cursor.fetchone():
    cursor.execute("UPDATE daily_attendance SET status=:1 WHERE ...", ...)
else:
    cursor.execute("INSERT INTO daily_attendance ...", ...)
```
For a class of 30 students × 31 days = 930 SELECT + 930 INSERT/UPDATE = 1860 DB round-trips.

**Why it happened:** Didn't consider concurrency initially. Two tabs submitting at once caused duplicate rows (both threads' SELECT returned "not found", both tried to INSERT → duplicate key error).

**How identified:** Tested concurrent submission from two browser tabs. Got `ORA-00001: unique constraint violated` error. Also noticed page was slow (~8 seconds for 30 students).

**How fixed:**
- Switched to MERGE — one SQL statement per attendance record. Handles both cases atomically.
- 930 MERGEs (not 1860 SELECT+INSERT pairs) — Oracle's row-level locking prevents duplicates
- Performance improved: MERGE executes 30–40% faster than SELECT-then-INSERT per record

---

### Challenge 4: CGPA Division by Zero

**What happened:** Students with no results yet caused CGPA query to fail: `SUM(credits) = 0` → division by zero → Oracle raised `ORA-01476: divisor is equal to zero`.

**How identified:** New student with no grades logged in → dashboard crashed.

**How fixed:**
```sql
ROUND(SUM(points * credits) / NULLIF(SUM(credits), 0), 2)
```
`NULLIF(SUM(credits), 0)` returns NULL if credits sum is 0. Division by NULL returns NULL (not error). Then Python shows "N.A." to the student.

---

### Challenge 5: Backlog Logic — Cleared vs Still Pending

**What happened:** A student fails DBMS in W25, then passes it in M25. When showing backlogs for the next registration, DBMS should NOT appear as a backlog anymore. Simple query `WHERE grade IN ('FF','W')` would show it as a backlog even after clearing.

**How identified:** Created test case: Insert FF grade for a course, then insert BB grade for same course, ran registration page — DBMS still appeared as backlog.

**How fixed:** Used NOT EXISTS anti-join:
```sql
SELECT ... FROM results r
WHERE r.student_id = :sid AND r.grade IN ('FF', 'W')
AND NOT EXISTS (
    SELECT 1 FROM results r2
    WHERE r2.student_id = r.student_id
    AND r2.course_id = r.course_id
    AND r2.grade NOT IN ('FF', 'W')
)
```
This finds failed courses that have NO subsequent passing grade — the correct backlog definition.

---

### Challenge 6: PDF Generation — Stateful BytesIO

**What happened:** Initially tried saving PDF to disk at `/tmp/registration.pdf`, then sending it. This caused: file permission errors in Docker container, stale PDFs when student re-registered, file cleanup complexity.

**How fixed:** Used `BytesIO()` — in-memory buffer. ReportLab writes to memory, `buffer.seek(0)` rewinds it, `make_response(buffer.getvalue())` streams it directly as HTTP response. No disk I/O, always fresh from DB.

---

## HOW CHALLENGES WERE OVERCOME — SUMMARY

| Challenge | Root Cause | Solution |
|---|---|---|
| DPY-4009 MERGE error | oracledb named param context restriction | Restructured parameter binding order in MERGE USING clause |
| Oracle/SQLite compatibility | Different SQL dialects | `OracleCompatibleCursor` + separate SQLite schema + DB_TYPE env var |
| Attendance race condition | SELECT-then-INSERT non-atomicity | Oracle MERGE — atomic upsert, row-level locking |
| CGPA division by zero | No results for new students | `NULLIF(SUM(credits), 0)` + Python null check |
| Backlog cleared-course detection | Simple grade filter insufficient | NOT EXISTS anti-join to check for subsequent pass |
| PDF disk management | File-based approach in containers | In-memory BytesIO streaming — no disk writes |

---

## RESULTS — What Was Achieved

### Functional Achievements
- **Complete digitization** of a paper-based institutional process
- **3-role RBAC system** working end-to-end: Student → Faculty → Admin
- **28 HTML pages** covering every workflow from application to result viewing
- **21-table Oracle schema** with full normalization (3NF), constraints, and referential integrity
- **PDF generation** on-the-fly with VNIT branding, course tables, and signatures
- **Daily attendance grid** for monthly tracking with % calculation
- **CGPA computation** using weighted grade points via SQL CTE
- **OBE compliance** via CO-PO mapping matrix (required for NAAC accreditation)
- **Email notifications** for student approval and registration approval

### Technical Achievements
- **Dual-database strategy** — same codebase runs on Oracle (production) and SQLite (demo)
- **Docker Compose** deployment — one command brings up Flask + Oracle XE
- **Deployed on Hugging Face Spaces** — public URL, free Docker Compose hosting
- **Zero SQL injection vulnerabilities** — parameterized queries throughout
- **Atomic transactions** — no partial data corruption possible
- **MERGE-based concurrency** — no race conditions in attendance or grading

### Why This Project Is Useful (Impact Statement)
> "This system eliminates an entire manual process that wastes 2–3 days per semester for each student. For an institution with 1,000 students, that's 2,000–3,000 person-hours saved per semester just on registration alone. The attendance digitization alone saves faculty 30 minutes per class of data entry. And the PDF slip generation means students always have an official printout within seconds."

### How to Project This in an Interview
- **Database skills:** "I designed a 21-table Oracle schema following 3NF normalization, used MERGE for atomic upserts, LISTAGG for aggregation, CTEs for CGPA, and sequences for thread-safe ID generation"
- **Backend skills:** "I built a multi-blueprint Flask application with session-based RBAC, parameterized SQL, PBKDF2 password hashing, and try/except/finally for connection management"
- **System design skills:** "I implemented a dual-database fallback, Docker Compose multi-container deployment, in-memory PDF generation, and email notification with SMTP simulation fallback"
- **Problem-solving skills:** "I identified and fixed a race condition in attendance using MERGE, resolved a DPY-4009 driver bug in Oracle named parameters, and built a NOT EXISTS anti-join for accurate backlog detection"

### Possible Follow-Up Questions & Quick Answers
- **"How would you scale this to 10,000 students?"** — Nginx load balancer + multiple Flask workers + Redis sessions + oracledb connection pooling + Celery for async email + Redis cache for course lists
- **"Why not use an ORM?"** — Oracle MERGE, LISTAGG, analytical functions are not supported by SQLAlchemy/Django ORM natively. Raw SQL gives full control.
- **"What's the most complex SQL query?"** — CGPA CTE with grade-to-points CASE mapping + weighted average + NULLIF division guard + LEFT JOIN for students with no results
- **"How is data consistency maintained?"** — CHECK constraints enforce valid status values, FK constraints prevent orphan records, transactions with ROLLBACK prevent partial updates, MERGE prevents duplicate attendance/grades
- **"What security measures did you implement?"** — PBKDF2 password hashing, parameterized queries (no SQL injection), signed session cookies (HMAC), role checks on every route, Jinja2 XSS escaping

---

*End of STAR Interview Preparation — Course Registration Portal*
