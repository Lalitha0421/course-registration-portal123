--------------------------------------------------
-- DROP TABLES
--------------------------------------------------

BEGIN EXECUTE IMMEDIATE 'DROP TABLE attendance CASCADE CONSTRAINTS'; EXCEPTION WHEN OTHERS THEN NULL; END;
/
BEGIN EXECUTE IMMEDIATE 'DROP TABLE results CASCADE CONSTRAINTS'; EXCEPTION WHEN OTHERS THEN NULL; END;
/
BEGIN EXECUTE IMMEDIATE 'DROP TABLE registration_courses CASCADE CONSTRAINTS'; EXCEPTION WHEN OTHERS THEN NULL; END;
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

--------------------------------------------------
-- USERS
--------------------------------------------------

CREATE TABLE users (
    user_id NUMBER PRIMARY KEY,
    login_id VARCHAR2(50) UNIQUE NOT NULL,
    password_hash VARCHAR2(200) NOT NULL,
    role VARCHAR2(20) CHECK (role IN ('student','faculty','admin')),
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
    student_id NUMBER PRIMARY KEY,
    user_id NUMBER UNIQUE,
    enrollment_no VARCHAR2(20) UNIQUE,
    name VARCHAR2(100),
    email VARCHAR2(100),
    mobile VARCHAR2(20),
    semester NUMBER,
    program VARCHAR2(50),
    advisor_id NUMBER,
    CONSTRAINT fk_student_user FOREIGN KEY (user_id) REFERENCES users(user_id),
    CONSTRAINT fk_student_advisor FOREIGN KEY (advisor_id) REFERENCES faculty(faculty_id)
);

--------------------------------------------------
-- COURSE MASTER
--------------------------------------------------

CREATE TABLE course_master (
    course_id NUMBER PRIMARY KEY,
    course_code VARCHAR2(20) UNIQUE,
    course_title VARCHAR2(200),
    course_type VARCHAR2(10),
    program VARCHAR2(100),
    L NUMBER,
    T NUMBER,
    P NUMBER,
    credits NUMBER
);

--------------------------------------------------
-- COURSE PREREQUISITES
--------------------------------------------------

CREATE TABLE course_prerequisites (
    id NUMBER PRIMARY KEY,
    course_id NUMBER,
    prerequisite_course_id NUMBER,
    CONSTRAINT fk_pr_course FOREIGN KEY (course_id) REFERENCES course_master(course_id),
    CONSTRAINT fk_prereq_course FOREIGN KEY (prerequisite_course_id) REFERENCES course_master(course_id)
);

--------------------------------------------------
-- COURSE OBJECTIVES
--------------------------------------------------

CREATE TABLE course_objectives (
    obj_id NUMBER PRIMARY KEY,
    course_id NUMBER,
    description VARCHAR2(500),
    print_seq NUMBER,
    CONSTRAINT fk_obj_course FOREIGN KEY (course_id) REFERENCES course_master(course_id)
);

--------------------------------------------------
-- COURSE OUTCOMES
--------------------------------------------------

CREATE TABLE course_outcomes (
    outcome_id NUMBER PRIMARY KEY,
    course_id NUMBER,
    outcome_desc VARCHAR2(500),
    print_seq NUMBER,
    CONSTRAINT fk_out_course FOREIGN KEY (course_id) REFERENCES course_master(course_id)
);

--------------------------------------------------
-- COURSE DESCRIPTION
--------------------------------------------------

CREATE TABLE course_description (
    desc_id NUMBER PRIMARY KEY,
    course_id NUMBER,
    topic VARCHAR2(500),
    duration_weeks NUMBER,
    CONSTRAINT fk_desc_course FOREIGN KEY (course_id) REFERENCES course_master(course_id)
);

--------------------------------------------------
-- TEXT BOOKS
--------------------------------------------------

