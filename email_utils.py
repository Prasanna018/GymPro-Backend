import os
import httpx
from dotenv import load_dotenv

load_dotenv()

# Email Configuration (Resend API)
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
FROM_EMAIL = os.getenv("FROM_EMAIL", "onboarding@resend.dev")

async def send_reset_email(to_email: str, token: str):
    if not RESEND_API_KEY:
        print("\n[WARNING] RESEND_API_KEY not configured. Email not sent.")
        print(f"[DEBUG] Password reset token for {to_email}: {token}\n")
        return False

    reset_link = f"https://gym-pro-ten.vercel.app/reset-password?token={token}"
    
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
            
            body {
                margin: 0;
                padding: 0;
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background-color: #f4f7fa;
                color: #1a1f36;
            }
            .wrapper {
                width: 100%;
                table-layout: fixed;
                background-color: #f4f7fa;
                padding-bottom: 40px;
                padding-top: 40px;
            }
            .content {
                max-width: 600px;
                margin: 0 auto;
                background-color: #ffffff;
                border-radius: 16px;
                overflow: hidden;
                box-shadow: 0 10px 25px rgba(0,0,0,0.05);
            }
            .header {
                background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
                padding: 40px 20px;
                text-align: center;
            }
            .header h1 {
                margin: 0;
                color: #ffffff;
                font-size: 28px;
                font-weight: 800;
                letter-spacing: -0.025em;
                text-transform: uppercase;
            }
            .header h1 span {
                color: rgba(255, 255, 255, 0.7);
            }
            .body {
                padding: 40px;
                text-align: center;
            }
            .body h2 {
                margin-top: 0;
                font-size: 24px;
                font-weight: 700;
                color: #111827;
                margin-bottom: 16px;
            }
            .body p {
                font-size: 16px;
                line-height: 1.6;
                color: #4b5563;
                margin-bottom: 24px;
            }
            .token-container {
                background-color: #f8fafc;
                border: 2px dashed #e2e8f0;
                border-radius: 12px;
                padding: 24px;
                margin: 32px 0;
            }
            .token-label {
                font-size: 12px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.1em;
                color: #64748b;
                margin-bottom: 8px;
            }
            .token-value {
                font-family: 'JetBrains Mono', 'Fira Code', monospace;
                font-size: 32px;
                font-weight: 800;
                color: #4f46e5;
                letter-spacing: 0.25em;
            }
            .cta-button {
                display: inline-block;
                background-color: #4f46e5;
                color: #ffffff !important;
                padding: 16px 32px;
                border-radius: 8px;
                text-decoration: none;
                font-weight: 700;
                font-size: 16px;
                transition: background-color 0.2s;
                box-shadow: 0 4px 6px -1px rgba(79, 70, 229, 0.2);
            }
            .footer {
                padding: 32px 40px;
                background-color: #f8fafc;
                text-align: center;
                font-size: 14px;
                color: #94a3b8;
                border-top: 1px solid #f1f5f9;
            }
            .footer p {
                margin: 8px 0;
            }
            .link-alt {
                font-size: 12px;
                color: #94a3b8;
                margin-top: 24px;
                word-break: break-all;
            }
            .link-alt a {
                color: #4f46e5;
                text-decoration: none;
            }
        </style>
    </head>
    <body>
        <div class="wrapper">
            <div class="content">
                <div class="header">
                    <h1>GYM<span>PRO</span></h1>
                </div>
                <div class="body">
                    <h2>Reset Your Password</h2>
                    <p>Hello,</p>
                    <p>We received a request to access your GymPro account. Use the secure token below to reset your password. This token will expire in 60 minutes.</p>
                    
                    <div class="token-container">
                        <div class="token-label">Your Reset Token</div>
                        <div class="token-value">{{TOKEN}}</div>
                    </div>
                    
                    <a href="{{LINK}}" class="cta-button">Reset My Password</a>
                    
                    <div class="link-alt">
                        If the button doesn't work, copy and paste this link into your browser:<br>
                        <a href="{{LINK}}">{{LINK}}</a>
                    </div>
                </div>
                <div class="footer">
                    <p>If you did not request this email, you can safely ignore it.</p>
                    <p>&copy; 2026 GymPro. All rights reserved.</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """.replace("{{TOKEN}}", token).replace("{{LINK}}", reset_link)

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {RESEND_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "from": FROM_EMAIL,
                    "to": to_email,
                    "subject": "Reset Your GymPro Password",
                    "html": html,
                },
                timeout=10.0
            )
            
            if response.status_code in [200, 201]:
                print(f"✅ Reset email sent successfully to {to_email}")
                return True
            else:
                print(f"❌ Resend API Error: {response.text}")
                # Fallback to console
                print(f"[DEBUG] Password reset token for {to_email}: {token}\n")
                return False
                
    except Exception as e:
        print(f"❌ Failed to send email via Resend: {str(e)}")
        # Fallback to console for debugging
        print(f"[DEBUG] Password reset token for {to_email}: {token}\n")
        return False

async def send_reminder_email(to_email: str, member_name: str, subject: str, message_text: str, button_text: str = "View Details"):
    if not RESEND_API_KEY:
        print(f"\n[WARNING] RESEND_API_KEY not configured. Reminder not sent to {to_email}")
        return False

    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
            
            body {
                margin: 0;
                padding: 0;
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background-color: #f4f7fa;
                color: #1a1f36;
            }
            .wrapper {
                width: 100%;
                table-layout: fixed;
                background-color: #f4f7fa;
                padding-bottom: 40px;
                padding-top: 40px;
            }
            .content {
                max-width: 600px;
                margin: 0 auto;
                background-color: #ffffff;
                border-radius: 16px;
                overflow: hidden;
                box-shadow: 0 10px 25px rgba(0,0,0,0.05);
            }
            .header {
                background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
                padding: 40px 20px;
                text-align: center;
            }
            .header h1 {
                margin: 0;
                color: #ffffff;
                font-size: 28px;
                font-weight: 800;
                letter-spacing: -0.025em;
                text-transform: uppercase;
            }
            .header h1 span {
                color: rgba(255, 255, 255, 0.7);
            }
            .body {
                padding: 40px;
                text-align: center;
            }
            .body h2 {
                margin-top: 0;
                font-size: 24px;
                font-weight: 700;
                color: #111827;
                margin-bottom: 16px;
            }
            .body p {
                font-size: 16px;
                line-height: 1.6;
                color: #4b5563;
                margin-bottom: 24px;
            }
            .message-container {
                background-color: #f8fafc;
                border-left: 4px solid #4f46e5;
                border-radius: 8px;
                padding: 24px;
                margin: 32px 0;
                text-align: left;
            }
            .cta-button {
                display: inline-block;
                background-color: #4f46e5;
                color: #ffffff !important;
                padding: 16px 32px;
                border-radius: 8px;
                text-decoration: none;
                font-weight: 700;
                font-size: 16px;
                transition: background-color 0.2s;
                box-shadow: 0 4px 6px -1px rgba(79, 70, 229, 0.2);
            }
            .footer {
                padding: 32px 40px;
                background-color: #f8fafc;
                text-align: center;
                font-size: 14px;
                color: #94a3b8;
                border-top: 1px solid #f1f5f9;
            }
            .footer p {
                margin: 8px 0;
            }
        </style>
    </head>
    <body>
        <div class="wrapper">
            <div class="content">
                <div class="header">
                    <h1>GYM<span>PRO</span></h1>
                </div>
                <div class="body">
                    <h2>Member Reminder</h2>
                    <p>Dear {{NAME}},</p>
                    <p>This is a friendly reminder regarding your GymPro membership account.</p>
                    
                    <div class="message-container">
                        <p style="margin: 0; font-weight: 600; color: #1e293b;">{{MESSAGE}}</p>
                    </div>
                </div>
                <div class="footer">
                    <p>Thank you for being a valued member of GymPro!</p>
                    <p>&copy; 2026 GymPro. All rights reserved.</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """.replace("{{NAME}}", member_name).replace("{{MESSAGE}}", message_text)

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {RESEND_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "from": FROM_EMAIL,
                    "to": to_email,
                    "subject": subject,
                    "html": html,
                },
                timeout=10.0
            )
            
            if response.status_code in [200, 201]:
                print(f"✅ Reminder email sent successfully to {to_email}")
                return True
            else:
                print(f"❌ Resend API Error (Reminder): {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Failed to send reminder email via Resend: {str(e)}")
        return False
