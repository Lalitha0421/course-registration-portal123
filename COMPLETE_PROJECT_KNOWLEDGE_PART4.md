# COMPLETE PROJECT KNOWLEDGE — PART 4

# INTERVIEW Q&A — BASIC TO ADVANCED

---

## 21. BASIC QUESTIONS

**Q: What is this project about?**
A: It's a full-stack academic course registration system for VNIT Nagpur. It automates paper-based registration with 3 roles (Student, Faculty, Admin), 28 pages, 21-table Oracle schema, Docker deployment.

**Q: Why did you build it?**
A: To solve a real institutional problem — manual paper registration is slow, error-prone, and doesn't scale. This system automates student applications, admin approvals, course registration, attendance tracking, grading, and PDF slip generation.

**Q: What technologies did you use?**
A: Flask (web framework), Oracle XE/Autonomous DB (primary database), SQLite (fallback), Jinja2 (templating), ReportLab (PDF generation), Werkzeug (password hashing), Docker Compose (containerization), Hugging Face Spaces (cloud deployment), smtplib (email), pandas/openpyxl (Excel export).

**Q: How many tables and why so many?**
A: 21 tables. Each represents a distinct entity or relationship. Normalization requires separating concerns — course definitions (course_master) from course offerings (course_instance) from student registrations (student_registration + student_registration_courses). This avoids data duplication and ensures integrity.

**Q: How does a student register?**
A: 1) Student submits application form (name, email, program). 2) Record saved with status=PENDING. 3) Admin reviews and clicks Approve. 4) System generates enrollment number, hashes temporary password, creates login credentials, sends email. 5) Student logs in, selects courses (all DC + 2 DE), submits. 6) Admin approves registration. 7) Student downloads PDF slip.

---

## 22. TECHNICAL QUESTIONS

**Q: Explain Oracle MERGE. Where did you use it?**
A: MERGE is an atomic upsert — INSERT if row doesn't exist, UPDATE if it does. I used it in 4 places:
1. Daily attendance (faculty marks present/absent per student per day)
2. CO-PO mapping (admin sets weightage 0-3 per CO-PO pair)
3. Student registration header (create or update registration per session)
4. Grading (faculty enters/updates grades per student per course)

Why not SELECT then INSERT/UPDATE? Race conditions. Two concurrent MERGE statements on the same row are handled safely by Oracle's row-level locking.

**Q: What is LISTAGG? Why did you use it?**
A: LISTAGG aggregates multiple row values into a single comma-separated string within a GROUP BY. I used it to show all faculty members and sections for a course in one row:
```sql
LISTAGG(NVL(f.faculty_name, 'N/A'), ', ') WITHIN GROUP (ORDER BY f.faculty_name)
```
Without it, a course taught by 3 faculty would appear as 3 separate rows in the UI.

**Q: How does CGPA calculation work?**
A: Using a CTE (WITH clause) and weighted average:
1. Map letter grades to points: AA=10, AB=9, BB=8, BC=7, CC=6, CD=5, DD=4, FF=0
2. Multiply each grade's points by course credits
3. Sum (points x credits) / Sum (credits) = CGPA
4. NULLIF(SUM(credits), 0) prevents division by zero for students with no results

**Q: How does attendance percentage work?**
A: Correlated subquery with conditional aggregation:
```sql
ROUND(
  COUNT(CASE WHEN status = 'PRESENT' THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0), 2
)
```
COUNT(CASE WHEN...) counts only PRESENT records. COUNT(*) counts all records. Division gives percentage. NULLIF prevents division by zero. Calculated at query time — always real-time.

**Q: How does the attendance grid work?**
A: The monthly calendar grid is a faculty feature. It's a table where rows are students and columns are days of the month (1-31). Python's `calendar.monthrange(year, month)` determines the number of days. On page load, existing attendance is fetched using EXTRACT(DAY FROM attendance_date) and pre-populated. On submit, every cell is processed — each student x day combination runs a MERGE into daily_attendance.

