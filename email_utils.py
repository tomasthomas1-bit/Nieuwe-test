# email_utils.py
import os
import logging
import secrets
import smtplib
import ssl
from email.message import EmailMessage
from typing import Optional, Tuple

from translations import translations

logger = logging.getLogger(__name__)


# ------------------ Token ------------------
def generate_verification_token(nbytes: int = 32) -> str:
    """
    Genereer een URL-veilige verificatietoken (default ~43 tekens).
    Verhoog nbytes voor langere tokens.
    """
    return secrets.token_urlsafe(nbytes)


# ------------------ Templates ------------------
def _render_email(name: str, token: str, lang: str = "nl") -> Tuple[str, str]:
    """
    Bouw subject en body op uit translations + FRONTEND_URL.
    """
    lang = lang if lang in translations else "en"
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000").rstrip("/")
    link = f"{frontend_url}/verify-email?token={token}"

    subject = translations[lang]["email_verification_subject"]
    # Belangrijk: 'email_verification_body' is een lambda in translations.py
    body = translations[lang]"email_verification_body"
    return subject, body


def _build_message(
    to_email: str,
    from_email: str,
    subject: str,
    body: str,
    reply_to: Optional[str] = None,
) -> EmailMessage:
    """
    Bouw een text/plain bericht op (kan je later uitbreiden naar HTML/alt).
    """
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email
    if reply_to:
        msg["Reply-To"] = reply_to
    msg.set_content(body, subtype="plain", charset="utf-8")
    return msg


# ------------------ SMTP ------------------
def _smtp_send(msg: EmailMessage) -> None:
    """
    Verzend het bericht via SMTP op basis van env-variabelen.
    Ondersteunt STARTTLS (meest gangbaar), SSL of PLAINTEXT.
    """

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
        # SMTPS (465)
        with smtplib.SMTP_SSL(host=host, port=port, timeout=timeout, context=context) as server:
            if user and pwd:
                server.login(user, pwd)
            server.send_message(msg)
    elif security == "STARTTLS":
        # Submission (587)
        with smtplib.SMTP(host=host, port=port, timeout=timeout) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            if user and pwd:
                server.login(user, pwd)
            server.send_message(msg)
    elif security == "PLAINTEXT":
        # Alleen voor lokale/dev relays zonder TLS
        with smtplib.SMTP(host=host, port=port, timeout=timeout) as server:
            if user and pwd:
                server.login(user, pwd)
            server.send_message(msg)
    else:
        raise ValueError(f"Onbekende SMTP_SECURITY: {security}")


# ------------------ Public API ------------------
def send_verification_email(
    to_email: str,
    name: str,
    token: str,
    lang: str = "nl",
    subject: Optional[str] = None,
    body: Optional[str] = None,
) -> None:
    """
    Verzend de verificatiemail.
    - Als subject/body niet zijn meegegeven, rendert dit ze op basis van 'lang'.
    - Als SMTP niet (volledig) geconfigureerd is, loggen we de mail (dev fallback).
    - Raise bij echte SMTP-fouten, zodat je dit in de app/logs ziet.
    """

    # From en (optioneel) Reply-To
    from_email = os.getenv("SMTP_FROM")
    reply_to = os.getenv("SMTP_REPLY_TO")

    # Als subject/body ontbreken, haal uit translations.
    if subject is None or body is None:
        subject, body = _render_email(name, token, lang)

    # Fallback: geen SMTP -> alleen loggen (dev/staging)
    host = os.getenv("SMTP_HOST")
    port = os.getenv("SMTP_PORT")
    if not host or not port or not from_email:
        logger.warning(
            "SMTP niet volledig geconfigureerd (HOST/PORT/FROM). "
            "E-mail wordt NIET verzonden; logging-only mode ingeschakeld."
        )
        logger.info("Verification email (to=%s, from=%s): subject=%r", to_email, from_email or "<unset>", subject)
        logger.debug("Body:\n%s", body)
        return

    # Bouw en verstuur bericht
    msg = _build_message(to_email=to_email, from_email=from_email, subject=subject, body=body, reply_to=reply_to)

    try:
        _smtp_send(msg)
        logger.info("Verificatiemail verzonden naar %s", to_email)
    except Exception as e:
        # Belangrijk: bubbelt door naar de caller of wordt gelogd door FastAPI exception handler
        logger.exception("Verzenden van verificatiemail is mislukt.")
        raise
