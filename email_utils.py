# email_utils.py
import os
import logging
import secrets
import requests
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
    body_template = lang_map.get("email_verification_body", "")
    
    # Als het een callable is (lambda), aanroepen met name en link
    if callable(body_template):
        body = body_template(name, link)
    else:
        body = body_template

    return subject, body

# -------- Resend API ----------
def _resend_send(to_email: str, subject: str, text_body: str, html_body: Optional[str] = None, from_email: Optional[str] = None) -> None:
    """
    Verstuur email via Resend API.
    """
    api_key = os.getenv("RESEND_API_KEY")
    if not api_key:
        logger.warning("RESEND_API_KEY niet geconfigureerd. E-mail wordt NIET verzonden; logging-only mode.")
        logger.info("Email (to=%s): subject=%r", to_email, subject)
        logger.debug("Text body:\n%s", text_body)
        logger.debug("HTML body:\n%s", html_body)
        return

    if not from_email:
        # Geverifieerd domein in Resend
        from_email = "Athlo <noreply@athlo.be>"

    url = "https://api.resend.com/emails"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "from": from_email,
        "to": to_email,
        "subject": subject,
        "text": text_body,
        "html": html_body or text_body,
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        response.raise_for_status()
        logger.info("Email verzonden naar %s via Resend", to_email)
    except requests.exceptions.RequestException as e:
        # Log de volledige response voor debugging
        if hasattr(e, 'response') and e.response is not None:
            logger.error("Resend API response: %s", e.response.text)
        logger.exception("Verzenden van email is mislukt: %s", str(e))
        raise

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

def send_verification_email(
    to_email: str,
    name: str,
    token: str,
    lang: str = "nl",
    subject: Optional[str] = None,
    body: Optional[str] = None,
) -> None:
    """
    Verstuur verificatiemail via Resend.
    - Als subject/body ontbreken, rendert functie zelf text + html op basis van 'lang'.
    """
    # Render text/html
    if subject is None or body is None:
        subject, text_body = _render_email_text(name, token, lang)
    else:
        text_body = body

    # Bouw link opnieuw voor HTML (zelfde logica als text)
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000").rstrip("/")
    link = f"{frontend_url}/verify-email?token={token}"
    html_body = render_verification_email_html(name, link, lang)

    _resend_send(to_email, subject, text_body, html_body)

def send_password_reset_email(
    to_email: str,
    name: str,
    token: str,
    lang: str = "nl",
) -> None:
    """
    Verstuur password reset email via Resend.
    """
    subject, text_body = _render_password_reset_text(name, token, lang)
    
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000").rstrip("/")
    link = f"{frontend_url}/reset-password?token={token}"
    html_body = render_password_reset_html(name, link, lang)

    _resend_send(to_email, subject, text_body, html_body)
