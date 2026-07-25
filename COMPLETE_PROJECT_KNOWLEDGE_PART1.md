# COMPLETE PROJECT KNOWLEDGE — Enterprise Course Registration Portal

# PART 1: PROJECT OVERVIEW, ARCHITECTURE, AND DATABASE

---

## 1. WHAT IS THIS PROJECT?

This is a full-stack academic course registration system built for VNIT Nagpur. It replaces the manual paper-based course registration process with a digital automated workflow. The system serves 3 user roles — Student, Faculty, and Admin — across 28 HTML pages, backed by a 21-table Oracle database schema.

**Why we built it:** In most Indian engineering colleges, course registration is done on paper forms. Students fill forms, get faculty advisor signatures, submit to the department office. This is slow, error-prone, and wastes paper. Our system digitizes this entire workflow.

**What problem it solves:**
- Students can register for courses online, view attendance, download PDF registration slips
- Faculty can mark daily attendance on a monthly calendar grid, enter grades, manage syllabus
- Admin can approve students, manage courses/faculty, view analytics, control system settings

---

## 2. TECHNOLOGY STACK — WHY EACH CHOICE

| Technology | Purpose | Why This Over Alternatives |
|---|---|---|
| **Flask** | Web framework | Micro-framework gives full control over Oracle SQL. Django's ORM would abstract away MERGE, LISTAGG, analytical functions we need |
| **Oracle XE / Autonomous DB** | Primary database | Enterprise-grade RDBMS with MERGE upserts, LISTAGG, analytical functions, sequences. Required for learning enterprise DB skills |
| **SQLite** | Fallback demo DB | Zero-config fallback when Oracle is unavailable. Allows demo on any machine |
| **Jinja2** | HTML templating | Flask's default. Template inheritance (base.html extends), loops, conditionals |
| **ReportLab** | PDF generation | Python library for programmatic PDF creation. Generates registration slips on-the-fly |
| **Werkzeug** | Password hashing | PBKDF2-HMAC-SHA256 with automatic salt. Industry standard for password security |
| **Docker + Docker Compose** | Containerization | Two-container setup (Flask + Oracle XE). One command deployment |
| **Hugging Face Spaces** | Cloud deployment | Free Docker Compose hosting with public URL |
| **oracledb** | Oracle Python driver | Oracle's official thin-mode Python driver. No Oracle Client installation needed |
| **python-dotenv** | Environment variables | Loads .env file for DB credentials, secret keys. Never hardcode secrets |
| **smtplib** | Email notifications | Python standard library for SMTP. Sends approval emails to students |
| **pandas + openpyxl** | Excel export | Admin can export student data to .xlsx files |

---

## 3. FOLDER STRUCTURE — EVERY FILE EXPLAINED

```
course_portal/
|-- app.py                  # Main Flask application entry point. Creates app, registers blueprints
|-- config.py               # Database connection logic. Oracle primary, SQLite fallback
|-- .env                    # Environment variables (DB_USER, DB_PASSWORD, DB_DSN, FLASK_SECRET)
|-- requirements.txt        # All Python dependencies with pinned versions
|-- Dockerfile              # Docker image definition for Flask container
|-- docker-compose.yml      # Multi-container setup: Flask (web) + Oracle XE (db)
|-- demo_database.db        # SQLite fallback database file
|-- create_demo_db.py       # Script to create and seed the SQLite demo database
|
|-- sql/
|   |-- schema.sql          # Complete Oracle schema: 21 tables, 3 sequences, constraints, seed data
|
|-- routes/
|   |-- __init__.py
|   |-- auth_routes.py      # Login, logout, student application (189 lines)
|   |-- admin_routes.py     # Admin dashboard, course/faculty CRUD, approvals, analytics (829 lines)
|   |-- student_routes.py   # Student dashboard, registration, PDF gen, examination (922 lines)
|   |-- faculty_routes.py   # Faculty dashboard, attendance grid, grading, syllabus (369 lines)
|   |-- course_routes.py    # Course listing and detail views (6825 bytes)
|
|-- models/
|   |-- student_model.py    # Early-stage student model (legacy, routes handle logic now)
|   |-- user_model.py       # User model placeholder
|   |-- course_model.py     # Course model placeholder
|
|-- services/
|   |-- pdf_service.py      # ReportLab PDF generation service for registration slips
|   |-- db_service.py       # Database service abstraction
|
|-- utils/
|   |-- email_utils.py      # SMTP email sending + simulation fallback
|   |-- ppt_gen.py          # PowerPoint generation utility
|
|-- templates/              # 28 Jinja2 HTML templates
|   |-- login.html
|   |-- student_application.html
|   |-- admin_dashboard.html
|   |-- student_dashboard.html
|   |-- faculty_dashboard.html
|   |-- register_courses.html
|   |-- view_registered.html
|   |-- attendance_grid.html
|   |-- enter_grades.html
|   |-- examination.html
|   |-- course_details.html
|   |-- manage_syllabus.html
|   |-- (and 16 more...)
|
|-- static/
|   |-- css/                # Stylesheets
|   |-- js/                 # JavaScript files
|   |-- vnit_logo.jpeg      # Institution logo for PDF headers
```

