import smtplib
import ssl
import secrets
from email.message import EmailMessage

def send_verification_email(user_email, user_name):
    token = secrets.token_urlsafe(32)
    verification_link = f"https://athlo.app/verify-email?token={token}"

    email_sender = "no-reply@athlo.app"
    email_password = "YOUR_APP_PASSWORD"  # Gebruik een app-specifiek wachtwoord of environment variable
    email_receiver = user_email

    subject = "Bevestig je e-mailadres voor Athlo"
    body = f"""
    Welkom bij Athlo, {user_name}!

    Bedankt voor je registratie. Klik op onderstaande link om je e-mailadres te bevestigen:

    {verification_link}

    Als je je niet hebt geregistreerd, kun je deze e-mail negeren.

    Sportieve groet,
    Het Athlo Team
    """

    em = EmailMessage()
    em['From'] = email_sender
    em['To'] = email_receiver
    em['Subject'] = subject
    em.set_content(body)

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
        smtp.login(email_sender, email_password)
        smtp.send_message(em)

    return token  # Deze token kun je opslaan in je database
