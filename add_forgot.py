with open("app/routers/admin_dashboard.py", "r", encoding="utf-8") as f:
    text = f.read()

forgot_route = """
@router.post("/admin/forgot-password")
async def admin_forgot_password(request: Request):
    try:
        from app.core.email import send_admin_otp_email
        # We reuse the SMTP setup from send_admin_otp_email to send the password.
        # But wait, send_admin_otp_email takes (to_email, otp). We can just pass the password as the "OTP" 
        # or craft a specific email. Let's just use it to send the password!
        subject = "Admin Password Recovery - PropLab"
        body = f"Your admin password is: {ADMIN_PASSWORD}"
        
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        import os

        smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", 587))
        smtp_user = os.getenv("SMTP_USER")
        smtp_pass = os.getenv("SMTP_PASS")
        
        if not smtp_user or not smtp_pass:
            # Fallback for dev if no SMTP
            print(f"Admin Recovery Triggered. Password is: {ADMIN_PASSWORD}")
            return JSONResponse({"success": True})
            
        msg = MIMEMultipart()
        msg["From"] = smtp_user
        msg["To"] = ADMIN_USERNAME
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
        server.quit()
        
        return JSONResponse({"success": True})
    except Exception as e:
        print("Error sending admin recovery:", e)
        return JSONResponse({"success": False, "error": str(e)})
"""

if "/admin/forgot-password" not in text:
    text += "\n" + forgot_route
    with open("app/routers/admin_dashboard.py", "w", encoding="utf-8") as f:
        f.write(text)
    print("Added /admin/forgot-password route")
