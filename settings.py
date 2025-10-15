from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
import logging

router = APIRouter()
logger = logging.getLogger("settings")

# Dummy dependencies voor standalone test
def get_current_user():
    return {"id": 1}

def get_db():
    import psycopg2
    conn = psycopg2.connect("dbname=test user=postgres password=secret")
    return conn, conn.cursor()

class MessagePreference(str, Enum):
    everyone = "everyone"
    matches = "matches"
    none = "none"

class MatchGoal(str, Enum):
    friendship = "friendship"
    training_partner = "training_partner"
    competition = "competition"
    coaching = "coaching"

class GenderPreference(str, Enum):
    any = "any"
    male = "male"
    female = "female"
    non_binary = "non_binary"

class UserSettings(BaseModel):
    sports: List[str] = Field(default_factory=list)
    show_location: bool = True
    allow_messages_from: MessagePreference = Field(default=MessagePreference.everyone)
    strava_token: Optional[str] = None
    garmin_token: Optional[str] = None
    match_goal: Optional[MatchGoal] = None
    preferred_gender: Optional[GenderPreference] = GenderPreference.any
    max_distance_km: Optional[int] = 50
    notifications_enabled: Optional[bool] = True

@router.get("/users/{user_id}/settings", response_model=UserSettings)
def get_user_settings(user_id: int, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    if user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Geen toegang tot instellingen van andere gebruikers.")
    conn, c = db
    c.execute("""
        SELECT sports, show_location, allow_messages_from, strava_token, garmin_token,
               match_goal, preferred_gender, max_distance_km, notifications_enabled
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
        garmin_token=row[4],
        match_goal=row[5],
        preferred_gender=row[6],
        max_distance_km=row[7],
        notifications_enabled=row[8]
    )

@router.post("/users/{user_id}/settings")
def update_user_settings(user_id: int, settings: UserSettings, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    if user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Geen toestemming om instellingen bij te werken.")
    conn, c = db
    try:
        c.execute("""
            INSERT INTO user_settings (
                user_id, sports, show_location, allow_messages_from, strava_token, garmin_token,
                match_goal, preferred_gender, max_distance_km, notifications_enabled
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id)
            DO UPDATE SET
                sports = EXCLUDED.sports,
                show_location = EXCLUDED.show_location,
                allow_messages_from = EXCLUDED.allow_messages_from,
                strava_token = EXCLUDED.strava_token,
                garmin_token = EXCLUDED.garmin_token,
                match_goal = EXCLUDED.match_goal,
                preferred_gender = EXCLUDED.preferred_gender,
                max_distance_km = EXCLUDED.max_distance_km,
                notifications_enabled = EXCLUDED.notifications_enabled
        """, (
            user_id,
            settings.sports,
            settings.show_location,
            settings.allow_messages_from.value,
            settings.strava_token,
            settings.garmin_token,
            settings.match_goal,
            settings.preferred_gender,
            settings.max_distance_km,
            settings.notifications_enabled
        ))
        conn.commit()
        return {"status": "success", "message": "Instellingen succesvol opgeslagen."}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
