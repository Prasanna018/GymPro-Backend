import smtplib
import anyio
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "").replace(" ", "").strip()

async def send_reset_email(to_email: str, token: str):
    if not SMTP_USER or not SMTP_PASSWORD:
        print("\n[WARNING] SMTP credentials not configured. Email not sent.")
        print(f"[DEBUG] Password reset token for {to_email}: {token}\n")
        return False

    reset_link = f"https://gym-pro-ten.vercel.app/reset-password?token={token}"
    
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Reset Your GymPro Password"
    msg["From"] = f"GymPro Support <{SMTP_USER}>"
    msg["To"] = to_email

    text = f"""
    Hello,

    You requested a password reset for your GymPro account.
    Please use the following token to reset your password:

    {token}

    Or click the link below to proceed:
    {reset_link}

    This token will expire in 1 hour.
    If you did not request this, please ignore this email.

    Regards,
    GymPro Team
    """

    html = f"""
    <html>
      <body style="font-family: sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #eee; border-radius: 10px;">
          <h2 style="color: #6366f1;">Reset Your Password</h2>
          <p>Hello,</p>
          <p>You requested a password reset for your GymPro account. Please use the token below to reset your password:</p>
          <div style="background: #f4f4f9; padding: 15px; border-radius: 5px; font-family: monospace; font-size: 1.2em; text-align: center; margin: 20px 0;">
            <strong>{token}</strong>
          </div>
          <p>Or click the button below to proceed to the reset page:</p>
          <div style="text-align: center; margin: 30px 0;">
            <a href="{reset_link}" style="background: #6366f1; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold;">Reset Password</a>
          </div>
          <p style="font-size: 0.8em; color: #666; margin-top: 40px; border-top: 1px solid #eee; padding-top: 20px;">
            This token will expire in 1 hour. If you did not request this, please ignore this email.
          </p>
        </div>
      </body>
    </html>
    """

    msg.attach(MIMEText(text, "plain"))
    msg.attach(MIMEText(html, "html"))

    def _send():
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)

    try:
        await anyio.to_thread.run_sync(_send)
        print(f"✅ Reset email sent successfully to {to_email}")
        return True
    except Exception as e:
        print(f"❌ Failed to send email to {to_email}: {str(e)}")
        # Fallback to console for debugging
        print(f"[DEBUG] Password reset token for {to_email}: {token}\n")
        return False
