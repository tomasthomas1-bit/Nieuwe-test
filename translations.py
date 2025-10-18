translations = {
    "nl": {
        "email_verification_subject": "Bevestig je e-mailadres voor Athlo",
        "email_verification_body": lambda name, link: f"""
            Welkom bij Athlo, {name}!

            Bedankt voor je registratie. Klik op onderstaande link om je e-mailadres te bevestigen:

            {link}

            Als je je niet hebt geregistreerd, kun je deze e-mail negeren.

            Sportieve groet,
            Het Athlo Team
        """,
        "email_verified": "E-mailadres succesvol bevestigd.",
        "email_already_verified": "Gebruiker is al geverifieerd.",
        "email_sent": "Verificatiemail verzonden. Controleer je inbox.",
    },
    "en": {
        "email_verification_subject": "Confirm your email address for Athlo",
        "email_verification_body": lambda name, link: f"""
            Welcome to Athlo, {name}!

            Thank you for registering. Click the link below to confirm your email address:

            {link}

            If you did not register, you can ignore this email.

            Best regards,
            The Athlo Team
        """,
        "email_verified": "Email address successfully verified.",
        "email_already_verified": "User is already verified.",
        "email_sent": "Verification email sent. Please check your inbox.",
    }
}
