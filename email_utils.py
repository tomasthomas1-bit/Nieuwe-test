# email_utils.py
import os
import logging
import secrets
import smtplib
import ssl
from email.message import EmailMessage
from typing import Optional, Tuple

from translations import translations
from email_templates import render_verification_email_html

logger = logging.getLogger(__name__)

# -------- Token --------
def generate_verification_token(nbytes: int = 32) -> str:
    return secrets.token_urlsafe(nbytes)

# -------- Templates (plain text) --------
def _render_email_text(name: str, token: str, lang: str = "nl") -> Tuple[str, str]:
    """
    Plain-text subject & body uit translations + FRONTEND_URL.
    """
    lang = lang if lang in translations else "en"
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000").rstrip("/")
    link = f"{frontend_url}/verify-email?token={token}"
    subject = translations[lang]["email_verification_subject"]
    lang_map = translations.get(lang, translations.get("en", {}))
    body = lang_map.get("email_verification_body", "")

    return subject, body

# -------- SMTP ----------
def _build_message(
    to_email: str,
    from_email: str,
    subject: str,
    text_body: str,
    html_body: Optional[str] = None,
    reply_to: Optional[str] = None,
) -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email
    if reply_to:
        msg["Reply-To"] = reply_to

    # multipart/alternative: eerst text/plain, dan text/html
    msg.set_content(text_body, subtype="plain", charset="utf-8")
    if html_body:
        msg.add_alternative(html_body, subtype="html", charset="utf-8")
    return msg

def _smtp_send(msg: EmailMessage) -> None:
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "0") or "0")
    user = os.getenv("SMTP_USERNAME")
    pwd = os.getenv("SMTP_PASSWORD")
    security = (os.getenv("SMTP_SECURITY", "STARTTLS") or "STARTTLS").upper()
    timeout = float(os.getenv("SMTP_TIMEOUT", "15") or "15")

    if not host or not port:
        raise RuntimeError("SMTP is niet geconfigureerd: SMTP_HOST/SMTP_PORT ontbreken.")

    context = ssl.create_default_context()

    if security == "SSL" or port == 465:
        with smtplib.SMTP_SSL(host=host, port=port, timeout=timeout, context=context) as server:
            if user and pwd:
                server.login(user, pwd)
            server.send_message(msg)
    elif security == "STARTTLS":
        with smtplib.SMTP(host=host, port=port, timeout=timeout) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            if user and pwd:
                server.login(user, pwd)
            server.send_message(msg)
    elif security == "PLAINTEXT":
        with smtplib.SMTP(host=host, port=port, timeout=timeout) as server:
            if user and pwd:
                server.login(user, pwd)
            server.send_message(msg)
    else:
        raise ValueError(f"Onbekende SMTP_SECURITY: {security}")

# -------- Password Reset Templates --------
def _render_password_reset_text(name: str, token: str, lang: str = "nl") -> Tuple[str, str]:
    """
    Plain-text subject & body voor password reset email.
    """
    lang = lang if lang in translations else "en"
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000").rstrip("/")
    link = f"{frontend_url}/reset-password?token={token}"
    
    lang_map = translations.get(lang, translations.get("en", {}))
    subject = lang_map.get("password_reset_subject", "Reset your password")
    
    body_template = lang_map.get("password_reset_body", 
        f"Hi {name},\n\nClick here to reset your password: {link}\n\nThis link expires in 1 hour.")
    
    return subject, body_template.format(name=name, link=link) if "{" in body_template else body_template


