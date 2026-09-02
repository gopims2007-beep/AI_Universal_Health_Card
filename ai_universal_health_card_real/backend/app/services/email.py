import smtplib
from email.message import EmailMessage
from app.core.config import settings

def send_email(to_email: str, subject: str, body: str) -> bool:
    if not all([settings.smtp_host, settings.smtp_username, settings.smtp_password, settings.smtp_from]):
        # Development fallback: do not pretend an email was sent.
        print(f"[EMAIL NOT CONFIGURED] To={to_email} Subject={subject}\n{body}")
        return False

    msg = EmailMessage()
    msg["From"] = settings.smtp_from
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as smtp:
        if settings.smtp_tls:
            smtp.starttls()
        smtp.login(settings.smtp_username, settings.smtp_password)
        smtp.send_message(msg)
    return True