CREATE TABLE text_books (
    book_id NUMBER PRIMARY KEY,
    course_id NUMBER,
    title VARCHAR2(200),
    type VARCHAR2(50),
    CONSTRAINT fk_text_course FOREIGN KEY (course_id) REFERENCES course_master(course_id)
);

--------------------------------------------------
-- REFERENCE BOOKS
--------------------------------------------------

CREATE TABLE reference_books (
    ref_id NUMBER PRIMARY KEY,
    course_id NUMBER,
    title VARCHAR2(200),
    type VARCHAR2(50),
    CONSTRAINT fk_ref_course FOREIGN KEY (course_id) REFERENCES course_master(course_id)
);

--------------------------------------------------
-- COURSE INSTANCE
--------------------------------------------------

CREATE TABLE course_instance (
    instance_id NUMBER PRIMARY KEY,
    course_id NUMBER,
    faculty_id NUMBER,
    academic_session VARCHAR2(20),
    semester NUMBER,
    CONSTRAINT fk_instance_course FOREIGN KEY (course_id) REFERENCES course_master(course_id),
    CONSTRAINT fk_instance_faculty FOREIGN KEY (faculty_id) REFERENCES faculty(faculty_id)
);

--------------------------------------------------
-- STUDENT REGISTRATION
--------------------------------------------------

CREATE TABLE student_registration (
    reg_id NUMBER PRIMARY KEY,
    student_id NUMBER,
    semester NUMBER,
    academic_session VARCHAR2(20),
    registration_date DATE,
    CONSTRAINT fk_reg_student FOREIGN KEY (student_id) REFERENCES students(student_id)
);

--------------------------------------------------
-- REGISTERED COURSES
--------------------------------------------------

CREATE TABLE registration_courses (
    id NUMBER PRIMARY KEY,
    reg_id NUMBER,
    course_instance_id NUMBER,
    course_type VARCHAR2(5),
    CONSTRAINT fk_regcourse_reg FOREIGN KEY (reg_id) REFERENCES student_registration(reg_id),
    CONSTRAINT fk_regcourse_instance FOREIGN KEY (course_instance_id) REFERENCES course_instance(instance_id)
);

--------------------------------------------------
-- RESULTS
--------------------------------------------------

CREATE TABLE results (
    result_id NUMBER PRIMARY KEY,
    student_id NUMBER,
    course_id NUMBER,
    grade VARCHAR2(5),
    CONSTRAINT fk_result_student FOREIGN KEY (student_id) REFERENCES students(student_id),
    CONSTRAINT fk_result_course FOREIGN KEY (course_id) REFERENCES course_master(course_id)
);

--------------------------------------------------
-- ATTENDANCE
--------------------------------------------------

CREATE TABLE attendance (
    attendance_id NUMBER PRIMARY KEY,
    student_id NUMBER,
    course_instance_id NUMBER,
    attendance_percentage NUMBER,
    CONSTRAINT fk_att_student FOREIGN KEY (student_id) REFERENCES students(student_id),
    CONSTRAINT fk_att_instance FOREIGN KEY (course_instance_id) REFERENCES course_instance(instance_id)
);

--------------------------------------------------
-- COORDINATOR
--------------------------------------------------

CREATE TABLE coordinator (
    id NUMBER PRIMARY KEY,
    course_id NUMBER,
    faculty_id NUMBER,
    CONSTRAINT fk_coord_course FOREIGN KEY (course_id) REFERENCES course_master(course_id),
    CONSTRAINT fk_coord_faculty FOREIGN KEY (faculty_id) REFERENCES faculty(faculty_id)
);





-- CREATE TABLE STUDENT_APPLICATION
-- (
--     APP_ID NUMBER PRIMARY KEY,
--     NAME VARCHAR2(100),
--     EMAIL VARCHAR2(100),
--     MOBILE VARCHAR2(20),
--     PROGRAM VARCHAR2(50),
--     SEMESTER NUMBER,
--     APPLICATION_DATE DATE
-- );