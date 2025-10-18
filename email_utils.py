# email_utils.py
import os
import logging
import secrets
from typing import Optional, Tuple
from translations import translations

logger = logging.getLogger(__name__)

def generate_verification_token(nbytes: int = 32) -> str:
    """
    Genereer een URL-veilige verificatietoken (default ~43 tekens).
    Verhoog nbytes voor langere tokens.
    """
    return secrets.token_urlsafe(nbytes)

def _render_email(name: str, token: str, lang: str = "nl") -> Tuple[str, str]:
    """
    Bouw subject en body op uit translations + FRONTEND_URL.
    """
    lang = lang if lang in translations else "en"
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    link = f"{frontend_url.rstrip('/')}/verify-email?token={token}"

    subject = translations[lang]["email_verification_subject"]
    body = translations[lang]["email_verification_body"    return subject, body

def send_verification_email(
    to_email: str,
    name: str,
    token: str,
    lang: str = "nl",
    subject: Optional[str] = None,
    body: Optional[str] = None,
) -> None:
    """
    Verzend de verificatiemail. Als subject/body niet meegegeven zijn,
    worden ze vertaald op basis van 'lang' en translations.
    Vervang de logging hieronder door je echte SMTP/ESP-integratie.
    """
    if subject is None or body is None:
        subject_rendered, body_rendered = _render_email(name, token, lang)
    else:
        subject_rendered, body_rendered = subject, body

    # TODO: vervang door echte mailtransport (SMTP/ESP). Voor nu loggen we:
    logger.info("Sending verification email to %s | subject=%r", to_email, subject_rendered)
    logger.debug("Body:\n%s", body_rendered)