def render_password_reset_html(name: str, link: str, lang: str = "nl") -> str:
    """
    HTML template voor password reset email.
    """
    lang_map = translations.get(lang, translations.get("en", {}))
    button_text = lang_map.get("reset_password_button", "Reset Password")
    expires_text = lang_map.get("link_expires_1hour", "This link expires in 1 hour.")
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: 'Montserrat', Arial, sans-serif; background-color: #f5f5f5; margin: 0; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}
            .header {{ background: linear-gradient(135deg, #FF6B35 0%, #FF8E53 100%); padding: 40px 20px; text-align: center; }}
            .header h1 {{ color: white; margin: 0; font-size: 28px; }}
            .content {{ padding: 40px 30px; text-align: center; }}
            .content p {{ color: #333; font-size: 16px; line-height: 1.6; }}
            .button {{ display: inline-block; background: #FF6B35; color: white; padding: 16px 40px; text-decoration: none; border-radius: 30px; font-weight: bold; margin: 20px 0; }}
            .footer {{ padding: 20px; text-align: center; color: #888; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Athlo</h1>
            </div>
            <div class="content">
                <p>Hi {name},</p>
                <p>{lang_map.get("password_reset_intro", "You requested to reset your password. Click the button below to create a new password.")}</p>
                <a href="{link}" class="button">{button_text}</a>
                <p style="color: #888; font-size: 14px;">{expires_text}</p>
            </div>
            <div class="footer">
                <p>{lang_map.get("ignore_if_not_requested", "If you didn't request this, you can safely ignore this email.")}</p>
            </div>
        </div>
    </body>
    </html>
    """


# -------- Public API --------
def send_password_reset_email(
    to_email: str,
    name: str,
    token: str,
    lang: str = "nl",
) -> None:
    """
    Verzend password reset email als multipart (text + HTML).
    """
    from_email = os.getenv("SMTP_FROM")
    reply_to = os.getenv("SMTP_REPLY_TO")

    subject, text_body = _render_password_reset_text(name, token, lang)
    
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000").rstrip("/")
    link = f"{frontend_url}/reset-password?token={token}"
    html_body = render_password_reset_html(name, link, lang)

    host = os.getenv("SMTP_HOST")
    port = os.getenv("SMTP_PORT")
    if not host or not port or not from_email:
        logger.warning(
            "SMTP niet volledig geconfigureerd. Password reset email wordt NIET verzonden; logging-only mode."
        )
        logger.info("Password reset email (to=%s): subject=%r, link=%s", to_email, subject, link)
        return

    msg = _build_message(
        to_email=to_email,
        from_email=from_email,
        subject=subject,
        text_body=text_body,
        html_body=html_body,
        reply_to=reply_to,
    )

    try:
        _smtp_send(msg)
        logger.info("Password reset email verzonden naar %s", to_email)
    except Exception:
        logger.exception("Verzenden van password reset email is mislukt.")
        raise


def send_verification_email(
    to_email: str,
    name: str,
    token: str,
    lang: str = "nl",
    subject: Optional[str] = None,
    body: Optional[str] = None,
) -> None:
    """
    Verzend verificatiemail als multipart (text + HTML).
    - Als subject/body ontbreken, rendert functie zelf text + html op basis van 'lang'.
    - Zonder SMTP-config -> logging-only (geen verzending, wel zichtbaar in logs).
    """
    from_email = os.getenv("SMTP_FROM")
    reply_to = os.getenv("SMTP_REPLY_TO")

    # Render text/html
    if subject is None or body is None:
        subject, text_body = _render_email_text(name, token, lang)
    else:
        text_body = body

    # Bouw link opnieuw voor HTML (zelfde logica als text)
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000").rstrip("/")
    link = f"{frontend_url}/verify-email?token={token}"
    html_body = render_verification_email_html(name, link, lang)

    # Fallback: geen SMTP-config -> loggen en return
    host = os.getenv("SMTP_HOST")
    port = os.getenv("SMTP_PORT")
    if not host or not port or not from_email:
        logger.warning(
            "SMTP niet volledig geconfigureerd (HOST/PORT/FROM). "
            "E-mail wordt NIET verzonden; logging-only mode ingeschakeld."
        )
        logger.info("Verification email (to=%s, from=%s): subject=%r", to_email, from_email or "<unset>", subject)
        logger.debug("Text body:\n%s", text_body)
        logger.debug("HTML body:\n%s", html_body)
        return

    msg = _build_message(
        to_email=to_email,
        from_email=from_email,
        subject=subject,
        text_body=text_body,
        html_body=html_body,
        reply_to=reply_to,
    )

    try:
        _smtp_send(msg)
        logger.info("Verificatiemail verzonden naar %s", to_email)
    except Exception:
        logger.exception("Verzenden van verificatiemail is mislukt.")
        raise
