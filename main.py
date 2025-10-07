# main.py
from __future__ import annotations

import logging
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Any, List, Optional, Tuple

import psycopg2
from cryptography.fernet import Fernet
from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Request,
    Response,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from haversine import Unit, haversine
from jose import JWTError, jwt
import bcrypt
from psycopg2.pool import ThreadedConnectionPool
from pydantic import BaseModel, Field, HttpUrl, validator
import uvicorn

# -------------------- Config & Logging --------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("app")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7  # future use
COOKIE_NAME = "access_token"

# -------------------- Env & Secrets --------------------
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL omgevingsvariabele is niet ingesteld.")

SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY omgevingsvariabele is niet ingesteld.")

ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY")
if not ENCRYPTION_KEY:
    raise RuntimeError("ENCRYPTION_KEY omgevingsvariabele is niet ingesteld.")

cipher_suite = Fernet(ENCRYPTION_KEY.encode("utf-8"))

GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY")
FRONTEND_ORIGINS = os.environ.get("FRONTEND_ORIGINS", "")  # bv: "https://app...,https://staging..."
_allowed_origins = [o.strip() for o in FRONTEND_ORIGINS.split(",") if o.strip()]

# -------------------- App init --------------------
app = FastAPI(title="Sports Match API", version="2.1.0")

# CORS
if _allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# -------------------- DB Pool & Helpers --------------------
pool: Optional[ThreadedConnectionPool] = None


def init_pool() -> None:
    """Initialiseer één thread-safe connection pool voor de app."""
    global pool
    if pool is None:
        pool = ThreadedConnectionPool(minconn=1, maxconn=10, dsn=DATABASE_URL)
        logger.info("PostgreSQL connection pool geïnitialiseerd.")


class DB:
    """Contextmanager voor (conn, cur) per request."""

    def __enter__(self) -> Tuple[psycopg2.extensions.connection, psycopg2.extensions.cursor]:
        if pool is None:
            raise RuntimeError("DB pool is niet geïnitialiseerd.")
        self.conn = pool.getconn()
        self.cur = self.conn.cursor()
        return self.conn, self.cur

    def __exit__(self, exc_type, exc, tb):
        try:
            if exc:
                self.conn.rollback()
            else:
                self.conn.commit()
        finally:
            self.cur.close()
            if pool:
                pool.putconn(self.conn)


def get_db():
    with DB() as (conn, cur):
        yield conn, cur


# -------------------- Password & Token --------------------
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

    @validator("password")
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Wachtwoord moet minimaal 8 karakters lang zijn.")
        if not re.search(r"[a-z]", v):
            raise ValueError("Wachtwoord moet minimaal één kleine letter bevatten.")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Wachtwoord moet minimaal één hoofdletter bevatten.")
        if not re.search(r"[0-9]", v):
            raise ValueError("Wachtwoord moet minimaal één cijfer bevatten.")
        if not re.search(r"[\\#\\?!@$%^&*\\-]", v):
            raise ValueError("Wachtwoord moet minimaal één speciaal karakter bevatten.")
        return v


class UserInDB(UserBase):
    password_hash: str


class Token(BaseModel):
    access_token: str
    token_type: str


class UserPhoto(BaseModel):
    id: int
    photo_url: str
    is_profile_pic: bool


class UserProfile(BaseModel):
    id: int
    name: str
    age: int
    bio: Optional[str] = None
    sport_type: str
    avg_distance: float
    lat: float
    lng: float
    photos: List[str] = []
    photos_meta: List[UserPhoto] = []
    strava_ytd_url: Optional[str] = None


class UserPreferences(BaseModel):
    preferred_sport_type: Optional[str] = None
    preferred_min_age: Optional[int] = Field(None, gt=0, lt=100)
    preferred_max_age: Optional[int] = Field(None, gt=0, lt=100)


class MessageIn(BaseModel):
    match_id: int
    message: str


class ChatMessage(BaseModel):
    sender_id: int
    message: str
    timestamp: str  # ISO8601


class ReportRequest(BaseModel):
    reported_id: int
    reason: str


