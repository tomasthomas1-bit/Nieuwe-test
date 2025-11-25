# translations.py

translations = {
    "nl": {
        # --- E-mail ---
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
        "email_not_verified": "Je e-mailadres is nog niet geverifieerd. Controleer je inbox voor de verificatielink.",

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
        
        # Strava
        "strava_link": "Koppel Strava",
        "strava_linked": "Strava Gekoppeld",
        "strava_unlink": "Ontkoppel Strava",
        "strava_activities": "Recente activiteiten",
        "strava_not_configured": "Strava integratie is niet geconfigureerd",
        "strava_connect_description": "Koppel je Strava account om automatisch je sportactiviteiten te delen en betere matches te vinden.",

        # Validatie/overige
        "no_fields_to_update": "Geen velden om bij te werken.",
        "day_of_week_invalid": "day_of_week moet 0..6 zijn.",
        "invalid_time_format": "Ongeldig tijdformaat, gebruik HH:MM.",
        "time_out_of_range": "Uur/minuut buiten bereik.",
        "end_time_after_start": "end_time moet later zijn dan start_time.",
        "cannot_swipe_self": "Je kunt niet op je eigen profiel swipen.",
        "db_error": "Databasefout.",
        "token_missing": "Kon validatiegegevens niet verifiëren.",
        "token_invalid": "Ongeldige of verlopen token.",
        
        # Password Reset
        "password_reset_subject": "Wachtwoord resetten voor Athlo",
        "password_reset_body": "Hallo {name},\n\nKlik op de volgende link om je wachtwoord te resetten:\n{link}\n\nDeze link verloopt na 1 uur.\n\nAls je dit niet hebt aangevraagd, kun je deze e-mail negeren.\n\nSportieve groet,\nHet Athlo Team",
        "password_reset_intro": "Je hebt gevraagd om je wachtwoord te resetten. Klik op de knop hieronder om een nieuw wachtwoord aan te maken.",
        "reset_password_button": "Wachtwoord Resetten",
        "link_expires_1hour": "Deze link verloopt na 1 uur.",
        "ignore_if_not_requested": "Als je dit niet hebt aangevraagd, kun je deze e-mail veilig negeren.",
        "password_reset_sent": "Als dit e-mailadres bij ons bekend is, ontvang je een e-mail met instructies.",
        "password_reset_success": "Je wachtwoord is succesvol gewijzigd.",
        "token_expired": "Deze link is verlopen. Vraag een nieuwe wachtwoord reset aan.",
        "forgot_password": "Wachtwoord vergeten?",
        "enter_email": "Voer je e-mailadres in",
        "send_reset_link": "Verstuur resetlink",
        "back_to_login": "Terug naar inloggen",
        "new_password": "Nieuw wachtwoord",
        "confirm_password": "Bevestig wachtwoord",
        "passwords_dont_match": "Wachtwoorden komen niet overeen.",
        "reset_password": "Wachtwoord resetten",
    },

    "en": {
        # --- Email ---
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
        "email_not_verified": "Your email address is not yet verified. Please check your inbox for the verification link.",

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
        
        # Strava
        "strava_link": "Link Strava",
        "strava_linked": "Strava Linked",
        "strava_unlink": "Unlink Strava",
        "strava_activities": "Recent activities",
        "strava_not_configured": "Strava integration not configured",
        "strava_connect_description": "Connect your Strava account to automatically share your sports activities and find better matches.",

        # Validation/other
        "no_fields_to_update": "No fields to update.",
        "day_of_week_invalid": "day_of_week must be 0..6.",
        "invalid_time_format": "Invalid time format, use HH:MM.",
        "time_out_of_range": "Hour/minute out of range.",
        "end_time_after_start": "end_time must be later than start_time.",
        "cannot_swipe_self": "You cannot swipe on your own profile.",
        "db_error": "Database error.",
        
        # Password Reset
        "password_reset_subject": "Reset your password for Athlo",
        "password_reset_body": "Hi {name},\n\nClick the following link to reset your password:\n{link}\n\nThis link expires in 1 hour.\n\nIf you didn't request this, you can safely ignore this email.\n\nBest regards,\nThe Athlo Team",
        "password_reset_intro": "You requested to reset your password. Click the button below to create a new password.",
        "reset_password_button": "Reset Password",
        "link_expires_1hour": "This link expires in 1 hour.",
        "ignore_if_not_requested": "If you didn't request this, you can safely ignore this email.",
        "password_reset_sent": "If this email address is registered with us, you'll receive an email with instructions.",
        "password_reset_success": "Your password has been successfully changed.",
        "token_expired": "This link has expired. Please request a new password reset.",
        "forgot_password": "Forgot password?",
        "enter_email": "Enter your email address",
        "send_reset_link": "Send reset link",
        "back_to_login": "Back to login",
        "new_password": "New password",
        "confirm_password": "Confirm password",
        "passwords_dont_match": "Passwords don't match.",
        "reset_password": "Reset password",
        "token_missing": "Could not verify credentials.",
        "token_invalid": "Invalid or expired token.",
    },

    "fr": {
        # --- E-mail ---
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
        "email_not_verified": "Votre adresse e-mail n'est pas encore vérifiée. Veuillez vérifier votre boîte de réception pour le lien de vérification.",

        # --- API keys (FR) ---
        "ok": "OK",
        "forbidden": "Accès refusé.",
        "user_not_found": "Utilisateur introuvable.",
        "user_already_verified": "L'utilisateur est déjà vérifié.",
        "verification_email_sent": "E-mail de vérification envoyé. Veuillez vérifier votre boîte de réception.",
        "invalid_or_expired_token": "Lien de vérification invalide ou expiré.",
        "internal_server_error": "Erreur interne du serveur.",
        "incorrect_credentials": "Nom d'utilisateur ou mot de passe incorrect.",
        "match_success": "Match !",
        "swipe_registered": "Swipe enregistré.",
        "message_sent": "Message envoyé.",
        "no_match_cannot_message": "Impossible d'envoyer le message : pas de match.",
        "chat_access_denied": "Aucun accès à cette discussion.",
        "user_reported": "Utilisateur signalé avec succès.",
        "cannot_report_self": "Vous ne pouvez pas vous signaler vous-même.",
        "user_blocked": "Utilisateur bloqué avec succès.",
        "user_already_blocked": "L'utilisateur était déjà bloqué.",
        "cannot_block_self": "Vous ne pouvez pas vous bloquer vous-même.",
        "match_deleted": "Match supprimé avec succès.",
        "photo_deleted": "Photo supprimée avec succès.",
        "photo_not_found": "Photo introuvable ou sans autorisation.",
        "photo_uploaded": "Photo téléchargée avec succès.",
        "no_profile_photo": "L'utilisateur n'a plus de photo de profil.",
        "route_suggestion_error": "Impossible de déterminer des positions Strava récentes. Assurez-vous que les deux utilisateurs possèdent un strava_token valide ou utilisez 'mock:LAT,LNG' pour les tests.",
        "route_suggestion_success": "Suggestion générée sur la base de l'activité Strava.",
        
        # Strava
        "strava_link": "Lier Strava",
        "strava_linked": "Strava Lié",
        "strava_unlink": "Dissocier Strava",
        "strava_activities": "Activités récentes",
        "strava_not_configured": "Intégration Strava non configurée",
        "strava_connect_description": "Connectez votre compte Strava pour partager automatiquement vos activités sportives et trouver de meilleures correspondances.",

        # Validation/other
        "no_fields_to_update": "Aucun champ à mettre à jour.",
        "day_of_week_invalid": "day_of_week doit être 0..6.",
        "invalid_time_format": "Format d'heure invalide, utilisez HH:MM.",
        "time_out_of_range": "Heure/minute hors limites.",
        "end_time_after_start": "end_time doit être postérieure à start_time.",
        "cannot_swipe_self": "Vous ne pouvez pas swiper votre propre profil.",
        "db_error": "Erreur de base de données.",
        "token_missing": "Impossible de vérifier les informations d’identification.",
        "token_invalid": "Jeton invalide ou expiré.",
    },

    "de": {
        # --- E-Mail ---
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
        "email_not_verified": "Ihre E-Mail-Adresse ist noch nicht bestätigt. Bitte überprüfen Sie Ihren Posteingang für den Bestätigungslink.",

        # --- API keys (DE) ---
        "ok": "OK",
        "forbidden": "Zugriff verweigert.",
        "user_not_found": "Benutzer nicht gefunden.",
        "user_already_verified": "Benutzer ist bereits verifiziert.",
        "verification_email_sent": "Bestätigungs-E-Mail gesendet. Bitte prüfen Sie Ihren Posteingang.",
        "invalid_or_expired_token": "Ungültiger oder abgelaufener Bestätigungslink.",
        "internal_server_error": "Interner Serverfehler.",
        "incorrect_credentials": "Falscher Benutzername oder falsches Passwort.",
        "match_success": "Match!",
        "swipe_registered": "Swipe registriert.",
        "message_sent": "Nachricht gesendet.",
        "no_match_cannot_message": "Nachricht kann nicht gesendet werden: kein Match.",
        "chat_access_denied": "Kein Zugriff auf diesen Chat.",
        "user_reported": "Benutzer erfolgreich gemeldet.",
        "cannot_report_self": "Sie können sich nicht selbst melden.",
        "user_blocked": "Benutzer erfolgreich blockiert.",
        "user_already_blocked": "Benutzer war bereits blockiert.",
        "cannot_block_self": "Sie können sich nicht selbst blockieren.",
        "match_deleted": "Match erfolgreich gelöscht.",
        "photo_deleted": "Foto erfolgreich gelöscht.",
        "photo_not_found": "Foto nicht gefunden oder keine Berechtigung.",
        "photo_uploaded": "Foto erfolgreich hochgeladen.",
        "no_profile_photo": "Benutzer hat kein Profilfoto mehr.",
        "route_suggestion_error": "Konnte keine aktuellen Strava-Positionen ermitteln. Stellen Sie sicher, dass beide Benutzer ein gültiges strava_token haben oder verwenden Sie 'mock:LAT,LNG' zum Testen.",
        "route_suggestion_success": "Vorschlag basierend auf Strava-Aktivität erstellt.",
        
        # Strava
        "strava_link": "Strava verbinden",
        "strava_linked": "Strava Verbunden",
        "strava_unlink": "Strava trennen",
        "strava_activities": "Aktuelle Aktivitäten",
        "strava_not_configured": "Strava-Integration nicht konfiguriert",
        "strava_connect_description": "Verbinden Sie Ihr Strava-Konto, um Ihre Sportaktivitäten automatisch zu teilen und bessere Matches zu finden.",

        # Validierung/sonstiges
        "no_fields_to_update": "Keine Felder zum Aktualisieren.",
        "day_of_week_invalid": "day_of_week muss 0..6 sein.",
        "invalid_time_format": "Ungültiges Zeitformat, verwenden Sie HH:MM.",
        "time_out_of_range": "Stunde/Minute außerhalb des gültigen Bereichs.",
        "end_time_after_start": "end_time muss nach start_time liegen.",
        "cannot_swipe_self": "Sie können Ihr eigenes Profil nicht swipen.",
        "db_error": "Datenbankfehler.",
        "token_missing": "Anmeldedaten konnten nicht überprüft werden.",
        "token_invalid": "Ungültiges oder abgelaufenes Token.",
    },

    "es": {
        # --- Correo ---
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

        # --- API keys (ES) ---
        "ok": "OK",
        "forbidden": "Acceso denegado.",
        "user_not_found": "Usuario no encontrado.",
        "user_already_verified": "El usuario ya está verificado.",
        "verification_email_sent": "Correo de verificación enviado. Por favor revisa tu bandeja de entrada.",
        "invalid_or_expired_token": "Enlace de verificación inválido o caducado.",
        "internal_server_error": "Error interno del servidor.",
        "incorrect_credentials": "Nombre de usuario o contraseña incorrectos.",
        "match_success": "¡Match!",
        "swipe_registered": "Swipe registrado.",
        "message_sent": "Mensaje enviado.",
        "no_match_cannot_message": "No se puede enviar el mensaje: no hay match.",
        "chat_access_denied": "Sin acceso a este chat.",
        "user_reported": "Usuario reportado correctamente.",
        "cannot_report_self": "No puedes reportarte a ti mismo.",
        "user_blocked": "Usuario bloqueado correctamente.",
        "user_already_blocked": "El usuario ya estaba bloqueado.",
        "cannot_block_self": "No puedes bloquearte a ti mismo.",
        "match_deleted": "Match eliminado correctamente.",
        "photo_deleted": "Foto eliminada correctamente.",
        "photo_not_found": "Foto no encontrada o sin permisos.",
        "photo_uploaded": "Foto subida correctamente.",
        "no_profile_photo": "El usuario ya no tiene foto de perfil.",
        "route_suggestion_error": "No se pudieron determinar ubicaciones recientes de Strava. Asegúrate de que ambos usuarios tengan un strava_token válido o usa 'mock:LAT,LNG' para pruebas.",
        "route_suggestion_success": "Sugerencia generada según la actividad de Strava.",
        
        # Strava
        "strava_link": "Vincular Strava",
        "strava_linked": "Strava Vinculado",
        "strava_unlink": "Desvincular Strava",
        "strava_activities": "Actividades recientes",
        "strava_not_configured": "Integración de Strava no configurada",
        "strava_connect_description": "Conecta tu cuenta de Strava para compartir automáticamente tus actividades deportivas y encontrar mejores coincidencias.",

        # Validación/otros
        "no_fields_to_update": "No hay campos para actualizar.",
        "day_of_week_invalid": "day_of_week debe ser 0..6.",
        "invalid_time_format": "Formato de hora inválido, usa HH:MM.",
        "time_out_of_range": "Hora/minuto fuera de rango.",
        "end_time_after_start": "end_time debe ser posterior a start_time.",
        "cannot_swipe_self": "No puedes hacer swipe en tu propio perfil.",
        "db_error": "Error de base de datos.",
        "token_missing": "No se pudieron verificar las credenciales.",
        "token_invalid": "Token inválido o expirado.",
    },

    "pt": {
        # --- E-mail ---
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

        # --- API keys (PT) ---
        "ok": "OK",
        "forbidden": "Acesso negado.",
        "user_not_found": "Usuário não encontrado.",
        "user_already_verified": "O usuário já está verificado.",
        "verification_email_sent": "E-mail de verificação enviado. Verifique sua caixa de entrada.",
        "invalid_or_expired_token": "Link de verificação inválido ou expirado.",
        "internal_server_error": "Erro interno do servidor.",
        "incorrect_credentials": "Nome de usuário ou senha incorretos.",
        "match_success": "Match!",
        "swipe_registered": "Swipe registrado.",
        "message_sent": "Mensagem enviada.",
        "no_match_cannot_message": "Não é possível enviar a mensagem: não há match.",
        "chat_access_denied": "Sem acesso a este chat.",
        "user_reported": "Usuário reportado com sucesso.",
        "cannot_report_self": "Você não pode se reportar.",
        "user_blocked": "Usuário bloqueado com sucesso.",
        "user_already_blocked": "O usuário já estava bloqueado.",
        "cannot_block_self": "Você não pode se bloquear.",
        "match_deleted": "Match excluído com sucesso.",
        "photo_deleted": "Foto excluída com sucesso.",
        "photo_not_found": "Foto não encontrada ou sem permissão.",
        "photo_uploaded": "Foto enviada com sucesso.",
        "no_profile_photo": "O usuário não possui mais foto de perfil.",
        "route_suggestion_error": "Não foi possível determinar locais recentes do Strava. Garanta que ambos os usuários tenham um strava_token válido ou use 'mock:LAT,LNG' para testes.",
        "route_suggestion_success": "Sugestão gerada com base na atividade do Strava.",
        
        # Strava
        "strava_link": "Vincular Strava",
        "strava_linked": "Strava Vinculado",
        "strava_unlink": "Desvincular Strava",
        "strava_activities": "Atividades recentes",
        "strava_not_configured": "Integração Strava não configurada",
        "strava_connect_description": "Conecte sua conta Strava para compartilhar automaticamente suas atividades esportivas e encontrar melhores correspondências.",

        # Validação/outros
        "no_fields_to_update": "Nenhum campo para atualizar.",
        "day_of_week_invalid": "day_of_week deve ser 0..6.",
        "invalid_time_format": "Formato de hora inválido, use HH:MM.",
        "time_out_of_range": "Hora/minuto fora do intervalo.",
        "end_time_after_start": "end_time deve ser posterior a start_time.",
        "cannot_swipe_self": "Você não pode fazer swipe no seu próprio perfil.",
        "db_error": "Erro de banco de dados.",
        "token_missing": "Não foi possível verificar as credenciais.",
        "token_invalid": "Token inválido ou expirado.",
    },

    "it": {
        # --- Email ---
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
        "email_already_verified": "L'utente è già verificato.",
        "email_sent": "Email di verifica inviata. Controlla la tua casella di posta.",

        # --- API keys (IT) ---
        "ok": "OK",
        "forbidden": "Accesso negato.",
        "user_not_found": "Utente non trovato.",
        "user_already_verified": "L'utente è già verificato.",
        "verification_email_sent": "Email di verifica inviata. Controlla la tua casella di posta.",
        "invalid_or_expired_token": "Link di verifica non valido o scaduto.",
        "internal_server_error": "Errore interno del server.",
        "incorrect_credentials": "Nome utente o password errati.",
        "match_success": "Match!",
        "swipe_registered": "Swipe registrato.",
        "message_sent": "Messaggio inviato.",
        "no_match_cannot_message": "Impossibile inviare il messaggio: nessun match.",
        "chat_access_denied": "Nessun accesso a questa chat.",
        "user_reported": "Utente segnalato con successo.",
        "cannot_report_self": "Non puoi segnalare te stesso.",
        "user_blocked": "Utente bloccato con successo.",
        "user_already_blocked": "L'utente era già bloccato.",
        "cannot_block_self": "Non puoi bloccare te stesso.",
        "match_deleted": "Match eliminato con successo.",
        "photo_deleted": "Foto eliminata con successo.",
        "photo_not_found": "Foto non trovata o senza autorizzazione.",
        "photo_uploaded": "Foto caricata con successo.",
        "no_profile_photo": "L'utente non ha più una foto del profilo.",
        "route_suggestion_error": "Impossibile determinare posizioni recenti di Strava. Assicurati che entrambi gli utenti abbiano un strava_token valido o usa 'mock:LAT,LNG' per i test.",
        "route_suggestion_success": "Suggerimento generato in base all'attività Strava.",
        
        # Strava
        "strava_link": "Collega Strava",
        "strava_linked": "Strava Collegato",
        "strava_unlink": "Scollega Strava",
        "strava_activities": "Attività recenti",
        "strava_not_configured": "Integrazione Strava non configurata",
        "strava_connect_description": "Collega il tuo account Strava per condividere automaticamente le tue attività sportive e trovare migliori corrispondenze.",

        # Validazione/altro
        "no_fields_to_update": "Nessun campo da aggiornare.",
        "day_of_week_invalid": "day_of_week deve essere 0..6.",
        "invalid_time_format": "Formato orario non valido, usa HH:MM.",
        "time_out_of_range": "Ora/minuto fuori intervallo.",
        "end_time_after_start": "end_time deve essere successivo a start_time.",
        "cannot_swipe_self": "Non puoi fare swipe sul tuo stesso profilo.",
        "db_error": "Errore del database.",
        "token_missing": "Impossibile verificare le credenziali.",
        "token_invalid": "Token non valido o scaduto.",
    },
}
