from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
from main import get_current_user, get_db
import logging

router = APIRouter()
logger = logging.getLogger("settings")

class MessagePreference(str, Enum):
    everyone = "everyone"
    matches = "matches"
    none = "none"

class UserSettings(BaseModel):
    sports: List[str] = Field(default_factory=list)
    show_location: bool = True
    allow_messages_from: MessagePreference = Field(default=MessagePreference.everyone)
    strava_token: Optional[str] = None
    garmin_token: Optional[str] = None

@router.get("/users/{user_id}/settings", response_model=UserSettings)
async def get_user_settings(user_id: int, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    if user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Geen toegang tot instellingen van andere gebruikers.")
    conn, c = db
    c.execute("""
        SELECT sports, show_location, allow_messages_from, strava_token, garmin_token
        FROM user_settings
        WHERE user_id = %s
    """, (user_id,))
    row = c.fetchone()
    if not row:
        return UserSettings()
    return UserSettings(
        sports=row[0] or [],
        show_location=row[1],
        allow_messages_from=row[2],
        strava_token=row[3],
        garmin_token=row[4]
    )

@router.post("/users/{user_id}/settings")
async def update_user_settings(user_id: int, settings: UserSettings, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    if user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Geen toestemming om instellingen bij te werken.")
    conn, c = db
    try:
        c.execute("""
            INSERT INTO user_settings (user_id, sports, show_location, allow_messages_from, strava_token, garmin_token)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id)
            DO UPDATE SET sports = EXCLUDED.sports,
                          show_location = EXCLUDED.show_location,
                          allow_messages_from = EXCLUDED.allow_messages_from,
                          strava_token = EXCLUDED.strava_token,
                          garmin_token = EXCLUDED.garmin_token
        """, (user_id, settings.sports, settings.show_location, settings.allow_messages_from.value, settings.strava_token, settings.garmin_token))
        logger.info("Instellingen bijgewerkt voor gebruiker %s", user_id)
        return {"status": "success", "message": "Instellingen succesvol opgeslagen."}
    except Exception:
        logger.exception("Fout bij instellingen update.")
        raise HTTPException(status_code=500, detail="Databasefout bij het opslaan van instellingen.")