---

## 4. DATABASE SCHEMA — ALL 21 TABLES IN DETAIL

### 4.1 SYSTEM_CONFIG
**Purpose:** Stores global portal settings like current academic session and registration status.

| Column | Type | Description |
|---|---|---|
| config_key | VARCHAR2(50) PK | Setting name (e.g., 'current_academic_session') |
| config_value | VARCHAR2(200) | Setting value (e.g., 'W25') |
| updated_at | DATE | Last modification timestamp |

**Why:** Instead of hardcoding the current semester, admin can change it from the settings page. The registration_status key controls whether students can register (OPEN/CLOSED).

### 4.2 USERS
**Purpose:** Authentication table. Every login (student, faculty, admin) has a row here.

| Column | Type | Description |
|---|---|---|
| user_id | NUMBER PK | Generated via USERS_SEQ sequence |
| login_id | VARCHAR2(50) UNIQUE | Username (enrollment_no for students, email prefix for faculty) |
| password_hash | VARCHAR2(500) | PBKDF2-SHA256 hash from Werkzeug |
| role | VARCHAR2(20) | CHECK constraint: 'student', 'faculty', or 'admin' |
| student_id | NUMBER | FK to students (NULL for non-students) |
| faculty_id | NUMBER | FK to faculty (NULL for non-faculty) |
| created_at | DATE | Account creation date |

**Why separate from students/faculty?** Separation of concerns. Authentication data (credentials) is separate from profile data. One user could theoretically have multiple roles. The CHECK constraint on role enforces only valid values.

### 4.3 STUDENTS
**Purpose:** Student profile and application data.

| Column | Type | Description |
|---|---|---|
| student_id | NUMBER IDENTITY PK | Auto-generated primary key |
| user_id | NUMBER UNIQUE FK | Links to users table (NULL until approved) |
| enrollment_no | VARCHAR2(20) UNIQUE | Generated by admin on approval (e.g., VNIT2025101) |
| name | VARCHAR2(100) | Full name |
| email | VARCHAR2(100) | Email address |
| mobile | VARCHAR2(20) | Phone number |
| semester | NUMBER | Current semester |
| program | VARCHAR2(50) | e.g., 'M.TECH CSE', 'B.TECH CSE' |
| advisor_id | NUMBER FK | Links to faculty (faculty advisor) |
| status | VARCHAR2(20) | CHECK: 'PENDING', 'APPROVED', 'REJECTED' |
| registration_date | DATE | Application submission date |

**Why status field?** Implements the approval workflow. New applications start as PENDING. Admin reviews and changes to APPROVED (creating credentials) or REJECTED.

### 4.4 FACULTY
| Column | Type | Description |
|---|---|---|
| faculty_id | NUMBER PK | Generated via FACULTY_SEQ |
| user_id | NUMBER UNIQUE FK | Links to users table |
| faculty_name | VARCHAR2(100) | Full name |
| email | VARCHAR2(100) | Email |
| department | VARCHAR2(100) | Department name |

