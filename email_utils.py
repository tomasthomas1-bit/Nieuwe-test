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

# -------- Public API --------
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
