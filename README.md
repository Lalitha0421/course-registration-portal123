# 🎓 VNIT Course Registration & Academic Portal

A professional-grade academic management system designed to streamline the student registration lifecycle, advisor approvals, and performance tracking at VNIT Nagpur. Built with a robust **Oracle XE** backend and a modern **Flask** architecture.

![License](https://img.shields.io/badge/License-MIT-blue.svg)
![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Framework-Flask-red.svg)
![Database](https://img.shields.io/badge/Database-Oracle%20XE-orange.svg)
![Architecture](https://img.shields.io/badge/Schema-21%2B%20Tables-green.svg)

## 🌟 Key Features

### 👨‍🎓 Student Lifecycle Management
- **Smart Registration:** Enforces DC (Departmental Core) and DE (Departmental Elective) selection rules.
- **Academic Auditing:** Automatically identifies Backlogs and validates Prerequisites in real-time.
- **Progress Tracking:** Interactive dashboards for CGPA calculation and attendance monitoring.
- **Document Generation:** Dynamic PDF generation for Registration Forms using ReportLab.

### 👨‍🏫 Faculty & Advisor Suite
- **Advisory Dashboard:** Dedicated interface for managing coordinated students and course approvals.
- **Daily Attendance Grid:** A specialized grid interface for high-resolution attendance tracking (Present/Absent).
- **Grading Engine:** Comprehensive result entry system with Oracle-backed data integrity.
- **Syllabus Management:** Integrated tools for defining Course Objectives, Outcomes (COs), and Weekly Descriptions.

### 🛡️ Administrative Control
- **Session Management:** Configure academic sessions, course instances, and faculty assignments.
- **System Monitoring:** Debug dashboards for verifying database table counts and session integrity.
- **Academic Catalog:** Centralized management of the master course database.

## 📊 Technical Architecture

The system is built on a highly normalized **Oracle Database** schema featuring **21+ tables**.

### Database Highlights:
- **Relational Integrity:** Complex multi-tenant relationships between Students, Advisors, Faculty, and Course Instances.
- **Outcome-Based Education (OBE):** Schema support for Course Outcomes (CO) to Program Outcomes (PO) mapping.
- **Efficient Upserts:** Utilizes Oracle `MERGE` statements for high-performance attendance and grading updates.
- **ER Transparency:** Includes a built-in interactive ER diagram generated via Mermaid.js.

## 🎨 Design Aesthetics
- **UI/UX:** Premium **Glassmorphism** interface with Outfit typography.
- **Interactivity:** Smooth micro-animations and responsive layouts built with Vanilla CSS and Bootstrap 5.
- **Real-time Feedback:** Toast notifications and dynamic progress bars for better UX.

## 🚀 Getting Started

### Prerequisites
- **Python 3.8+**
- **Oracle Database Express Edition (XE)**
- **cx_Oracle / python-oracledb** drivers.

### Quick Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Lalitha0421/course-registration-portal123.git
   cd course-registration-portal123
   ```

2. **Setup Virtual Environment:**
   ```bash
   python -m venv venv
   source venv/Scripts/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration:**
   Create a `.env` file with your Oracle credentials:
   ```env
   DB_USER=your_user
   DB_PASSWORD=your_password
   DB_DSN=localhost:1521/xe
   SECRET_KEY=your_secret_key
   ```

5. **Initialize Database:**
   Run the provided scripts in `/sql` or use `create_demo_db.py` for a quick setup.

6. **Run App:**
   ```bash
   python app.py
   ```

### Docker Deployment (Recommended)
Launch the entire stack (App + Oracle XE) with a single command:
```bash
docker-compose up --build -d
```

---
*Built for excellence at VNIT Nagpur.*
