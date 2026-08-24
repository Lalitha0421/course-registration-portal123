# STAR Interview Preparation — Course Registration Portal
## Part 1: Situation, Task, Problem Statement & Complete Workflow

---

## S — SITUATION (Need of the Problem Statement)

### Why This Project Exists — The Real-World Problem

In most Indian engineering colleges like **VNIT Nagpur**, course registration is a fully manual, paper-based process. Every semester, students:
1. Collect a physical registration form from the department office
2. Hand-fill their course selections (DC + DE courses)
3. Walk to their Faculty Advisor's office to get a physical signature
4. Submit the paper form back to the department
5. Wait for the office to manually enter data into spreadsheets

**This process is broken in 5 ways:**
| Problem | Real Impact |
|---|---|
| Paper forms get lost | Students must redo the entire process |
| No real-time visibility | Admin can't see who registered, who's pending |
| Manual data entry into Excel | Human errors, wrong course codes |
| No backlog tracking | Faculty don't know which students have failed courses |
| No attendance digitization | Attendance registers are paper-based, can't calculate % |

### Where Is This Used?
- Engineering colleges with semester-based credit systems
- Institutions following CBCS (Choice Based Credit System) or OBE (Outcome Based Education)
- Any university managing 500–5000 students across multiple programs (B.TECH, M.TECH, MBA)
- Directly applicable to VNIT Nagpur's actual workflow

### What This Project Demonstrates (Real Usage)
This isn't a toy project. It models a **complete institutional workflow**:
- A student applies → Admin reviews and approves → Student gets login credentials via email
- Student logs in → Selects courses → Admin approves registration → Student downloads official PDF slip
- Faculty marks daily attendance on a calendar grid → System calculates % automatically
- Faculty enters grades → System computes CGPA using weighted formula
- Admin views analytics — grade distribution, program-wise registration counts, CGPA rankings

---

## T — TASK (Problem It Tries to Solve)

### The 3-Role System Explained

The system has **exactly 3 roles**. Here is what each role does, end-to-end:

---

### ROLE 1: STUDENT

**Function 1: Apply for Admission**
- Student opens the portal → clicks "New Student Application"
- Fills form: Name, Email, Mobile, Program (B.TECH CSE / M.TECH CSE), Aadhaar, DOB, Address, Hosteller Y/N
- System inserts into `STUDENTS` table with `status = 'PENDING'`
- Student has NO login yet — that comes after admin approval

**Function 2: Login (after approval)**
- Student uses `enrollment_no` as login_id (e.g., `VNIT2025101`) and temporary password `VNIT@123`
- System checks `USERS` table, verifies PBKDF2 hash, sets Flask session

**Function 3: Register Courses**
- Student opens `/student/register_courses`
- System checks `system_config` → if `registration_status = 'OPEN'`, proceeds
- System fetches **DC courses** (Departmental Core — mandatory) using LISTAGG SQL
- System fetches **DE courses** (Departmental Elective — student picks 2)
- System fetches **Backlogs** — courses where student got grade `FF` or `W` and hasn't cleared yet
- Student selects all DCs + exactly 2 DEs + any backlogs → clicks Submit
- MERGE SQL creates/updates `STUDENT_REGISTRATION` header
- `STUDENT_REGISTRATION_COURSES` gets one row per course selected
- Admin sees it in queue → approves → student gets email notification

**Function 4: Download PDF Registration Slip**
- After approval, student clicks "Generate PDF"
- System uses ReportLab → builds PDF in memory (BytesIO) with:
  - VNIT logo + institution name
  - Student info (8 fields: name, enrollment no, faculty advisor, mobile, address, email, hosteller, date)
  - Course table (9 columns: Sr, Code, Title, Section, Batch, Slot, Type, Credits, Coordinator)
  - Summary: DC count, DE count, total credits
  - Signature lines
- PDF is streamed directly as HTTP download — never saved to disk

**Function 5: View Attendance**
- Student dashboard shows each registered course with real-time attendance %
- Calculated via correlated subquery: `COUNT(PRESENT) * 100 / COUNT(*)` from `DAILY_ATTENDANCE`
- Student can click a course to see day-by-day record

**Function 6: View Results & Backlogs**
- Student opens `/student/examination`
- Selects semester + session from dropdown
- System separates results: grade `FF/W` → backlogs list, others → cleared list
- Shows total cleared credits (sum of credits where grade ≠ FF/W)
- CGPA computed as: `SUM(grade_points × credits) / SUM(credits)` using CASE-based mapping

**Function 7: Update Profile**
- Student can update email, mobile, address
- Can change password (min 6 chars, re-hashed with PBKDF2)

---

### ROLE 2: FACULTY

**Function 1: View Dashboard**
- Lists all assigned courses with: enrolled student count, average attendance %
- Lists all advised/coordinated students with current semester

**Function 2: Mark Attendance (Monthly Calendar Grid)**
- Faculty opens `/faculty/attendance/<course_instance_id>`
- Python's `calendar.monthrange(year, month)` determines number of days
- Grid renders: Rows = Students, Columns = Days 1–31
- Existing attendance pre-filled using `EXTRACT(DAY FROM attendance_date)` from `DAILY_ATTENDANCE`
- Faculty checks/unchecks cells (PRESENT / ABSENT)
- On submit: for every student × every day → Oracle MERGE into `DAILY_ATTENDANCE`
  - If record exists → UPDATE status
  - If record doesn't exist → INSERT new record
- This is fully atomic — no race conditions, no duplicates

