import os
import resend
from datetime import datetime
from app.config import RESEND_API_KEY, RESEND_FROM_EMAIL

resend.api_key = RESEND_API_KEY or os.getenv("RESEND_API_KEY", "")

def send_activity_email(user_email: str, subject: str, headline: str, message: str, request_info: dict = None):
    if not resend.api_key:
        print("Warning: RESEND_API_KEY not set. Cannot send activity email.")
        return False
        
    info_html = ""
    if request_info:
        info_html = "<ul>"
        for k, v in request_info.items():
            info_html += f"<li><strong>{k}:</strong> {v}</li>"
        info_html += "</ul>"

    html_content = f"""
    <div style="font-family: sans-serif; max-w-md: 600px; margin: 0 auto; padding: 20px; background: #f8fafc; border-radius: 12px;">
        <h2 style="color: #0f172a; margin-bottom: 10px;">{headline}</h2>
        <p style="color: #475569; font-size: 15px; line-height: 1.5;">
            {message}
        </p>
        
        <div style="margin-top: 20px; padding: 15px; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; color: #64748b; font-size: 13px;">
            <p style="margin-top: 0; font-weight: bold;">Activity Security Log:</p>
            {info_html}
            <p style="margin-bottom: 0;">Time (UTC): {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <p style="color: #94a3b8; font-size: 11px; margin-top: 30px;">
            If this was not you, please immediately reset your password or contact MyFundedDesk support.
        </p>
    </div>
    """
    
    try:
        resend.Emails.send({
            "from": RESEND_FROM_EMAIL,
            "to": user_email,
            "subject": subject,
            "html": html_content
        })
        return True
    except Exception as e:
        print(f"[Email Error] {e}")
        return False
