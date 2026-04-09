# 🎓 VNIT Course Registration & Academic Portal

A professional-grade academic management system designed to streamline the student registration lifecycle, advisor approvals, and performance tracking at VNIT Nagpur.

![License](https://img.shields.io/badge/License-MIT-blue.svg)
![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Framework-Flask-red.svg)
![Database](https://img.shields.io/badge/Database-Oracle%20XE-orange.svg)

## 🌟 Key Features
- **Multi-Role Dashboards:** Specialized interfaces for Students, Faculty (Advisors), and Administrators.
- **Academic Engine:** 
  - Enforces DC (Departmental Core) and DE (Departmental Elective) selection rules.
  - Automatically identifies Backlogs and checks Prerequisites.
  - Real-time CGPA calculation and attendance progress tracking.
- **Outcome-Based Education (OBE):** Integrated mapping for Course Outcomes (CO) to Program Outcomes (PO) for NBA/NAAC compliance.
- **Automated Documents:** Dynamic generation of formatted Registration PDFs using ReportLab.
- **Administrative Control:** Manage session configurations, faculty assignments, and syllabus descriptions.
- **Architectural Transparency:** Built-in interactive ER diagram showing the 21-table schema.

## 🎨 Visual Excellence
The portal features a premium **Glassmorphism UI** with:
- Outfit typography for maximum readability.
- Micro-animations for smooth transitions.
- Responsive layouts for cross-device compatibility.
- Interactive data visualizations for academic progress.

## 🛠️ Tech Stack
- **Backend:** Python (Flask)
- **Database:** Oracle Database Express Edition (XE)
- **Frontend:** HTML5, CSS3, JavaScript (Vanilla), Bootstrap 5
- **Reporting:** ReportLab (PDF Generation)
- **Environment:** Dotenv for secure configuration

## 📊 Database Architecture
The system is built on a robust Oracle schema featuring:
- **21+ Normalized Tables**
- Multi-tenant relationships (Students ↔ Advisors ↔ Courses)
- Comprehensive Syllabus & Evaluation management

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Oracle Database Express Edition (XE)
- **Optional:** Docker & Docker Compose

### Option 1: Manual Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/Lalitha0421/course-registration-portal123.git
   cd course-registration-portal123
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/Scripts/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables in `.env`.

5. Launch the application:
   ```bash
   python app.py
   ```

### Option 2: Docker Deployment (Recommended)
This is the easiest way to launch the portal along with a pre-configured Oracle XE database.

1. Install [Docker Desktop](https://www.docker.com/products/docker-desktop/).
2. Run the deployment command:
   ```bash
   docker-compose up --build -d
   ```
3. The app will be available at `http://localhost:5000`. 
   The database will automatically initialize using scripts in `/sql`.

---
*Built with ❤️ for VNIT Nagpur.*
