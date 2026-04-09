import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

# Load credentials from .env
load_dotenv()

def send_email(to_email, subject, body):
    """
    To enable REAL emails:
    1. Create a Google App Password (if using Gmail)
    2. Add these to your .env file:
       SENDER_EMAIL=your_email@gmail.com
       SENDER_PASSWORD=your_app_password
    """
    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("SENDER_PASSWORD")

    if not sender_email or not sender_password:
        # FALLBACK: Simulation Mode (Prints to terminal)
        print(f"\n[EMAIL SIMULATION] »»»»»»»»»»»»»»»»»»»»»»»»")
        print(f"TO:      {to_email}")
        print(f"SUBJECT: {subject}")
        print(f"MESSAGE: {body}")
        print(f"««««««««««««««««««««««««««««««««««««««\n")
        return True

    # Real SMTP Logic
    try:
        smtp_server = "smtp.gmail.com"
        smtp_port = 587

        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = to_email
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(message)
        print(f"SUCCESS: Real email sent to {to_email}")
        return True
    except Exception as e:
        print(f"ERROR: Failed to send real email: {e}")
        return False

def notify_student_approval(student_name, student_email, enrollment_no, password):
    subject = "VNIT Course Portal - Application Approved"
    body = f"""Dear {student_name},

Congratulations! Your application to the VNIT Course Portal has been approved.

Your login credentials are provided below:
Enrollment Number: {enrollment_no}
Temporary Password: {password}

Please login at the portal and change your password immediately.

Regards,
Admin Team
VNIT Nagpur
"""
    return send_email(student_email, subject, body)

def notify_registration_approval(student_name, student_email, academic_session):
    subject = "VNIT Course Portal - Course Registration Approved"
    body = f"""Dear {student_name},

Your course registration for the session {academic_session} has been approved by the admin.

You can now login to the portal and download your final registration PDF.

Regards,
Admin Team
VNIT Nagpur
"""
    return send_email(student_email, subject, body)
