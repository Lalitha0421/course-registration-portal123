--------------------------------------------------
-- DROP TABLES (Ordered for constraints)
--------------------------------------------------

BEGIN EXECUTE IMMEDIATE 'DROP TABLE attendance CASCADE CONSTRAINTS'; EXCEPTION WHEN OTHERS THEN NULL; END;
/
BEGIN EXECUTE IMMEDIATE 'DROP TABLE results CASCADE CONSTRAINTS'; EXCEPTION WHEN OTHERS THEN NULL; END;
/
BEGIN EXECUTE IMMEDIATE 'DROP TABLE student_registration_courses CASCADE CONSTRAINTS'; EXCEPTION WHEN OTHERS THEN NULL; END;
/
BEGIN EXECUTE IMMEDIATE 'DROP TABLE student_registration CASCADE CONSTRAINTS'; EXCEPTION WHEN OTHERS THEN NULL; END;
/
BEGIN EXECUTE IMMEDIATE 'DROP TABLE coordinator CASCADE CONSTRAINTS'; EXCEPTION WHEN OTHERS THEN NULL; END;
/
BEGIN EXECUTE IMMEDIATE 'DROP TABLE course_instance CASCADE CONSTRAINTS'; EXCEPTION WHEN OTHERS THEN NULL; END;
/
BEGIN EXECUTE IMMEDIATE 'DROP TABLE reference_books CASCADE CONSTRAINTS'; EXCEPTION WHEN OTHERS THEN NULL; END;
/
BEGIN EXECUTE IMMEDIATE 'DROP TABLE text_books CASCADE CONSTRAINTS'; EXCEPTION WHEN OTHERS THEN NULL; END;
/
BEGIN EXECUTE IMMEDIATE 'DROP TABLE course_description CASCADE CONSTRAINTS'; EXCEPTION WHEN OTHERS THEN NULL; END;
/
BEGIN EXECUTE IMMEDIATE 'DROP TABLE course_outcomes CASCADE CONSTRAINTS'; EXCEPTION WHEN OTHERS THEN NULL; END;
/
BEGIN EXECUTE IMMEDIATE 'DROP TABLE course_objectives CASCADE CONSTRAINTS'; EXCEPTION WHEN OTHERS THEN NULL; END;
/
BEGIN EXECUTE IMMEDIATE 'DROP TABLE course_prerequisites CASCADE CONSTRAINTS'; EXCEPTION WHEN OTHERS THEN NULL; END;
/
BEGIN EXECUTE IMMEDIATE 'DROP TABLE course_master CASCADE CONSTRAINTS'; EXCEPTION WHEN OTHERS THEN NULL; END;
/
BEGIN EXECUTE IMMEDIATE 'DROP TABLE students CASCADE CONSTRAINTS'; EXCEPTION WHEN OTHERS THEN NULL; END;
/
BEGIN EXECUTE IMMEDIATE 'DROP TABLE faculty CASCADE CONSTRAINTS'; EXCEPTION WHEN OTHERS THEN NULL; END;
/
BEGIN EXECUTE IMMEDIATE 'DROP TABLE users CASCADE CONSTRAINTS'; EXCEPTION WHEN OTHERS THEN NULL; END;
/
BEGIN EXECUTE IMMEDIATE 'DROP TABLE system_config CASCADE CONSTRAINTS'; EXCEPTION WHEN OTHERS THEN NULL; END;
/

--------------------------------------------------
-- DROP & CREATE SEQUENCES
--------------------------------------------------
BEGIN EXECUTE IMMEDIATE 'DROP SEQUENCE USERS_SEQ'; EXCEPTION WHEN OTHERS THEN NULL; END;
/
CREATE SEQUENCE USERS_SEQ START WITH 1 INCREMENT BY 1;
/
BEGIN EXECUTE IMMEDIATE 'DROP SEQUENCE STUDENTS_SEQ'; EXCEPTION WHEN OTHERS THEN NULL; END;
/
CREATE SEQUENCE STUDENTS_SEQ START WITH 1 INCREMENT BY 1;
/
BEGIN EXECUTE IMMEDIATE 'DROP SEQUENCE FACULTY_SEQ'; EXCEPTION WHEN OTHERS THEN NULL; END;
/
CREATE SEQUENCE FACULTY_SEQ START WITH 1 INCREMENT BY 1;
/

