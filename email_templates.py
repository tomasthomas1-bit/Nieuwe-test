# email_templates.py
from typing import Dict

# Simpele i18n voor de HTML-knop en korte zinnen.
# (Voor plain text gebruiken we al translations.py)
EMAIL_I18N: Dict[str, Dict[str, str]] = {
    "nl": {
        "preheader": "Bevestig je e-mailadres voor Athlo.",
        "title": "Bevestig je e-mailadres",
        "hello": "Hallo {name},",
        "intro": "Klik op de knop hieronder om je e-mailadres te bevestigen.",
        "cta": "E-mailadres bevestigen",
        "alt": "Werkt de knop niet? Kopieer en plak onderstaande link in je browser:",
        "ignore": "Heb jij je niet geregistreerd? Dan kun je deze e-mail negeren.",
        "regards": "Sportieve groet,",
        "team": "Het Athlo Team",
    },
    "en": {
        "preheader": "Confirm your email address for Athlo.",
        "title": "Confirm your email address",
        "hello": "Hi {name},",
        "intro": "Click the button below to confirm your email address.",
        "cta": "Confirm email address",
        "alt": "Button not working? Copy and paste the link below into your browser:",
        "ignore": "If you did not sign up, you can safely ignore this email.",
        "regards": "Best regards,",
        "team": "The Athlo Team",
    },
    "fr": {
        "preheader": "Confirmez votre adresse e-mail pour Athlo.",
        "title": "Confirmez votre adresse e-mail",
        "hello": "Bonjour {name},",
        "intro": "Cliquez sur le bouton ci-dessous pour confirmer votre adresse e-mail.",
        "cta": "Confirmer l'adresse e-mail",
        "alt": "Le bouton ne fonctionne pas ? Copiez-collez le lien ci-dessous dans votre navigateur :",
        "ignore": "Si vous ne vous êtes pas inscrit, ignorez cet e-mail.",
        "regards": "Cordialement,",
        "team": "L'équipe Athlo",
    },
    "de": {
        "preheader": "Bestätigen Sie Ihre E‑Mail-Adresse für Athlo.",
        "title": "E‑Mail-Adresse bestätigen",
        "hello": "Hallo {name},",
        "intro": "Klicken Sie unten auf die Schaltfläche, um Ihre E‑Mail‑Adresse zu bestätigen.",
        "cta": "E‑Mail-Adresse bestätigen",
        "alt": "Button funktioniert nicht? Kopieren Sie den folgenden Link in Ihren Browser:",
        "ignore": "Wenn Sie sich nicht registriert haben, ignorieren Sie diese E‑Mail.",
        "regards": "Mit freundlichen Grüßen,",
        "team": "Das Athlo‑Team",
    },
    "es": {
        "preheader": "Confirma tu correo electrónico para Athlo.",
        "title": "Confirma tu correo electrónico",
        "hello": "Hola {name},",
        "intro": "Haz clic en el botón de abajo para confirmar tu correo electrónico.",
        "cta": "Confirmar correo electrónico",
        "alt": "¿No funciona el botón? Copia y pega el siguiente enlace en tu navegador:",
        "ignore": "Si no te registraste, puedes ignorar este correo.",
        "regards": "Saludos,",
        "team": "El equipo de Athlo",
    },
    "pt": {
        "preheader": "Confirme seu e‑mail para o Athlo.",
        "title": "Confirme seu e‑mail",
        "hello": "Olá {name},",
        "intro": "Clique no botão abaixo para confirmar seu e‑mail.",
        "cta": "Confirmar e‑mail",
        "alt": "O botão não funciona? Copie e cole o link abaixo no seu navegador:",
        "ignore": "Se você não se registrou, pode ignorar este e‑mail.",
        "regards": "Atenciosamente,",
        "team": "Equipe Athlo",
    },
    "it": {
        "preheader": "Conferma la tua email per Athlo.",
        "title": "Conferma la tua email",
        "hello": "Ciao {name},",
        "intro": "Fai clic sul pulsante qui sotto per confermare la tua email.",
        "cta": "Conferma email",
        "alt": "Il pulsante non funziona? Copia e incolla il link qui sotto nel tuo browser:",
        "ignore": "Se non ti sei registrato tu, ignora pure questa email.",
        "regards": "Cordiali saluti,",
        "team": "Il team di Athlo",
    },
}

def render_verification_email_html(name: str, link: str, lang: str = "nl") -> str:
    i = EMAIL_I18N.get(lang, EMAIL_I18N["en"])
    # Basic responsive/email-safe HTML met inline CSS
    return f"""\
<!doctype html>
<html lang="{lang}">
  <head>
    <meta charset="utf-8">
    <meta name="x-apple-disable-message-reformatting">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{i["title"]}</title>
    <style>
      body {{ margin:0; padding:0; background:#f6f7fb; color:#222; font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif; }}
      .container {{ max-width:600px; margin:0 auto; background:#ffffff; border-radius:12px; overflow:hidden; box-shadow:0 2px 12px rgba(0,0,0,0.06); }}
      .header {{ padding:24px 24px 0 24px; }}
      .brand {{ font-weight:700; color:#0b5cff; font-size:14px; letter-spacing:0.5px; text-transform:uppercase; }}
      .title {{ font-size:24px; font-weight:800; margin:8px 0 0 0; }}
      .content {{ padding:16px 24px 24px 24px; font-size:16px; line-height:1.6; }}
      .cta-wrap {{ text-align:center; margin:24px 0; }}
      .btn {{ display:inline-block; background:#0b5cff; color:#fff !important; text-decoration:none; padding:12px 20px; border-radius:8px; font-weight:700; }}
      .linkbox {{ word-break:break-all; background:#f2f4ff; border-radius:8px; padding:10px 12px; font-size:14px; }}
      .footer {{ color:#666; font-size:13px; padding:0 24px 24px 24px; }}
      .preheader {{ display:none; visibility:hidden; opacity:0; color:transparent; height:0; width:0; overflow:hidden; }}
      @media (prefers-color-scheme: dark) {{
        body {{ background:#0e1117; color:#e6edf3; }}
        .container {{ background:#161b22; box-shadow:none; }}
        .linkbox {{ background:#0b213f; }}
      }}
    </style>
  </head>
  <body>
    <div class="preheader">{i["preheader"]}</div>
    <div class="container">
      <div class="header">
        <div class="brand">Athlo</div>
        <h1 class="title">{i["title"]}</h1>
      </div>
      <div class="content">
        <p>{i["hello"].format(name=name)}</p>
        <p>{i["intro"]}</p>
        <div class="cta-wrap">
          {link}{i["cta"]}</a>
        </div>
        <p><strong>{i["alt"]}</strong></p>
        <div class="linkbox">{link}</div>
        <p>{i["ignore"]}</p>
        <p>{i["regards"]}<br>{i["team"]}</p>
      </div>
      <div class="footer">
        © {i["team"]}. Alle rechten voorbehouden.
      </div>
    </div>
  </body>
</html>
"""