**Function 3: Enter Grades**
- Faculty opens `/faculty/grading/<instance_id>`
- Lists all enrolled students with existing grades
- Faculty enters letter grade (AA, AB, BB, BC, CC, CD, DD, FF)
- Oracle MERGE into `RESULTS` table — upsert per student per course per session

**Function 4: Manage Syllabus**
- Faculty can edit course objectives, outcomes, and weekly syllabus topics
- System verifies: `SELECT 1 FROM course_instance WHERE faculty_id = :fid AND course_id = :cid`
- Only authorized faculty can edit their own courses
- Pattern: DELETE existing → INSERT new (handles variable count of objectives/outcomes)

**Function 5: View Advised Students**
- Faculty can see full profile of each student they advise (coordinator)
- Shows student's current courses + attendance % per course

---

### ROLE 3: ADMIN

**Function 1: Manage Students**
- View all students (pending, approved, rejected)
- Approve a student → system does 4 operations in ONE transaction:
  1. Generate `enrollment_no` = `VNIT{year}{student_id}` (e.g., VNIT2025101)
  2. Hash temporary password `VNIT@123` using PBKDF2
  3. INSERT into `USERS` table with `role = 'student'`
  4. UPDATE `STUDENTS` table: `status = 'APPROVED'`, set `enrollment_no`, set `user_id`
  - COMMIT at end; ROLLBACK on any failure — full atomicity
  - Sends email notification via SMTP with login credentials

**Function 2: Manage Courses**
- Add new course → inserts into `COURSE_MASTER` + creates `COURSE_INSTANCE`
- Edit course → update title, credits, type in course_master; DELETE + re-INSERT evaluation weights
- Manage objectives, outcomes per course using DELETE-then-INSERT pattern

**Function 3: CO-PO Mapping**
- Admin sets Course Outcome → Program Outcome mapping on a matrix grid
- Each cell = weightage (0, 1, 2, or 3)
- Oracle MERGE per CO-PO pair: update if exists, insert if new
- Used for OBE (Outcome Based Education) institutional compliance

**Function 4: Manage Faculty**
- Add faculty → creates USER record (login_id = email prefix, hashed password "faculty123")
- Creates FACULTY record → links back to USER via `faculty_id`
- Edit faculty name, email, department

**Function 5: Approve Course Registrations**
- Views all submitted registrations with course count
- Clicks Approve → updates `student_registration.status = 'APPROVED'` → sends email

**Function 6: Analytics Dashboard**
- Registration status breakdown (SUBMITTED/APPROVED/REJECTED counts)
- Grade distribution across all students
- Department-wise student count (B.TECH vs M.TECH)

**Function 7: System Settings**
- Control `current_academic_session` (e.g., 'W25' = Winter 2025)
- Control `registration_status` = `OPEN` or `CLOSED`
- When CLOSED, students see a message and can't register

**Function 8: Export to Excel**
- Admin clicks Export → pandas reads from DB, creates `.xlsx` using openpyxl
- Sent as HTTP response with proper Content-Type header

---

## Complete Workflow — One Student's Full Journey (Interview Story)

> **"Let me walk you through the entire system from a student named Rahul applying for the first time."**

**Step 1:** Rahul opens the portal. He clicks "New Student Application." Fills his details — name, email, B.TECH CSE program, hostel yes. Hits submit. The system inserts a row into the `STUDENTS` table with `status = 'PENDING'`. Rahul has no login yet.

**Step 2:** Admin logs in. Opens "Pending Students." Sees Rahul's application. Clicks Approve. In one database transaction: enrollment number `VNIT2025101` is generated, password `VNIT@123` is hashed, a row is inserted in `USERS` table, and the students row is updated with status = `APPROVED`. Rahul receives an email with his credentials.

**Step 3:** Rahul logs in using `VNIT2025101` / `VNIT@123`. Flask stores his `user_id`, `student_id`, `role = student` in a signed session cookie. He's redirected to the student dashboard.

**Step 4:** Registration is OPEN (admin set it). Rahul clicks Register Courses. System fetches 6 DC courses mandatory for B.TECH CSE in session W25 using LISTAGG SQL — one row per course even though 3 faculty teach it. Fetches 4 DE options. Rahul has no backlogs (first semester). He selects all DCs + 2 DEs. Hits Submit. MERGE SQL creates the `STUDENT_REGISTRATION` header row. 8 rows get inserted into `STUDENT_REGISTRATION_COURSES` (one per course).

**Step 5:** Admin sees registration in queue. Approves it. Rahul gets email.

**Step 6:** Rahul downloads his PDF registration slip. ReportLab builds it in memory — VNIT logo, his 8 personal details, course table with sections/batches/slots/credits, summary totals, signature lines. Browser downloads it immediately.

**Step 7:** Faculty Dr. Sharma logs in. Opens attendance grid for CSL312 (DBMS). It's a 31-day month. Python's `calendar.monthrange` gives 31 days. Grid shows 30 students × 31 columns. Dr. Sharma checks present for each day. On submit, 930 MERGE statements execute (30 students × 31 days) — all atomic.

**Step 8:** Semester ends. Dr. Sharma opens grading for CSL312. Rahul gets grade `BB`. MERGE inserts into `RESULTS` table. CGPA = (8 × 4 credits + ... ) / total credits = computed with NULLIF to prevent division by zero.

**Step 9:** Rahul opens Examination. Selects W25 session. Sees his grade BB for DBMS in the cleared list. CGPA shows 7.8. He's done.

---

*Continued in Part 2: Technical Details, DBMS Principles, Challenges & Results*