--------------------------------------------------
-- SYSTEM CONFIG
--------------------------------------------------

CREATE TABLE system_config (
    config_key VARCHAR2(50) PRIMARY KEY,
    config_value VARCHAR2(200),
    updated_at DATE DEFAULT SYSDATE
);

-- Initial Config
INSERT INTO system_config (config_key, config_value) VALUES ('current_academic_session', 'W25');
INSERT INTO system_config (config_key, config_value) VALUES ('registration_status', 'OPEN');
COMMIT;

--------------------------------------------------
-- USERS
--------------------------------------------------

CREATE TABLE users (
    user_id NUMBER PRIMARY KEY,
    login_id VARCHAR2(50) UNIQUE NOT NULL,
    password_hash VARCHAR2(500) NOT NULL, -- Increased length for hashing
    role VARCHAR2(20) CHECK (role IN ('student','faculty','admin')),
    student_id NUMBER, -- Direct link
    faculty_id NUMBER, -- Direct link
    created_at DATE DEFAULT SYSDATE
);

--------------------------------------------------
-- FACULTY
--------------------------------------------------

CREATE TABLE faculty (
    faculty_id NUMBER PRIMARY KEY,
    user_id NUMBER UNIQUE,
    faculty_name VARCHAR2(100),
    email VARCHAR2(100),
    department VARCHAR2(100),
    CONSTRAINT fk_faculty_user FOREIGN KEY (user_id) REFERENCES users(user_id)
);

--------------------------------------------------
-- STUDENTS
--------------------------------------------------

CREATE TABLE students (
    student_id NUMBER GENERATED AS IDENTITY PRIMARY KEY,
    user_id NUMBER UNIQUE,
    enrollment_no VARCHAR2(20) UNIQUE, -- Populated by Admin upon approval
    name VARCHAR2(100),
    email VARCHAR2(100),
    mobile VARCHAR2(20),
    semester NUMBER,
    program VARCHAR2(50),
    advisor_id NUMBER,
    status VARCHAR2(20) DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'APPROVED', 'REJECTED')),
    registration_date DATE DEFAULT SYSDATE,
    CONSTRAINT fk_student_user FOREIGN KEY (user_id) REFERENCES users(user_id),
    CONSTRAINT fk_student_advisor FOREIGN KEY (advisor_id) REFERENCES faculty(faculty_id)
);

--------------------------------------------------
-- COURSE MASTER
--------------------------------------------------

CREATE TABLE course_master (
    course_id NUMBER GENERATED AS IDENTITY PRIMARY KEY,
    course_code VARCHAR2(20) UNIQUE,
    course_title VARCHAR2(200),
    course_type VARCHAR2(10), -- DC, DE, etc.
    program VARCHAR2(100),
    L NUMBER DEFAULT 0,
    T NUMBER DEFAULT 0,
    P NUMBER DEFAULT 0,
    credits NUMBER DEFAULT 0
);

--------------------------------------------------
-- COURSE PREREQUISITES
--------------------------------------------------

CREATE TABLE course_prerequisites (
    id NUMBER GENERATED AS IDENTITY PRIMARY KEY,
    course_id NUMBER,
    prerequisite_course_id NUMBER,
    CONSTRAINT fk_pr_course FOREIGN KEY (course_id) REFERENCES course_master(course_id),
    CONSTRAINT fk_prereq_course FOREIGN KEY (prerequisite_course_id) REFERENCES course_master(course_id)
);

--------------------------------------------------
-- COURSE OBJECTIVES
--------------------------------------------------

CREATE TABLE course_objectives (
    obj_id NUMBER GENERATED AS IDENTITY PRIMARY KEY,
    course_id NUMBER,
    description VARCHAR2(1000),
    print_seq NUMBER,
    CONSTRAINT fk_obj_course FOREIGN KEY (course_id) REFERENCES course_master(course_id)
);

