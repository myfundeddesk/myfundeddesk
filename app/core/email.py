import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@myfundeddesk.com")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "myfundeddesk@gmail.com") # Default admin email

def send_email(to_email: str, subject: str, body: str):
    if not SMTP_USER or not SMTP_PASS:
        print(f"--- MOCK EMAIL TO {to_email} ---")
        print(f"Subject: {subject}")
        print(f"Body:\n{body}")
        print("---------------------------------")
        return True

    msg = MIMEMultipart()
    msg['From'] = FROM_EMAIL
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html'))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