### 4.5 COURSE_MASTER
**Purpose:** Master course catalog. Contains course definitions independent of when/who teaches them.

| Column | Type | Description |
|---|---|---|
| course_id | NUMBER IDENTITY PK | Auto-generated |
| course_code | VARCHAR2(20) UNIQUE | e.g., 'CSL312' |
| course_title | VARCHAR2(200) | e.g., 'Database Management Systems' |
| course_type | VARCHAR2(10) | 'DC' (Departmental Core) or 'DE' (Departmental Elective) |
| program | VARCHAR2(100) | Which program this course belongs to |
| L, T, P | NUMBER | Lecture/Tutorial/Practical hours per week |
| credits | NUMBER | Credit value |

**Why separate from course_instance?** A course like "DBMS" exists permanently in the catalog. But it may be offered in W25 by Prof. A in Section A, and in M25 by Prof. B in Section B. The instance captures the offering; the master captures the definition.

### 4.6 COURSE_INSTANCE
**Purpose:** A specific offering of a course in a particular semester, by a particular faculty.

| Column | Type | Description |
|---|---|---|
| instance_id | NUMBER IDENTITY PK | |
| course_id | NUMBER FK | Which course from course_master |
| faculty_id | NUMBER FK | Who teaches it |
| academic_session | VARCHAR2(20) | e.g., 'W25' (Winter 2025) |
| semester | NUMBER | Semester number |
| section | VARCHAR2(10) | Section A, B, etc. |
| batch | VARCHAR2(10) | Batch identifier |
| slot | VARCHAR2(10) | Time slot |

### 4.7 COURSE_PREREQUISITES
| Column | Type | Description |
|---|---|---|
| id | NUMBER IDENTITY PK | |
| course_id | NUMBER FK | The course that has a prerequisite |
| prerequisite_course_id | NUMBER FK | The prerequisite course |

**Why self-referencing FKs?** Both FKs point to course_master. This models the "course A requires course B" relationship.

### 4.8 COURSE_OBJECTIVES
| Column | Type | Description |
|---|---|---|
| obj_id | NUMBER IDENTITY PK | |
| course_id | NUMBER FK | |
| description | VARCHAR2(1000) | Objective text |
| print_seq | NUMBER | Display order |

### 4.9 COURSE_OUTCOMES
| Column | Type | Description |
|---|---|---|
| outcome_id | NUMBER IDENTITY PK | |
| course_id | NUMBER FK | |
| outcome_desc | VARCHAR2(1000) | Outcome text |
| print_seq | NUMBER | Display order |

### 4.10 COURSE_DESCRIPTION
| Column | Type | Description |
|---|---|---|
| desc_id | NUMBER IDENTITY PK | |
| course_id | NUMBER FK | |
| topic | VARCHAR2(1000) | Syllabus topic |
| duration_weeks | NUMBER | How many weeks this topic takes |

### 4.11 TEXT_BOOKS
| Column | Type | Description |
|---|---|---|
| book_id | NUMBER IDENTITY PK | |
| course_id | NUMBER FK | |
| title | VARCHAR2(300) | Book title |
| type | VARCHAR2(50) | Category |

### 4.12 REFERENCE_BOOKS
Same structure as text_books but for reference materials.

### 4.13 STUDENT_REGISTRATION
**Purpose:** Header record for a student's course registration in a session.

| Column | Type | Description |
|---|---|---|
| reg_id | NUMBER IDENTITY PK | |
| student_id | NUMBER FK | |
| semester | NUMBER | |
| academic_session | VARCHAR2(20) | e.g., 'W25' |
| status | VARCHAR2(20) | CHECK: 'SUBMITTED', 'APPROVED', 'REJECTED' |
| registration_date | DATE | |

### 4.14 STUDENT_REGISTRATION_COURSES
**Purpose:** Line items — which courses are in a registration.

| Column | Type | Description |
|---|---|---|
| id | NUMBER IDENTITY PK | |
| reg_id | NUMBER FK | Links to student_registration |
| course_instance_id | NUMBER FK | Links to course_instance |
| course_type | VARCHAR2(5) | DC or DE |