--------------------------------------------------
-- COURSE OUTCOMES
--------------------------------------------------

CREATE TABLE course_outcomes (
    outcome_id NUMBER GENERATED AS IDENTITY PRIMARY KEY,
    course_id NUMBER,
    outcome_desc VARCHAR2(1000),
    print_seq NUMBER,
    CONSTRAINT fk_out_course FOREIGN KEY (course_id) REFERENCES course_master(course_id)
);

--------------------------------------------------
-- COURSE DESCRIPTION
--------------------------------------------------

CREATE TABLE course_description (
    desc_id NUMBER GENERATED AS IDENTITY PRIMARY KEY,
    course_id NUMBER,
    topic VARCHAR2(1000),
    duration_weeks NUMBER,
    CONSTRAINT fk_desc_course FOREIGN KEY (course_id) REFERENCES course_master(course_id)
);

--------------------------------------------------
-- TEXT BOOKS
--------------------------------------------------

CREATE TABLE text_books (
    book_id NUMBER GENERATED AS IDENTITY PRIMARY KEY,
    course_id NUMBER,
    title VARCHAR2(300),
    type VARCHAR2(50),
    CONSTRAINT fk_text_course FOREIGN KEY (course_id) REFERENCES course_master(course_id)
);

--------------------------------------------------
-- REFERENCE BOOKS
--------------------------------------------------

CREATE TABLE reference_books (
    ref_id NUMBER GENERATED AS IDENTITY PRIMARY KEY,
    course_id NUMBER,
    title VARCHAR2(300),
    type VARCHAR2(50),
    CONSTRAINT fk_ref_course FOREIGN KEY (course_id) REFERENCES course_master(course_id)
);

CREATE TABLE course_instance (
    instance_id NUMBER GENERATED AS IDENTITY PRIMARY KEY,
    course_id NUMBER,
    faculty_id NUMBER,
    academic_session VARCHAR2(20),
    semester NUMBER,
    section VARCHAR2(10),
    batch VARCHAR2(10),
    slot VARCHAR2(10),
    CONSTRAINT fk_instance_course FOREIGN KEY (course_id) REFERENCES course_master(course_id),
    CONSTRAINT fk_instance_faculty FOREIGN KEY (faculty_id) REFERENCES faculty(faculty_id)
);

--------------------------------------------------
-- STUDENT REGISTRATION (Main Entry)
--------------------------------------------------

CREATE TABLE student_registration (
    reg_id NUMBER GENERATED AS IDENTITY PRIMARY KEY,
    student_id NUMBER,
    semester NUMBER,
    academic_session VARCHAR2(20),
    status VARCHAR2(20) DEFAULT 'SUBMITTED' CHECK (status IN ('SUBMITTED', 'APPROVED', 'REJECTED')),
    registration_date DATE DEFAULT SYSDATE,
    CONSTRAINT fk_reg_student FOREIGN KEY (student_id) REFERENCES students(student_id)
);

--------------------------------------------------
-- REGISTERED COURSES (Courses in a registration)
--------------------------------------------------

CREATE TABLE student_registration_courses (
    id NUMBER GENERATED AS IDENTITY PRIMARY KEY,
    reg_id NUMBER,
    course_instance_id NUMBER,
    course_type VARCHAR2(5),
    CONSTRAINT fk_src_reg FOREIGN KEY (reg_id) REFERENCES student_registration(reg_id),
    CONSTRAINT fk_src_instance FOREIGN KEY (course_instance_id) REFERENCES course_instance(instance_id)
);

--------------------------------------------------
-- RESULTS
--------------------------------------------------

CREATE TABLE results (
    result_id NUMBER GENERATED AS IDENTITY PRIMARY KEY,
    student_id NUMBER,
    course_id NUMBER,
    academic_session VARCHAR2(20),
    grade NUMBER(5,2), 
    grade_letter VARCHAR2(5),
    CONSTRAINT fk_result_student FOREIGN KEY (student_id) REFERENCES students(student_id),
    CONSTRAINT fk_result_course FOREIGN KEY (course_id) REFERENCES course_master(course_id)
);

