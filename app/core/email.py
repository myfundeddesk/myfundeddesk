import os
import resend

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY

FROM_EMAIL = os.getenv("FROM_EMAIL", "onboarding@resend.dev")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "myfundeddesk@gmail.com")

def send_email(to_email: str, subject: str, body: str):
    if not RESEND_API_KEY:
        print(f"--- MOCK EMAIL TO {to_email} ---")
        print(f"Subject: {subject}")
        print(f"Body:\n{body}")
        print("---------------------------------")
        return True

    try:
        r = resend.Emails.send({
            "from": FROM_EMAIL,
            "to": to_email,
            "subject": subject,
            "html": body
        })
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False