class PhotoUpload(BaseModel):
    photo_url: HttpUrl
    is_profile_pic: Optional[bool] = False


# -------------------- Auth Dependency --------------------
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    request: Request = None,
    db=Depends(get_db),
):
    conn, c = db
    if not token and request:
        token = get_bearer_from_cookie(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kon validatiegegevens niet verifiëren.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Token zonder subject.")
    except JWTError:
        raise HTTPException(status_code=401, detail="Ongeldige of verlopen token.")

    c.execute(
        """
        SELECT id, username, name, age, bio, sport_type, avg_distance, last_lat, last_lng, availability,
               preferred_sport_type, preferred_min_age, preferred_max_age, strava_token
        FROM users
        WHERE username = %s AND deleted_at IS NULL
        """,
        (username,),
    )
    row = c.fetchone()
    if not row:
        raise HTTPException(status_code=401, detail="Gebruiker niet gevonden of gedeactiveerd.")

    user = {
        "id": row[0],
        "username": row[1],
        "name": row[2],
        "age": row[3],
        "bio": row[4],
        "sport_type": row[5],
        "avg_distance": row[6],
        "last_lat": row[7],
        "last_lng": row[8],
        "availability": row[9],
        "preferred_sport_type": row[10],
        "preferred_min_age": row[11],
        "preferred_max_age": row[12],
        "strava_token": row[13],
    }
    return user


# -------------------- Startup / Shutdown --------------------
@app.on_event("startup")
def on_startup():
    init_pool()
    with DB() as (conn, c):
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE,
                password_hash TEXT,
                name TEXT,
                age INTEGER,
                bio TEXT,
                sport_type TEXT,
                avg_distance REAL,
                last_lat REAL,
                last_lng REAL,
                availability TEXT,
                strava_token TEXT,
                preferred_sport_type TEXT,
                preferred_min_age INTEGER,
                preferred_max_age INTEGER,
                push_token TEXT,
                deleted_at TIMESTAMPTZ
            )
            """
        )
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS swipes (
                swiper_id INTEGER,
                swipee_id INTEGER,
                liked BOOLEAN,
                deleted_at TIMESTAMPTZ,
                PRIMARY KEY (swiper_id, swipee_id)
            )
            """
        )
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS chats (
                id SERIAL PRIMARY KEY,
                match_id INTEGER,
                sender_id INTEGER,
                encrypted_message TEXT,
                timestamp TIMESTAMPTZ DEFAULT NOW(),
                deleted_at TIMESTAMPTZ
            )
            """
        )
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS user_photos (
                id SERIAL PRIMARY KEY,
                user_id INTEGER,
                photo_url TEXT,
                is_profile_pic INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
        )
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS user_blocks (
                blocker_id INTEGER,
                blocked_id INTEGER,
                timestamp TIMESTAMPTZ,
                PRIMARY KEY (blocker_id, blocked_id)
            )
            """
        )
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS user_reports (
                id SERIAL PRIMARY KEY,
                reporter_id INTEGER,
                reported_id INTEGER,
                reason TEXT,
                timestamp TIMESTAMPTZ
            )
            """
        )
        c.execute('CREATE INDEX IF NOT EXISTS idx_users_username ON users (username)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_swipes_swiper_swipee ON swipes (swiper_id, swipee_id)')
        c.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_swipes_swiper_liked
              ON swipes (swiper_id, liked)
              WHERE deleted_at IS NULL
            """
        )
        c.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_blocks_pair
              ON user_blocks (blocker_id, blocked_id)
            """
        )
        c.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_chats_match
              ON chats (match_id)
              WHERE deleted_at IS NULL
            """
        )


@app.on_event("shutdown")
def on_shutdown():
    global pool
    if pool:
        pool.closeall()
        logger.info("PostgreSQL connection pool afgesloten.")
        pool = None