--------------------------------------------------
-- ATTENDANCE
--------------------------------------------------

CREATE TABLE attendance (
    attendance_id NUMBER GENERATED AS IDENTITY PRIMARY KEY,
    student_id NUMBER,
    course_instance_id NUMBER,
    attendance_percentage NUMBER(5,2),
    updated_date DATE DEFAULT SYSDATE,
    CONSTRAINT fk_att_student FOREIGN KEY (student_id) REFERENCES students(student_id),
    CONSTRAINT fk_att_instance FOREIGN KEY (course_instance_id) REFERENCES course_instance(instance_id)
);

--------------------------------------------------
-- COORDINATOR / ADVISOR
--------------------------------------------------

CREATE TABLE coordinator (
    id NUMBER GENERATED AS IDENTITY PRIMARY KEY,
    faculty_id NUMBER, 
    student_id NUMBER, 
    academic_session VARCHAR2(20),
    CONSTRAINT fk_coord_faculty FOREIGN KEY (faculty_id) REFERENCES faculty(faculty_id),
    CONSTRAINT fk_coord_student FOREIGN KEY (student_id) REFERENCES students(student_id)
);

--------------------------------------------------
-- NEW TABLES FOR PHASE 2/3
--------------------------------------------------

-- 1. Program Outcomes (PO)
CREATE TABLE program_outcomes (
    po_id NUMBER GENERATED AS IDENTITY PRIMARY KEY,
    po_code VARCHAR2(10) UNIQUE,
    po_description VARCHAR2(1000)
);

-- 2. CO-PO Mapping (Heatmap data)
CREATE TABLE co_po_mapping (
    id NUMBER GENERATED AS IDENTITY PRIMARY KEY,
    course_outcome_id NUMBER,
    program_outcome_id NUMBER,
    weightage NUMBER(3) CHECK (weightage BETWEEN 0 AND 3),
    CONSTRAINT fk_copo_co FOREIGN KEY (course_outcome_id) REFERENCES course_outcomes(outcome_id) ON DELETE CASCADE,
    CONSTRAINT fk_copo_po FOREIGN KEY (program_outcome_id) REFERENCES program_outcomes(po_id) ON DELETE CASCADE
);

-- 3. Evaluation Details (Weights for Midsem/Endsem/Quiz)
CREATE TABLE evaluation_details (
    eval_id NUMBER GENERATED AS IDENTITY PRIMARY KEY,
    course_id NUMBER,
    component_name VARCHAR2(100), -- E.g., 'Mid-Sem', 'End-Sem', 'Practical'
    weightage_percent NUMBER(5,2),
    CONSTRAINT fk_eval_course FOREIGN KEY (course_id) REFERENCES course_master(course_id) ON DELETE CASCADE
);

-- 4. Course Equivalents (For credit transfer/alternate options)
CREATE TABLE course_equivalents (
    id NUMBER GENERATED AS IDENTITY PRIMARY KEY,
    course_id NUMBER,
    equivalent_course_id NUMBER,
    CONSTRAINT fk_ceq_course FOREIGN KEY (course_id) REFERENCES course_master(course_id) ON DELETE CASCADE,
    CONSTRAINT fk_ceq_equiv FOREIGN KEY (equivalent_course_id) REFERENCES course_master(course_id) ON DELETE CASCADE
);

-- Seed Admin User (Temporary Login: admin / admin123)
-- In production, the password_hash will be verified.
INSERT INTO users (user_id, login_id, password_hash, role) 
VALUES (USERS_SEQ.NEXTVAL, 'admin', 'pbkdf2:sha256:600000$Jp9yN3m9$9f24ce7b8b4c0607d72111160352062534568853b4789508546b38c29377488c', 'admin');

-- Seed initial POs
INSERT INTO program_outcomes (po_code, po_description) VALUES ('PO1', 'Engineering Knowledge');
INSERT INTO program_outcomes (po_code, po_description) VALUES ('PO2', 'Problem Analysis');

COMMIT;