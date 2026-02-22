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
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="utf-8">
        <style>
          .container {{
            max-width: 600px;
            margin: 0 auto;
            padding: 40px 20px;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            color: #1a1a1a;
            background-color: #f9fafb;
          }}
          .card {{
            background: #ffffff;
            border-radius: 16px;
            padding: 40px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            border: 1px solid #e5e7eb;
          }}
          .logo {{
            text-align: center;
            margin-bottom: 32px;
          }}
          .logo-text {{
            font-size: 24px;
            font-weight: 800;
            letter-spacing: -0.025em;
            color: #111827;
            text-transform: uppercase;
          }}
          .logo-highlight {{
            color: #6366f1;
          }}
          h2 {{
            margin: 0 0 16px;
            font-size: 24px;
            font-weight: 700;
            color: #111827;
            text-align: center;
          }}
          p {{
            margin: 0 0 24px;
            font-size: 16px;
            line-height: 1.6;
            color: #4b5563;
          }}
          .token-box {{
            background: #f3f4f6;
            padding: 24px;
            border-radius: 12px;
            font-family: 'JetBrains Mono', 'Fira Code', monospace;
            font-size: 20px;
            font-weight: 700;
            text-align: center;
            letter-spacing: 0.1em;
            color: #111827;
            margin: 32px 0;
            border: 2px dashed #d1d5db;
          }}
          .button-container {{
            text-align: center;
            margin: 32px 0;
          }}
          .button {{
            background-color: #6366f1;
            color: #ffffff !important;
            padding: 16px 32px;
            text-decoration: none;
            border-radius: 8px;
            font-weight: 600;
            display: inline-block;
            transition: background-color 0.2s;
          }}
          .footer {{
            margin-top: 32px;
            padding-top: 24px;
            border-top: 1px solid #e5e7eb;
            font-size: 14px;
            color: #9ca3af;
            text-align: center;
          }}
        </style>
      </head>
      <body>
        <div class="container">
          <div class="card">
            <div class="logo">
              <span class="logo-text">GYM<span class="logo-highlight">PRO</span></span>
            </div>
            <h2>Reset Your Password</h2>
            <p>Hello,</p>
            <p>We received a request to reset your password. Use the secure token below to proceed:</p>
            
            <div class="token-box">
              {token}
            </div>
            
            <div class="button-container">
              <a href="{reset_link}" class="button">Reset Password</a>
            </div>
            
            <p style="font-size: 14px;">If the button doesn't work, you can copy and paste this link into your browser:</p>
            <p style="font-size: 12px; word-break: break-all; color: #6366f1;">{reset_link}</p>
            
            <div class="footer">
              <p>This token will expire in 1 hour. If you didn't request this, you can safely ignore this email.</p>
              &copy; 2026 GymPro. All rights reserved.
            </div>
          </div>
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