# -------------------- Endpoints --------------------
@app.post("/token", response_model=Token)
async def login_for_access_token(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db=Depends(get_db),
):
    conn, c = db
    try:
        c.execute(
            "SELECT password_hash FROM users WHERE username = %s AND deleted_at IS NULL",
            (form_data.username,),
        )
        row = c.fetchone()
        if not row or not verify_password(form_data.password, row[0]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrecte gebruikersnaam of wachtwoord",
                headers={"WWW-Authenticate": "Bearer"},
            )
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(data={"sub": form_data.username}, expires_delta=access_token_expires)

        response.set_cookie(
            key=COOKIE_NAME,
            value=access_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception:
        logger.exception("Fout bij het genereren van een token.")
        raise HTTPException(status_code=500, detail="Interne serverfout bij tokenaanmaak.")


@app.post("/register")
async def create_user(user: UserCreate, db=Depends(get_db)):
    conn, c = db
    password_hash = get_password_hash(user.password)
    try:
        c.execute(
            """
            INSERT INTO users (username, password_hash, name, age, bio, sport_type, avg_distance,
                               last_lat, last_lng, availability)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            RETURNING id
            """,
            (user.username, password_hash, user.name, user.age, user.bio, user.sport_type,
             user.avg_distance, user.last_lat, user.last_lng, user.availability),
        )
        user_id = c.fetchone()[0]

        default_photo_url = "https://example.com/default-profile.png"
        c.execute(
            "INSERT INTO user_photos (user_id, photo_url, is_profile_pic) VALUES (%s,%s,%s)",
            (user_id, default_photo_url, 1),
        )
        logger.info("Nieuwe gebruiker aangemaakt: %s", user.username)
        return {
            "status": "success",
            "user_id": user_id,
            "username": user.username,
            "profile_pic_url": default_photo_url,
        }
    except psycopg2.Error:
        logger.exception("Databasefout bij het aanmaken van gebruiker.")
        raise HTTPException(status_code=500, detail="Databasefout bij het aanmaken van gebruiker.")
    except Exception:
        logger.exception("Algemene fout bij het aanmaken van gebruiker.")
        raise HTTPException(status_code=500, detail="Interne serverfout")


@app.get("/users/{user_id}", response_model=UserProfile)
async def read_user(user_id: int, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    conn, c = db
    c.execute(
        """
        SELECT id, name, age, bio, sport_type, avg_distance, last_lat, last_lng, availability, strava_token
        FROM users
        WHERE id = %s AND deleted_at IS NULL
        """,
        (user_id,),
    )
    user = c.fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="Gebruiker niet gevonden")

    # Photos (urls + metadata)
    c.execute(
        "SELECT id, photo_url, is_profile_pic FROM user_photos WHERE user_id = %s ORDER BY id ASC",
        (user_id,),
    )
    rows = c.fetchall()
    photos = [r[1] for r in rows]
    photos_meta = [{"id": r[0], "photo_url": r[1], "is_profile_pic": bool(r[2])} for r in rows]
    strava_ytd_url = f"https://www.strava.com/athletes/{user[9]}/ytd" if user[9] else None

    logger.info("Gebruiker %s bekijkt profiel van gebruiker %s.", current_user['id'], user_id)
    return {
        "id": user[0],
        "name": user[1],
        "age": user[2],
        "bio": user[3],
        "sport_type": user[4],
        "avg_distance": user[5],
        "lat": user[6],
        "lng": user[7],
        "photos": photos,
        "photos_meta": photos_meta,
        "strava_ytd_url": strava_ytd_url,
    }


@app.post("/users/{user_id}/preferences")
async def update_user_preferences(
    user_id: int,
    preferences: UserPreferences,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    if user_id != current_user['id']:
        raise HTTPException(status_code=403, detail="Geen toestemming om deze voorkeuren bij te werken.")

    conn, c = db
    try:
        c.execute(
            """
            UPDATE users
            SET preferred_sport_type=%s, preferred_min_age=%s, preferred_max_age=%s
            WHERE id=%s AND deleted_at IS NULL
            """,
            (preferences.preferred_sport_type, preferences.preferred_min_age, preferences.preferred_max_age, user_id),
        )
        logger.info("Voorkeuren van gebruiker %s succesvol bijgewerkt.", user_id)
        return {"status": "success", "message": "Voorkeuren succesvol bijgewerkt."}
    except psycopg2.Error:
        logger.exception("Databasefout bij het bijwerken van voorkeuren.")
        raise HTTPException(status_code=500, detail="Databasefout bij het bijwerken van voorkeuren.")


@app.get("/suggestions")
async def get_suggestions(current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    conn, c = db
    user_id = current_user['id']
    lat = current_user['last_lat']
    lng = current_user['last_lng']
    sport_type = current_user.get('preferred_sport_type')
    min_age = current_user.get('preferred_min_age')
    max_age = current_user.get('preferred_max_age')

    query = """
        SELECT u.id, u.name, u.age, u.bio, u.sport_type, u.avg_distance, u.last_lat, u.last_lng
        FROM users u
        WHERE u.id <> %s
          AND u.deleted_at IS NULL
          AND NOT EXISTS (SELECT 1 FROM user_blocks b WHERE b.blocker_id = %s AND b.blocked_id = u.id)
          AND NOT EXISTS (SELECT 1 FROM user_blocks b WHERE b.blocker_id = u.id AND b.blocked_id = %s)
          AND NOT EXISTS (SELECT 1 FROM swipes s WHERE s.swiper_id = %s AND s.swipee_id = u.id)
    """
    params: List[Any] = [user_id, user_id, user_id, user_id]
    if sport_type:
        query += " AND u.sport_type = %s"
        params.append(sport_type)
    if min_age:
        query += " AND u.age >= %s"
        params.append(min_age)
    if max_age:
        query += " AND u.age <= %s"
        params.append(max_age)
    query += " LIMIT 200"

    c.execute(query, tuple(params))
    suggestions = c.fetchall()
    if not suggestions:
        return {"suggestions": []}

    suggestions_with_dist = []
    for s in suggestions:
        distance = haversine((lat, lng), (s[6], s[7]), unit=Unit.KILOMETERS)
        if distance <= 250:
            suggestions_with_dist.append(
                {
                    "id": s[0],
                    "name": s[1],
                    "age": s[2],
                    "bio": s[3],
                    "sport_type": s[4],
                    "avg_distance": s[5],
                    "lat": s[6],
                    "lng": s[7],
                    "distance_km": round(distance, 2),
                }
            )
    suggestions_with_dist.sort(key=lambda x: x['distance_km'])
    logger.info("Suggesties gegenereerd voor gebruiker %s. Aantal: %d", user_id, len(suggestions_with_dist))
    return {"suggestions": suggestions_with_dist}


@app.post("/swipe/{swipee_id}")
async def swipe(
    swipee_id: int,
    liked: bool,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    conn, c = db
    swiper_id = current_user['id']
    if swiper_id == swipee_id:
        raise HTTPException(status_code=400, detail="Je kunt niet op je eigen profiel swipen.")

    try:
        c.execute(
            """
            INSERT INTO swipes (swiper_id, swipee_id, liked, deleted_at)
            VALUES (%s, %s, %s, NULL)
            ON CONFLICT (swiper_id, swipee_id)
            DO UPDATE SET liked = EXCLUDED.liked, deleted_at = NULL
            """,
            (swiper_id, swipee_id, liked),
        )
        logger.info("Gebruiker %s heeft op gebruiker %s geswipet (liked: %s).", swiper_id, swipee_id, liked)

        match = False
        if liked:
            c.execute(
                """
                SELECT 1
                FROM swipes
                WHERE swiper_id = %s
                  AND swipee_id = %s
                  AND liked = TRUE
                  AND deleted_at IS NULL
                """,
                (swipee_id, swiper_id),
            )
            if c.fetchone():
                match = True
                logger.info("Nieuwe match tussen gebruiker %s en gebruiker %s.", swiper_id, swipee_id)

        return {"status": "success", "message": "Match!" if match else "Swipe geregistreerd.", "match": match}
    except psycopg2.Error:
        logger.exception("Databasefout bij het swipen.")
        raise HTTPException(status_code=500, detail="Databasefout bij het swipen.")


@app.get("/matches")
async def get_matches(current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    conn, c = db
    user_id = current_user['id']
    c.execute(
        """
        SELECT u.id, u.name, u.age, up.photo_url
        FROM users u
        JOIN swipes s1
          ON s1.swipee_id = u.id
         AND s1.swiper_id = %s
         AND s1.liked = TRUE
         AND s1.deleted_at IS NULL
        LEFT JOIN LATERAL (
            SELECT photo_url
            FROM user_photos up
            WHERE up.user_id = u.id AND up.is_profile_pic = 1
            ORDER BY up.id DESC
            LIMIT 1
        ) up ON TRUE
        WHERE u.deleted_at IS NULL
          AND EXISTS (
            SELECT 1
            FROM swipes s2
            WHERE s2.swiper_id = u.id
              AND s2.swipee_id = %s
              AND s2.liked = TRUE
              AND s2.deleted_at IS NULL
          )
        """,
        (user_id, user_id),
    )
    rows = c.fetchall()
    matches = [{"id": r[0], "name": r[1], "age": r[2], "photo_url": r[3]} for r in rows]
    return {"matches": matches}


@app.post("/send_message")
async def send_message(message: MessageIn, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    conn, c = db
    user_id = current_user['id']
    match_id = message.match_id
    plain_message = message.message
    timestamp = datetime.now(timezone.utc)

    c.execute(
        """
        SELECT 1
        FROM swipes
        WHERE (
            swiper_id = %s
            AND swipee_id = %s
            AND liked = TRUE
            AND deleted_at IS NULL
        )
          AND EXISTS (
            SELECT 1
            FROM swipes
            WHERE swiper_id = %s
              AND swipee_id = %s
              AND liked = TRUE
              AND deleted_at IS NULL
          )
        """,
        (user_id, match_id, match_id, user_id),
    )
    if not c.fetchone():
        raise HTTPException(status_code=403, detail="Bericht kan niet worden verzonden: geen match.")

    encrypted_message = cipher_suite.encrypt(plain_message.encode("utf-8")).decode("utf-8")
    c.execute(
        """
        INSERT INTO chats (match_id, sender_id, encrypted_message, timestamp)
        VALUES (%s, %s, %s, %s)
        """,
        (match_id, user_id, encrypted_message, timestamp),
    )
    logger.info("Chatbericht van gebruiker %s naar gebruiker %s opgeslagen.", user_id, match_id)
    return {"status": "success", "message": "Bericht verzonden."}


@app.get("/chat/{match_id}/messages")
async def get_chat_messages(match_id: int, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    conn, c = db
    user_id = current_user['id']

    c.execute(
        """
        SELECT 1
        FROM swipes
        WHERE (
            swiper_id = %s
            AND swipee_id = %s
            AND liked = TRUE
            AND deleted_at IS NULL
        )
          AND EXISTS (
            SELECT 1
            FROM swipes
            WHERE swiper_id = %s
              AND swipee_id = %s
              AND liked = TRUE
              AND deleted_at IS NULL
          )
        """,
        (user_id, match_id, match_id, user_id),
    )
    if not c.fetchone():
        raise HTTPException(status_code=403, detail="Geen toegang tot deze chat.")

    c.execute(
        """
        SELECT sender_id, encrypted_message, timestamp
        FROM chats
        WHERE match_id = %s AND (deleted_at IS NULL)
        ORDER BY timestamp ASC
        """,
        (match_id,),
    )
    rows = c.fetchall()

    chat_history: List[ChatMessage] = []
    for sender_id, encrypted_message, ts in rows:
        try:
            decrypted = cipher_suite.decrypt(encrypted_message.encode("utf-8")).decode("utf-8")
            iso_ts = ts.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
            chat_history.append(ChatMessage(sender_id=sender_id, message=decrypted, timestamp=iso_ts))
        except Exception:
            logger.exception("Fout bij decoderen van bericht.")
            continue

    return {"chat_history": chat_history}


@app.post("/report_user")
async def report_user(report: ReportRequest, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    conn, c = db
    reporter_id = current_user['id']
    if reporter_id == report.reported_id:
        raise HTTPException(status_code=400, detail="Je kunt jezelf niet rapporteren.")

    try:
        c.execute(
            """
            INSERT INTO user_reports (reporter_id, reported_id, reason, timestamp)
            VALUES (%s, %s, %s, %s)
            """,
            (reporter_id, report.reported_id, report.reason, datetime.now(timezone.utc)),
        )
        logger.info("Gebruiker %s gerapporteerd door gebruiker %s.", report.reported_id, reporter_id)
        return {"status": "success", "message": "Gebruiker succesvol gerapporteerd."}
    except psycopg2.Error:
        logger.exception("Databasefout bij rapporteren van gebruiker.")
        raise HTTPException(status_code=500, detail="Databasefout bij het rapporteren van gebruiker.")


@app.post("/block_user")
async def block_user(user_to_block_id: int, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    conn, c = db
    blocker_id = current_user['id']
    if blocker_id == user_to_block_id:
        raise HTTPException(status_code=400, detail="Je kunt jezelf niet blokkeren.")

    try:
        c.execute(
            """
            INSERT INTO user_blocks (blocker_id, blocked_id, timestamp)
            VALUES (%s, %s, %s)
            ON CONFLICT (blocker_id, blocked_id) DO NOTHING
            """,
            (blocker_id, user_to_block_id, datetime.now(timezone.utc)),
        )
        if c.rowcount == 0:
            logger.info("Gebruiker %s was al geblokkeerd door gebruiker %s.", user_to_block_id, blocker_id)
            return {"status": "success", "message": "Gebruiker was al geblokkeerd."}

        logger.info("Gebruiker %s succesvol geblokkeerd door gebruiker %s.", user_to_block_id, blocker_id)
        return {"status": "success", "message": "Gebruiker succesvol geblokkeerd."}
    except psycopg2.Error:
        logger.exception("Databasefout bij het blokkeren van gebruiker.")
        raise HTTPException(status_code=500, detail="Databasefout bij het blokkeren van gebruiker.")


@app.delete("/delete/match/{match_id}")
async def delete_match(match_id: int, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    conn, c = db
    user_id = current_user['id']
    c.execute(
        """
        UPDATE swipes
        SET deleted_at = NOW()
        WHERE (
            (swiper_id = %s AND swipee_id = %s AND liked = TRUE)
            OR (swiper_id = %s AND swipee_id = %s AND liked = TRUE)
        )
        """,
        (user_id, match_id, match_id, user_id),
    )
    logger.info("Match met gebruiker %s soft-verwijderd door gebruiker %s.", match_id, user_id)
    return {"status": "success", "message": "Match succesvol soft-verwijderd."}


@app.delete("/delete_photo/{photo_id}")
async def delete_photo(photo_id: int, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    conn, c = db
    user_id = current_user['id']
    try:
        c.execute("SELECT is_profile_pic FROM user_photos WHERE id = %s AND user_id = %s", (photo_id, user_id))
        row = c.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Foto niet gevonden of geen permissie.")
        was_profile = row[0] == 1

        c.execute("DELETE FROM user_photos WHERE id = %s AND user_id = %s", (photo_id, user_id))
        if c.rowcount == 0:
            raise HTTPException(status_code=404, detail="Foto niet gevonden.")

        if was_profile:
            c.execute("SELECT id FROM user_photos WHERE user_id = %s LIMIT 1", (user_id,))
            new_pic = c.fetchone()
            if new_pic:
                c.execute("UPDATE user_photos SET is_profile_pic = 1 WHERE id = %s", (new_pic[0],))
                logger.info("Nieuwe profielfoto %s toegewezen voor gebruiker %s.", new_pic[0], user_id)
            else:
                logger.warning("Gebruiker %s heeft geen profielfoto meer.", user_id)

        logger.info("Foto %s verwijderd voor gebruiker %s.", photo_id, user_id)
        return {"status": "success", "message": "Foto succesvol verwijderd."}
    except psycopg2.Error:
        logger.exception("Databasefout bij foto-verwijderen.")
        raise HTTPException(status_code=500, detail="Databasefout bij het verwijderen van een foto.")


@app.post("/upload_photo")
async def upload_photo(photo: PhotoUpload, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    conn, c = db
    user_id = current_user['id']
    photo_url = str(photo.photo_url)
    try:
        if photo.is_profile_pic:
            c.execute("UPDATE user_photos SET is_profile_pic = 0 WHERE user_id = %s", (user_id,))
        c.execute(
            "INSERT INTO user_photos (user_id, photo_url, is_profile_pic) VALUES (%s,%s,%s)",
            (user_id, photo_url, int(bool(photo.is_profile_pic))),
        )
        logger.info(
            "Nieuwe foto geüpload voor gebruiker %s. URL: %s (profile: %s)",
            user_id,
            photo_url,
            bool(photo.is_profile_pic),
        )
        return {"status": "success", "message": "Foto succesvol geüpload."}
    except psycopg2.Error:
        logger.exception("Databasefout bij foto-upload.")
        raise HTTPException(status_code=500, detail="Databasefout bij het uploaden van een foto.")


# -------------------- WebSocket (auth via token query-param) --------------------
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4401)
        return
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            await websocket.close(code=4401)
            return
    except JWTError:
        await websocket.close(code=4401)
        return

    await websocket.accept()
    logger.info("WebSocket geaccepteerd voor gebruiker %s (via token).", user_id)
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Bericht ontvangen: {data}")
    except WebSocketDisconnect:
        logger.info("WebSocket gesloten voor gebruiker %s.", user_id)
    except Exception:
        logger.exception("WebSocket fout voor gebruiker %s.", user_id)


# -------------------- Route Suggestion --------------------
@app.get("/suggest_route/{match_id}")
async def get_route_suggestion(match_id: int, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    conn, c = db
    user_id = current_user['id']

    c.execute(
        """
        SELECT 1
        FROM swipes
        WHERE (
            swiper_id = %s
            AND swipee_id = %s
            AND liked = TRUE
            AND deleted_at IS NULL
        )
          AND EXISTS (
            SELECT 1
            FROM swipes
            WHERE swiper_id = %s
              AND swipee_id = %s
              AND liked = TRUE
              AND deleted_at IS NULL
          )
        """,
        (user_id, match_id, match_id, user_id),
    )
    if not c.fetchone():
        raise HTTPException(status_code=403, detail="Geen toegang tot routevoorstellen (geen match).")

    c.execute("SELECT last_lat, last_lng FROM users WHERE id = %s", (user_id,))
    u = c.fetchone()
    c.execute("SELECT last_lat, last_lng FROM users WHERE id = %s", (match_id,))
    m = c.fetchone()
    if not u or not m:
        raise HTTPException(status_code=404, detail="Locatiegegevens niet gevonden.")

    user_location = (u[0], u[1])
    match_location = (m[0], m[1])
    distance_km = haversine(user_location, match_location, unit=Unit.KILOMETERS)
    map_link = f"https://www.google.com/maps/dir/{user_location[0]},{user_location[1]}/{match_location[0]},{match_location[1]}"

    popular_route = {
        "name": "Voorstel gezamenlijke route",
        "description": "Voorbeeld: een route ongeveer halverwege jullie locaties. Pas aan op basis van voorkeur.",
        "distance_km": round(distance_km / 2, 2),
        "map_link": map_link,
    }
    logger.info("Routevoorstel gegenereerd voor match %s-%s.", user_id, match_id)
    return {"status": "success", "route_suggestion": popular_route}


# -------------------- Health --------------------
@app.get("/healthz")
def healthz(db=Depends(get_db)):
    conn, c = db
    c.execute("SELECT 1")
    return {"status": "ok"}


# -------------------- Main --------------------
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8000")),
        reload=True,
    )


from fastapi.responses import HTMLResponse

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <html>
        <head><title>Sports Match API</title></head>
        <body style="font-family: sans-serif; text-align: center; margin-top: 50px;">
            <h1>Sports Match API is live! ✅</h1>
            <p>Bekijk de /docsAPI Docs</a> of /redocRedoc</a>.</p>
        </body>
    </html>
    """

