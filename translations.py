# translations.py

translations = {
    "nl": {
        # --- E-mail (reeds aanwezig) ---
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
        # --- API keys (NL) ---
        "ok": "OK",
        "forbidden": "Toegang geweigerd.",
        "user_not_found": "Gebruiker niet gevonden.",
        "user_already_verified": "Gebruiker is al geverifieerd.",
        "verification_email_sent": "Verificatiemail verzonden. Controleer je inbox.",
        "invalid_or_expired_token": "Ongeldige of verlopen verificatielink.",
        "internal_server_error": "Interne serverfout.",
        "incorrect_credentials": "Incorrecte gebruikersnaam of wachtwoord.",
        "match_success": "Match!",
        "swipe_registered": "Swipe geregistreerd.",
        "message_sent": "Bericht verzonden.",
        "no_match_cannot_message": "Bericht kan niet worden verzonden: geen match.",
        "chat_access_denied": "Geen toegang tot deze chat.",
        "user_reported": "Gebruiker succesvol gerapporteerd.",
        "cannot_report_self": "Je kunt jezelf niet rapporteren.",
        "user_blocked": "Gebruiker succesvol geblokkeerd.",
        "user_already_blocked": "Gebruiker was al geblokkeerd.",
        "cannot_block_self": "Je kunt jezelf niet blokkeren.",
        "match_deleted": "Match succesvol verwijderd.",
        "photo_deleted": "Foto succesvol verwijderd.",
        "photo_not_found": "Foto niet gevonden of geen permissie.",
        "photo_uploaded": "Foto succesvol geüpload.",
        "no_profile_photo": "Gebruiker heeft geen profielfoto meer.",
        "route_suggestion_error": "Kon geen recente Strava-locaties bepalen. Zorg dat beide gebruikers een geldig strava_token hebben of gebruik 'mock:LAT,LNG' voor testen.",
        "route_suggestion_success": "Voorstel gegenereerd op basis van Strava-activiteit.",

        # Extra keys gebruikt in validaties
        "no_fields_to_update": "Geen velden om bij te werken.",
        "day_of_week_invalid": "day_of_week moet 0..6 zijn.",
        "invalid_time_format": "Ongeldig tijdformaat, gebruik HH:MM.",
        "time_out_of_range": "Uur/minuut buiten bereik.",
        "end_time_after_start": "end_time moet later zijn dan start_time.",
        "cannot_swipe_self": "Je kunt niet op je eigen profiel swipen.",
        "db_error": "Databasefout.",
        "token_missing": "Kon validatiegegevens niet verifiëren.",
        "token_invalid": "Ongeldige of verlopen token.",
    },
    "en": {
        # --- Email (existing) ---
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

        # --- API keys (EN) ---
        "ok": "OK",
        "forbidden": "Forbidden.",
        "user_not_found": "User not found.",
        "user_already_verified": "User is already verified.",
        "verification_email_sent": "Verification email sent. Please check your inbox.",
        "invalid_or_expired_token": "Invalid or expired verification link.",
        "internal_server_error": "Internal server error.",
        "incorrect_credentials": "Incorrect username or password.",
        "match_success": "Match!",
        "swipe_registered": "Swipe registered.",
        "message_sent": "Message sent.",
        "no_match_cannot_message": "Cannot send message: no match.",
        "chat_access_denied": "No access to this chat.",
        "user_reported": "User successfully reported.",
        "cannot_report_self": "You cannot report yourself.",
        "user_blocked": "User successfully blocked.",
        "user_already_blocked": "User was already blocked.",
        "cannot_block_self": "You cannot block yourself.",
        "match_deleted": "Match deleted successfully.",
        "photo_deleted": "Photo deleted successfully.",
        "photo_not_found": "Photo not found or no permission.",
        "photo_uploaded": "Photo uploaded successfully.",
        "no_profile_photo": "User has no profile photo anymore.",
        "route_suggestion_error": "Could not determine recent Strava locations. Ensure both users have a valid strava_token or use 'mock:LAT,LNG' for testing.",
        "route_suggestion_success": "Suggestion generated based on Strava activity.",

        # Extra keys used in validations
        "no_fields_to_update": "No fields to update.",
        "day_of_week_invalid": "day_of_week must be 0..6.",
        "invalid_time_format": "Invalid time format, use HH:MM.",
        "time_out_of_range": "Hour/minute out of range.",
        "end_time_after_start": "end_time must be later than start_time.",
        "cannot_swipe_self": "You cannot swipe on your own profile.",
        "db_error": "Database error.",
        "token_missing": "Could not verify credentials.",
        "token_invalid": "Invalid or expired token.",
    },

    # De overige talen behouden de e-mail sleutels zoals je had
    "fr": {
        "email_verification_subject": "Confirmez votre adresse e-mail pour Athlo",
        "email_verification_body": lambda name, link: f"""
Bienvenue sur Athlo, {name} !
Merci pour votre inscription. Cliquez sur le lien ci-dessous pour confirmer votre adresse e-mail :
{link}
Si vous ne vous êtes pas inscrit, vous pouvez ignorer cet e-mail.
Sportivement,
L'équipe Athlo
""",
        "email_verified": "Adresse e-mail confirmée avec succès.",
        "email_already_verified": "L'utilisateur est déjà vérifié.",
        "email_sent": "E-mail de vérification envoyé. Veuillez vérifier votre boîte de réception.",
    },
    "de": {
        "email_verification_subject": "Bestätigen Sie Ihre E-Mail-Adresse für Athlo",
        "email_verification_body": lambda name, link: f"""
Willkommen bei Athlo, {name}!
Vielen Dank für Ihre Registrierung. Klicken Sie auf den folgenden Link, um Ihre E-Mail-Adresse zu bestätigen:
{link}
Wenn Sie sich nicht registriert haben, ignorieren Sie bitte diese E-Mail.
Sportliche Grüße,
Das Athlo-Team
""",
        "email_verified": "E-Mail-Adresse erfolgreich bestätigt.",
        "email_already_verified": "Benutzer ist bereits verifiziert.",
        "email_sent": "Bestätigungs-E-Mail gesendet. Bitte überprüfen Sie Ihren Posteingang.",
    },
    "es": {
        "email_verification_subject": "Confirma tu dirección de correo electrónico para Athlo",
        "email_verification_body": lambda name, link: f"""
¡Bienvenido a Athlo, {name}!
Gracias por registrarte. Haz clic en el siguiente enlace para confirmar tu dirección de correo electrónico:
{link}
Si no te registraste, puedes ignorar este correo.
Saludos deportivos,
El equipo de Athlo
""",
        "email_verified": "Dirección de correo electrónico confirmada con éxito.",
        "email_already_verified": "El usuario ya está verificado.",
        "email_sent": "Correo de verificación enviado. Por favor revisa tu bandeja de entrada.",
    },
    "pt": {
        "email_verification_subject": "Confirme seu endereço de e-mail para Athlo",
        "email_verification_body": lambda name, link: f"""
Bem-vindo ao Athlo, {name}!
Obrigado por se registrar. Clique no link abaixo para confirmar seu endereço de e-mail:
{link}
Se você não se registrou, pode ignorar este e-mail.
Saudações esportivas,
Equipe Athlo
""",
        "email_verified": "Endereço de e-mail confirmado com sucesso.",
        "email_already_verified": "Usuário já verificado.",
        "email_sent": "E-mail de verificação enviado. Verifique sua caixa de entrada.",
    },
    "it": {
        "email_verification_subject": "Conferma il tuo indirizzo email per Athlo",
        "email_verification_body": lambda name, link: f"""
Benvenuto su Athlo, {name}!
Grazie per esserti registrato. Clicca sul link qui sotto per confermare il tuo indirizzo email:
{link}
Se non ti sei registrato, puoi ignorare questa email.
Cordiali saluti,
Il team di Athlo
""",
        "email_verified": "Indirizzo email confermato con successo.",
        "email_already_verified": "Utente già verificato.",
        "email_sent": "Email di verifica inviata. Controlla la tua casella di posta.",
    },
}
``