**Why two tables?** This is a header-detail (master-detail) pattern. One registration (header) has many courses (details). This is standard normalized design.

### 4.15 RESULTS
| Column | Type | Description |
|---|---|---|
| result_id | NUMBER IDENTITY PK | |
| student_id | NUMBER FK | |
| course_id | NUMBER FK | |
| academic_session | VARCHAR2(20) | |
| grade | NUMBER(5,2) | Numeric grade |
| grade_letter | VARCHAR2(5) | Letter grade (AA, AB, BB, BC, CC, CD, DD, FF) |

### 4.16 ATTENDANCE
| Column | Type | Description |
|---|---|---|
| attendance_id | NUMBER IDENTITY PK | |
| student_id | NUMBER FK | |
| course_instance_id | NUMBER FK | |
| attendance_percentage | NUMBER(5,2) | Calculated percentage |
| updated_date | DATE | |

### 4.17 COORDINATOR
**Purpose:** Maps faculty advisors to students.

| Column | Type | Description |
|---|---|---|
| id | NUMBER IDENTITY PK | |
| faculty_id | NUMBER FK | |
| student_id | NUMBER FK | |
| academic_session | VARCHAR2(20) | |

### 4.18 PROGRAM_OUTCOMES
| Column | Type | Description |
|---|---|---|
| po_id | NUMBER IDENTITY PK | |
| po_code | VARCHAR2(10) UNIQUE | e.g., 'PO1' |
| po_description | VARCHAR2(1000) | e.g., 'Engineering Knowledge' |

### 4.19 CO_PO_MAPPING
**Purpose:** Maps Course Outcomes to Program Outcomes with a weightage (0-3 scale). Used for OBE (Outcome Based Education) compliance.

| Column | Type | Description |
|---|---|---|
| id | NUMBER IDENTITY PK | |
| course_outcome_id | NUMBER FK ON DELETE CASCADE | |
| program_outcome_id | NUMBER FK ON DELETE CASCADE | |
| weightage | NUMBER(3) CHECK 0-3 | |

### 4.20 EVALUATION_DETAILS
| Column | Type | Description |
|---|---|---|
| eval_id | NUMBER IDENTITY PK | |
| course_id | NUMBER FK ON DELETE CASCADE | |
| component_name | VARCHAR2(100) | e.g., 'Mid-Sem', 'End-Sem', 'Quiz' |
| weightage_percent | NUMBER(5,2) | |

### 4.21 COURSE_EQUIVALENTS
| Column | Type | Description |
|---|---|---|
| id | NUMBER IDENTITY PK | |
| course_id | NUMBER FK ON DELETE CASCADE | |
| equivalent_course_id | NUMBER FK ON DELETE CASCADE | |

---

## 5. SEQUENCES

| Sequence | Purpose |
|---|---|
| USERS_SEQ | Generates user_id for the users table |
| STUDENTS_SEQ | Generates student_id for student applications |
| FACULTY_SEQ | Generates faculty_id |

**Why sequences over IDENTITY?** Some tables use IDENTITY (auto-increment), others use sequences. Sequences give more control — you can get NEXTVAL before INSERT, use it across multiple tables in one transaction (e.g., create user + link to student in same commit).

---

## 6. KEY DATABASE RELATIONSHIPS (ER Summary)

```
users 1──1 students (via user_id)
users 1──1 faculty (via user_id)
faculty 1──N course_instance (faculty teaches many course offerings)
course_master 1──N course_instance (one course offered multiple times)
students 1──N student_registration (one student registers each semester)
student_registration 1──N student_registration_courses (one registration has many courses)
course_instance 1──N student_registration_courses (one offering has many enrollments)
course_master 1──N course_outcomes (one course has many COs)
course_outcomes N──N program_outcomes (via co_po_mapping junction table)
students 1──N results (one student has many results)
faculty 1──N students (via advisor_id — faculty advises students)
```

---

*Continued in PART 2...*