**Q: How do you handle backlogs?**
A: Backlogs are courses where a student got grade 'FF' (fail) or 'W' (withdrawn). When registering for a new semester, the system queries:
```sql
SELECT ... FROM results r WHERE r.student_id = :sid AND r.grade IN ('FF', 'W')
AND NOT EXISTS (SELECT 1 FROM results r2 WHERE r2.student_id = r.student_id 
    AND r2.course_id = r.course_id AND r2.grade NOT IN ('FF', 'W'))
```
This finds failed courses that haven't been subsequently cleared. These are mandatory re-registrations.

**Q: How does session-based auth work in Flask?**
A: On login: store user_id, role, name in `flask.session`. Flask serializes this into a cookie, signs it with SECRET_KEY (HMAC-SHA1). On each request, Flask reads the cookie, verifies the signature, deserializes the session. If tampered, signature check fails and session is rejected. On logout: `session.clear()`.

**Q: How did you implement RBAC?**
A: Every route starts with a role check:
```python
if session.get('role') != 'admin':
    flash('Access denied', 'danger')
    return redirect(url_for('auth.login_page'))
```
Even if a student knows the URL `/admin/dashboard`, they can't access it because the role check redirects them. The role is stored server-side in the session — the client can't forge it.

**Q: Explain parameterized queries and SQL injection.**
A: SQL injection happens when user input is directly concatenated into SQL:
```python
# VULNERABLE:
cursor.execute(f"SELECT * FROM users WHERE login_id = '{user_input}'")
# If user_input = "admin' OR '1'='1" → returns all users!

# SAFE (parameterized):
cursor.execute("SELECT * FROM users WHERE login_id = :1", (user_input,))
# :1 is treated as DATA, not SQL code. Oracle handles escaping.
```

**Q: Why Flask over Django?**
A: I needed direct Oracle SQL access. Django's ORM generates SQL automatically — it doesn't support Oracle MERGE, LISTAGG, or analytical functions natively. Flask lets me write raw SQL with oracledb, giving full control. Django would have added abstraction I didn't need.

**Q: How does the PDF generation work?**
A: ReportLab builds PDFs programmatically. I create a SimpleDocTemplate with letter-size page, add elements (Paragraphs, Tables, Images, Spacers), call doc.build(elements). The PDF is generated in-memory using BytesIO — not saved to disk. The buffer is returned as a Flask response with Content-Type: application/pdf. The browser downloads it directly.

**Q: How does the dual-database (Oracle/SQLite) strategy work?**
A: config.py reads DB_TYPE from environment. If ORACLE and credentials exist, connects to Oracle. If connection fails or credentials missing, falls back to SQLite. The SQLite version (create_demo_db.py) mirrors the Oracle schema but uses SQLite syntax (AUTOINCREMENT instead of IDENTITY, ? instead of :1). This allows demos without Oracle installed.

**Q: Explain Docker Compose for this project.**
A: Two services: `db` (Oracle XE container) and `web` (Flask container). Docker Compose creates an internal network so `web` can reach `db` by hostname. The DSN `db:1521/XE` resolves because Docker's internal DNS maps service names to IPs. Volume `oracle_data` persists database files. `depends_on` ensures Oracle starts before Flask. One command `docker-compose up` runs everything.

---

## 23. ADVANCED / SYSTEM DESIGN QUESTIONS

**Q: How would you scale to 10,000 students?**
A: 1) Run multiple Flask workers behind Nginx load balancer. 2) Move sessions to Redis (shared across workers). 3) Use oracledb.SessionPool for connection pooling. 4) Move email sending to Celery background workers. 5) Cache course lists in Redis. 6) Use Oracle Autonomous DB for auto-scaling.

**Q: What would you change if starting over?**
A: 1) REST API backend + React frontend (better separation). 2) Proper permission system (not just role strings). 3) Comprehensive test suite with pytest. 4) Audit logging table for all admin actions. 5) Rate limiting on login endpoint. 6) WebSocket for real-time notifications instead of email-only.

**Q: What security vulnerabilities exist and how did you address them?**
A: SQL Injection (parameterized queries), XSS (Jinja2 auto-escaping), CSRF (Flask-WTF tokens), Password storage (PBKDF2 hashing with salt), Session fixation (Flask regenerates session), Unauthorized access (role checks on every route), Secret management (.env file, never hardcoded).

**Q: Explain the approval workflow as a state machine.**
A: Student application: PENDING -> APPROVED/REJECTED. Course registration: NOT_STARTED -> SUBMITTED -> APPROVED/REJECTED. Each transition triggers actions: PENDING->APPROVED creates credentials and sends email. SUBMITTED->APPROVED sends notification. Status is enforced by CHECK constraints in Oracle.

**Q: How does the system handle concurrent access?**
A: Oracle handles concurrency at the database level with row-level locking. MERGE statements are atomic. Flask sessions are per-user (no shared state). Each request gets its own database connection (no connection sharing between requests). For higher concurrency, use connection pooling.

---

## 24. BEHAVIORAL QUESTIONS

**Q: What was the hardest challenge?**
A: The Oracle MERGE for attendance at scale. Initially I used SELECT-then-INSERT/UPDATE which caused race conditions with concurrent faculty submissions. Refactoring to MERGE eliminated duplicates and reduced DB round-trips from 2 to 1 per record.

**Q: How did you test it?**
A: Three levels: 1) Unit testing individual functions (password hashing, enrollment generation). 2) Integration testing Flask routes with test DB. 3) Manual testing with all 3 role accounts through every workflow. Edge cases: duplicate email registration, future-date attendance, student accessing admin URLs.

**Q: Why Hugging Face Spaces for deployment?**
A: It supports Docker Compose for free — rare among free platforms. Most (Render, Railway) only support single containers. I needed two (Flask + Oracle). It also gives a public URL for portfolio demos.

**Q: What did you learn from this project?**
A: 1) Enterprise database design (normalization, constraints, sequences). 2) Real-world workflow automation (approval flows, state machines). 3) Production deployment (Docker, environment variables, secrets management). 4) The importance of atomic database operations (MERGE vs manual upsert). 5) Security best practices (PBKDF2, parameterized queries, RBAC).

---

## 25. QUICK REFERENCE — SQL CHEAT SHEET FOR THIS PROJECT

| Operation | SQL Used |
|---|---|
| Login check | `SELECT user_id, password_hash FROM users WHERE login_id = :1 AND role = :2` |
| Duplicate check | `SELECT 1 FROM students WHERE email = :1` |
| Auto-ID | `SELECT NVL(MAX(course_id), 0) + 1 FROM course_master` |
| Sequence | `SELECT USERS_SEQ.NEXTVAL FROM dual` |
| Upsert | `MERGE INTO ... USING ... ON (...) WHEN MATCHED THEN UPDATE ... WHEN NOT MATCHED THEN INSERT ...` |
| Aggregation | `LISTAGG(f.faculty_name, ', ') WITHIN GROUP (ORDER BY f.faculty_name)` |
| Conditional count | `COUNT(CASE WHEN status = 'PRESENT' THEN 1 END)` |
| Safe division | `NULLIF(SUM(credits), 0)` |
| CTE | `WITH grade_points AS (...) SELECT ...` |
| Row limiting | `FETCH FIRST 1 ROWS ONLY` |
| Date extract | `EXTRACT(DAY FROM attendance_date)` |
| NULL handling | `NVL(f.faculty_name, 'N/A')` |
| Subquery in SELECT | `(SELECT COUNT(*) FROM ... WHERE ...)` as column |
| NOT EXISTS | Anti-join for finding uncleared backlogs |
| JOIN types | INNER JOIN (courses+faculty), LEFT JOIN (students+attendance) |
| GROUP BY + HAVING | Analytics aggregations |

---

**END OF COMPLETE PROJECT KNOWLEDGE DOCUMENT**

*This document covers all 21 tables, all routes, all SQL functions, all design decisions, deployment details, and interview Q&A from basic to advanced. Reading this should enable you to answer any question about this project.*
