# main.py
from __future__ import annotations

from translations import translations
def get_lang(user: dict) -> str:
    lang = user.get("language", "nl")
    return lang if lang in translations else "en"

def t(key: str, lang: str) -> str:
    return translations.get(lang, translations["en"]).get(key, key)

import logging
import os
import re
import traceback
from datetime import datetime, timedelta, timezone
from typing import Any, List, Optional, Tuple, Dict, Iterable

import bcrypt
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
    Header,
)
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from haversine import Unit, haversine
from jose import JWTError, jwt
from psycopg2.pool import ThreadedConnectionPool
from pydantic import BaseModel, Field, HttpUrl, validator
import uvicorn

# ------------------------- Config & Logging -------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("app")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = 7
COOKIE_NAME = "access_token"

# ------------------------- Env & Secrets ---------------------------
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

GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY")  # optioneel
FRONTEND_ORIGINS = os.environ.get("FRONTEND_ORIGINS", "")  # bv. "https://app...,https://staging..."
_allowed_origins = [o.strip() for o in FRONTEND_ORIGINS.split(",") if o.strip()]

# Strava OAuth configuratie
STRAVA_CLIENT_ID = os.environ.get("STRAVA_CLIENT_ID")
STRAVA_CLIENT_SECRET = os.environ.get("STRAVA_CLIENT_SECRET")
STRAVA_REDIRECT_URI = os.environ.get("STRAVA_REDIRECT_URI", "http://localhost:8000/strava/callback")
REPLIT_DEV_DOMAIN = os.environ.get("REPLIT_DEV_DOMAIN", "")

# ------------------------- App init --------------------------------
app = FastAPI(title="Sports Match API", version="2.2.0")

# Middleware: log of auth header/cookie aanwezig is
@app.middleware("http")
async def log_requests_and_responses(request: Request, call_next):
    has_auth_header = "authorization" in request.headers
    has_auth_cookie = COOKIE_NAME in request.cookies
    logger.info(
        "Request: %s %s (auth_header=%s, auth_cookie=%s)",
        request.method,
        request.url.path,
        has_auth_header,
        has_auth_cookie,
    )
    try:
        response = await call_next(request)
        logger.info(
            "Response: %s %s - Status: %d",
            request.method,
            request.url.path,
            response.status_code,
        )
        return response
    except Exception as e:
        logger.exception("Onverwachte fout tijdens verwerking van request.")
        return JSONResponse(
            status_code=500,
            content={"detail": t("internal_server_error", "en"), "error": str(e)},
        )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning("Validatiefout bij %s: %s", request.url.path, exc.errors())
    return JSONResponse(status_code=422, content={"detail": exc.errors()})

@app.exception_handler(Exception)
async def unexpected_exception_handler(request: Request, exc: Exception):
    tb = traceback.format_exc()
    logger.error("Onverwachte fout bij %s: %s\n%s", request.url.path, str(exc), tb)
    return JSONResponse(
        status_code=500,
        content={"detail": t("internal_server_error", "en"), "error": str(exc)},
    )

# CORS - Allow all origins for Expo Snack compatibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# ------------------------- Static Files ----------------------------
# Mount static files to serve profile photos
static_dir = os.path.join(os.path.dirname(__file__), "attached_assets", "stock_images")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    logger.info("Static files mounted at /static from %s", static_dir)
else:
    logger.warning("Static images directory not found: %s", static_dir)

# ------------------------- DB Pool & Helpers -----------------------
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
        try:
            self.cur = self.conn.cursor()
            self.cur.execute("SET search_path TO public;")
            return self.conn, self.cur
        except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
            logger.warning(f"Stale connection detected, getting fresh connection: {e}")
            try:
                pool.putconn(self.conn, close=True)
            except Exception:
                pass
            self.conn = pool.getconn()
            self.cur = self.conn.cursor()
            self.cur.execute("SET search_path TO public;")
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

# ------------------------- Models ----------------------------------
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    name: str = Field(..., min_length=2, max_length=50)
    age: int = Field(..., gt=17, lt=100)
    bio: Optional[str] = Field(None, max_length=500)

class UserInDB(UserBase):
    password_hash: str

class UserCreate(UserBase):
    password: str
    email: Optional[str] = None
    
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
        if not re.search(r"[\\#\?!@$%^&*\-]", v):
            raise ValueError("Wachtwoord moet minimaal één speciaal karakter bevatten.")
        return v

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
    photos: List[str] = []
    photos_meta: List[UserPhoto] = []

class UserPreferences(BaseModel):
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

class UserPublic(BaseModel):
    id: int
    username: str
    name: str
    age: int
    bio: Optional[str] = None
    language: Optional[str] = "nl"

class UserUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    bio: Optional[str] = None
    language: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    city: Optional[str] = None

class UserSettingsModel(BaseModel):
    match_goal: Optional[str] = None
    preferred_gender: Optional[str] = None
    max_distance_km: Optional[int] = None
    notifications_enabled: Optional[bool] = None
    # Optioneel taalveld zou hier kunnen, maar laten we nu buiten scope.

DEFAULT_SETTINGS = {
    "match_goal": "friendship",
    "preferred_gender": "any",
    "max_distance_km": 25,
    "notifications_enabled": True,
}

# ------------------------- Password & Token ------------------------
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")  # (niet direct gebruikt)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

def get_password_hash(plain_password: str) -> str:
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def create_access_token(data: Dict[str, Any], expires_delta: timedelta) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# ------------------------- Timestamp helper ------------------------
def _to_isoz(ts) -> str:
    """Converteer een datetime of string naar ISO-8601 met 'Z' (UTC). Failsafe."""
    if isinstance(ts, datetime):
        return ts.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    if isinstance(ts, str):
        s = ts.strip()
        try:
            if "T" not in s and " " in s:
                s = s.replace(" ", "T")
            if s.endswith("+00"):
                s = s + ":00"
            if s.endswith("Z"):
                dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
            else:
                dt = datetime.fromisoformat(s)
            return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        except Exception:
            return s
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

# ------------------------- Strava helpers (mock) -------------------
def get_latest_strava_coords(strava_token: Optional[str]) -> Optional[Tuple[float, float]]:
    """
    MOCK: haalt coördinaten uit strava_token als die begint met 'mock:LAT,LNG'.
    Voorbeeld: 'mock:51.2194,4.4025' -> (51.2194, 4.4025)
    """
    if not strava_token:
        return None
    if strava_token.startswith("mock:"):
        try:
            coords = strava_token.split("mock:", 1)[1]
            lat_str, lng_str = coords.split(",", 1)
            return float(lat_str.strip()), float(lng_str.strip())
        except Exception:
            return None
    return None

# ------------------------- Auth Dependency -------------------------
async def get_bearer_token(
    request: Request,
    authorization: Optional[str] = Header(None),
) -> Optional[str]:
    """Lees eerst Authorization: Bearer ...; zo niet, val terug op cookie."""
    if authorization and authorization.lower().startswith("bearer "):
        return authorization[7:]
    return request.cookies.get(COOKIE_NAME)

async def get_current_user(
    token: Optional[str] = Depends(get_bearer_token),
    db=Depends(get_db),
):
    conn, c = db
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=t("token_missing", "en"),
        )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: Optional[str] = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail=t("token_invalid", "en"))
    except JWTError:
        raise HTTPException(status_code=401, detail=t("token_invalid", "en"))

    c.execute(
        """
        SELECT id, username, name, age, bio, preferred_min_age, preferred_max_age, strava_token, COALESCE(language,'nl'), latitude, longitude, city, strava_athlete_id
        FROM users
        WHERE username = %s AND deleted_at IS NULL
        """,
        (username,),
    )
    row = c.fetchone()
    if not row:
        raise HTTPException(status_code=401, detail=t("user_not_found", "en"))
    return {
        "id": row[0],
        "username": row[1],
        "name": row[2],
        "age": row[3],
        "bio": row[4],
        "preferred_min_age": row[5],
        "preferred_max_age": row[6],
        "strava_token": row[7],
        "language": row[8],
        "latitude": row[9],
        "longitude": row[10],
        "city": row[11],
        "strava_athlete_id": row[12],
    }

# ------------------------- Startup / Shutdown ----------------------
@app.on_event("startup")
def on_startup():
    init_pool()
    with DB() as (conn, c):
        # Tabellen
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE,
                password_hash TEXT,
                name TEXT,
                age INTEGER,
                bio TEXT,
                strava_token TEXT,
                preferred_min_age INTEGER,
                preferred_max_age INTEGER,
                push_token TEXT,
                is_verified BOOLEAN DEFAULT FALSE,
                language TEXT DEFAULT 'nl',
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
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS email_verification_tokens (
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                token TEXT UNIQUE,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                is_used BOOLEAN DEFAULT FALSE
            )
            """
        )
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
                match_goal TEXT,
                preferred_gender TEXT,
                max_distance_km INTEGER,
                notifications_enabled BOOLEAN
            )
            """
        )
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS user_availabilities (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                day_of_week SMALLINT NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
                start_time TIME NOT NULL,
                end_time TIME NOT NULL,
                timezone TEXT DEFAULT 'Europe/Brussels'
            )
            """
        )
        # Indexen
        c.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users (username)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_swipes_swiper_swipee ON swipes (swiper_id, swipee_id)")
        c.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_swipes_swiper_liked
            ON swipes (swiper_id, liked)
            WHERE deleted_at IS NULL
            """
        )
        c.execute("CREATE INDEX IF NOT EXISTS idx_blocks_pair ON user_blocks (blocker_id, blocked_id)")
        c.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_chats_match
            ON chats (match_id)
            WHERE deleted_at IS NULL
            """
        )
        c.execute("CREATE INDEX IF NOT EXISTS idx_avail_user ON user_availabilities(user_id)")

        # Migraties
        # chats.timestamp -> timestamptz (idempotent)
        c.execute(
            """
            SELECT data_type
            FROM information_schema.columns
            WHERE table_name = 'chats' AND column_name = 'timestamp'
            """
        )
        row = c.fetchone()
        if row and row[0] not in ('timestamp with time zone', 'timestamptz'):
            logger.warning("Migrating chats.timestamp from %s to TIMESTAMPTZ ...", row[0])
            c.execute("ALTER TABLE chats ALTER COLUMN timestamp TYPE TIMESTAMPTZ USING (timestamp::timestamptz)")
            logger.info("Migratie voltooid: chats.timestamp is nu TIMESTAMPTZ.")

@app.on_event("shutdown")
def on_shutdown():
    global pool
    if pool:
        pool.closeall()
        logger.info("PostgreSQL connection pool afgesloten.")
    pool = None

# ------------------------- Email utils -----------------------------
from email_utils import generate_verification_token, send_verification_email

# ------------------------- Endpoints -------------------------------
@app.get("/me")
async def me(current_user: dict = Depends(get_current_user)):
    return {
        "id": current_user["id"],
        "username": current_user["username"],
        "name": current_user["name"],
        "age": current_user["age"],
        "bio": current_user["bio"],
        "language": current_user.get("language", "nl"),
        "latitude": current_user.get("latitude"),
        "longitude": current_user.get("longitude"),
        "city": current_user.get("city"),
        "strava_athlete_id": current_user.get("strava_athlete_id"),
    }

@app.patch("/users/{user_id}", response_model=UserPublic)
async def patch_user(
    user_id: int,
    payload: UserUpdate,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    lang = get_lang(current_user)
    if user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail=t("forbidden", lang))
    conn, c = db
    updates: List[str] = []
    values: List[Any] = []
    for k, v in payload.dict(exclude_unset=True).items():
        updates.append(f"{k}=%s")
        values.append(v)
    if not updates:
        raise HTTPException(status_code=400, detail=t("no_fields_to_update", lang))
    values.append(user_id)
    c.execute(
        f"UPDATE users SET {', '.join(updates)} WHERE id=%s AND deleted_at IS NULL",
        tuple(values)
    )
    c.execute("SELECT id, username, name, age, bio, COALESCE(language,'nl') FROM users WHERE id=%s", (user_id,))
    row = c.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=t("user_not_found", lang))
    return {"id": row[0], "username": row[1], "name": row[2], "age": row[3], "bio": row[4], "language": row[5]}

@app.get("/users/{user_id}/settings")
async def get_user_settings(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    lang = get_lang(current_user)
    if user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail=t("forbidden", lang))
    conn, c = db
    c.execute(
        """
        SELECT match_goal, preferred_gender, max_distance_km, notifications_enabled
        FROM user_settings WHERE user_id=%s
        """,
        (user_id,),
    )
    row = c.fetchone()
    if not row:
        return DEFAULT_SETTINGS
    return {
        "match_goal": row[0],
        "preferred_gender": row[1],
        "max_distance_km": row[2],
        "notifications_enabled": row[3],
    }

@app.post("/users/{user_id}/settings")
async def save_user_settings(
    user_id: int,
    payload: UserSettingsModel,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    lang = get_lang(current_user)
    if user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail=t("forbidden", lang))
    conn, c = db
    data = {**DEFAULT_SETTINGS, **payload.dict(exclude_unset=True)}
    c.execute(
        """
        INSERT INTO user_settings (user_id, match_goal, preferred_gender, max_distance_km, notifications_enabled)
        VALUES (%s,%s,%s,%s,%s)
        ON CONFLICT (user_id) DO UPDATE SET
            match_goal=EXCLUDED.match_goal,
            preferred_gender=EXCLUDED.preferred_gender,
            max_distance_km=EXCLUDED.max_distance_km,
            notifications_enabled=EXCLUDED.notifications_enabled
        """,
        (user_id, data["match_goal"], data["preferred_gender"], data["max_distance_km"], data["notifications_enabled"]),
    )
    return {"status": "success", "message": t("ok", lang)}

class AvailabilityItem(BaseModel):
    day_of_week: int  # 0..6 (0=ma, 6=zo)
    start_time: str   # "HH:MM"
    end_time: str     # "HH:MM"
    timezone: Optional[str] = "Europe/Brussels"

def _validate_time(hhmm: str) -> Tuple[int, int]:
    parts = hhmm.split(":")
    if len(parts) != 2:
        raise ValueError("Ongeldig tijdformaat, gebruik HH:MM")
    h, m = int(parts[0]), int(parts[1])
    if not (0 <= h < 24 and 0 <= m < 60):
        raise ValueError("Uur/minuut buiten bereik")
    return h, m

@app.get("/users/{user_id}/availability")
async def get_availability(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    lang = get_lang(current_user)
    if user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail=t("forbidden", lang))
    conn, c = db
    c.execute("""
        SELECT id, day_of_week, to_char(start_time,'HH24:MI'), to_char(end_time,'HH24:MI'), timezone
        FROM user_availabilities WHERE user_id=%s ORDER BY day_of_week, start_time
    """, (user_id,))
    rows = c.fetchall()
    items = [{
        "id": r[0],
        "day_of_week": r[1],
        "start_time": r[2],
        "end_time": r[3],
        "timezone": r[4],
    } for r in rows]
    return {"availability": items}

@app.post("/users/{user_id}/availability")
async def save_availability(
    user_id: int,
    payload: List[AvailabilityItem],
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    lang = get_lang(current_user)
    if user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail=t("forbidden", lang))
    conn, c = db
    # Validatie
    for it in payload:
        if it.day_of_week < 0 or it.day_of_week > 6:
            raise HTTPException(status_code=422, detail=t("day_of_week_invalid", lang))
        try:
            sh, sm = _validate_time(it.start_time)
            eh, em = _validate_time(it.end_time)
        except Exception as e:
            msg = str(e)
            if "HH:MM" in msg:
                raise HTTPException(status_code=422, detail=t("invalid_time_format", lang))
            if "bereik" in msg or "range" in msg:
                raise HTTPException(status_code=422, detail=t("time_out_of_range", lang))
            raise HTTPException(status_code=422, detail=t("internal_server_error", lang))
        if (eh, em) <= (sh, sm):
            raise HTTPException(status_code=422, detail=t("end_time_after_start", lang))
    # Vervang alles in één transactie
    try:
        c.execute("DELETE FROM user_availabilities WHERE user_id=%s", (user_id,))
        for it in payload:
            c.execute(
                """
                INSERT INTO user_availabilities (user_id, day_of_week, start_time, end_time, timezone)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (user_id, it.day_of_week, it.start_time, it.end_time, it.timezone or "Europe/Brussels"),
            )
        return {"status": "success", "message": t("ok", lang)}
    except psycopg2.Error:
        logger.exception("Databasefout bij het opslaan van beschikbaarheden.")
        raise HTTPException(status_code=500, detail=t("db_error", lang))

@app.post("/photos/{photo_id}/set_profile")
async def set_profile_photo(
    photo_id: int,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    conn, c = db
    user_id = current_user["id"]
    lang = get_lang(current_user)

    # Check eigendom
    c.execute("SELECT id FROM user_photos WHERE id=%s AND user_id=%s", (photo_id, user_id))
    row = c.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=t("photo_not_found", lang))

    # Reset en zet nieuwe
    c.execute("UPDATE user_photos SET is_profile_pic=0 WHERE user_id=%s", (user_id,))
    c.execute("UPDATE user_photos SET is_profile_pic=1 WHERE id=%s", (photo_id,))
    return {"status": "success", "message": t("ok", lang)}

@app.post("/token", response_model=Token)
async def login_for_access_token(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db=Depends(get_db),
):
    conn, c = db
    try:
        c.execute(
            "SELECT password_hash, COALESCE(language,'nl'), is_verified FROM users WHERE username = %s AND deleted_at IS NULL",
            (form_data.username,),
        )
        row = c.fetchone()
        lang_guess = "nl" if not row else (row[1] if len(row) > 1 else "nl")
        if not row or not verify_password(form_data.password, row[0]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=t("incorrect_credentials", get_lang({"language": lang_guess})),
            )
        is_verified = row[2] if len(row) > 2 else False
        if not is_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=t("email_not_verified", get_lang({"language": lang_guess})),
            )
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(data={"sub": form_data.username}, expires_delta=access_token_expires)
        # Cookie zetten (fallback)
        response.set_cookie(
            key=COOKIE_NAME,
            value=access_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
        return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException:
        raise
    except Exception:
        logger.exception("Fout bij het genereren van een token.")
        raise HTTPException(status_code=500, detail=t("internal_server_error", "en"))

@app.post("/register")
async def create_user(user: UserCreate, db=Depends(get_db)):
    conn, c = db
    password_hash = get_password_hash(user.password)
    try:
        # Gebruiker aanmaken
        c.execute(
            """
            INSERT INTO users (username, password_hash, name, age, bio, email, strava_token,
                               preferred_min_age, preferred_max_age, push_token, deleted_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NULL)
            RETURNING id, COALESCE(language,'nl')
            """,
            (
                user.username, password_hash, user.name, user.age, user.bio, user.email,
                None, None, None, None
            )
        )
        user_id, lang = c.fetchone()

        # Token genereren en opslaan
        token = generate_verification_token()
        c.execute(
            "INSERT INTO email_verification_tokens (user_id, token) VALUES (%s, %s)",
            (user_id, token)
        )

        # Mail versturen naar het email adres van de gebruiker
        if user.email:
            send_verification_email(user.email, user.name, token, lang=lang)

        logger.info("Nieuwe gebruiker aangemaakt: %s", user.username)
        return {
            "status": "success",
            "user_id": user_id,
            "username": user.username,
            "profile_pic_url": None,
            "message": t("verification_email_sent", get_lang({"language": lang})),
        }
    except Exception as e:
        logger.exception("Fout bij registratie.")
        error_msg = str(e)
        lang = getattr(user, 'language', None) or "en"
        if "users_email_unique" in error_msg or "users_email_key" in error_msg:
            raise HTTPException(status_code=400, detail=t("email_already_exists", lang))
        if "users_username_key" in error_msg:
            raise HTTPException(status_code=400, detail=t("username_already_exists", lang))
        raise HTTPException(status_code=500, detail=t("internal_server_error", "en"))

@app.post("/resend-verification")
async def resend_verification(username: str, db=Depends(get_db)):
    conn, c = db
    c.execute("SELECT id, name, email, is_verified, COALESCE(language,'nl') FROM users WHERE username = %s AND deleted_at IS NULL", (username,))
    row = c.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=t("user_not_found", "en"))
    user_id, name, email, is_verified, lang = row
    lang = get_lang({"language": lang})
    if is_verified:
        raise HTTPException(status_code=400, detail=t("user_already_verified", lang))
    if not email:
        raise HTTPException(status_code=400, detail=t("no_email_address", lang))
    token = generate_verification_token()
    c.execute("INSERT INTO email_verification_tokens (user_id, token) VALUES (%s, %s)", (user_id, token))
    send_verification_email(email, name, token, lang=lang)
    return {"status": "success", "message": t("verification_email_sent", lang)}

@app.get("/verify-email")
async def verify_email(token: str, db=Depends(get_db)):
    conn, c = db
    c.execute(
        """
        SELECT evt.user_id, COALESCE(u.language,'nl')
        FROM email_verification_tokens evt
        JOIN users u ON u.id = evt.user_id
        WHERE evt.token = %s AND evt.is_used = FALSE
        """,
        (token,)
    )
    row = c.fetchone()
    if not row:
        raise HTTPException(status_code=400, detail=t("invalid_or_expired_token", "en"))
    user_id, lang = row
    lang = get_lang({"language": lang})
    c.execute("UPDATE email_verification_tokens SET is_used = TRUE WHERE token = %s", (token,))
    c.execute("UPDATE users SET is_verified = TRUE WHERE id = %s", (user_id,))
    logger.info("E-mailadres bevestigd voor gebruiker %s", user_id)
    return {"status": "success", "message": t("email_verified", lang)}


# -------- Password Reset --------
class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str
    
    @validator("new_password")
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Wachtwoord moet minimaal 8 karakters lang zijn.")
        if not re.search(r"[a-z]", v):
            raise ValueError("Wachtwoord moet minimaal één kleine letter bevatten.")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Wachtwoord moet minimaal één hoofdletter bevatten.")
        if not re.search(r"[0-9]", v):
            raise ValueError("Wachtwoord moet minimaal één cijfer bevatten.")
        if not re.search(r"[\\#\?!@$%^&*\-]", v):
            raise ValueError("Wachtwoord moet minimaal één speciaal karakter bevatten.")
        return v


@app.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest, db=Depends(get_db)):
    """
    Vraag een wachtwoord reset aan. Stuurt een email met reset link.
    """
    from email_utils import send_password_reset_email
    conn, c = db
    
    # Zoek gebruiker op email
    c.execute(
        "SELECT id, name, email, COALESCE(language,'nl') FROM users WHERE email = %s AND deleted_at IS NULL",
        (request.email,)
    )
    row = c.fetchone()
    
    # Altijd success retourneren (security: vertel niet of email bestaat)
    if not row:
        logger.info("Password reset aangevraagd voor onbekend email: %s", request.email)
        return {"status": "success", "message": t("password_reset_sent", "nl")}
    
    user_id, name, email, lang = row
    lang = get_lang({"language": lang})
    
    # Genereer reset token
    token = generate_verification_token()
    expires_at = datetime.utcnow() + timedelta(hours=1)
    
    # Sla token op
    c.execute(
        "INSERT INTO password_reset_tokens (user_id, token, expires_at) VALUES (%s, %s, %s)",
        (user_id, token, expires_at)
    )
    
    # Verstuur email
    try:
        send_password_reset_email(email, name, token, lang=lang)
        logger.info("Password reset email verzonden naar %s", email)
    except Exception:
        logger.exception("Fout bij verzenden password reset email")
    
    return {"status": "success", "message": t("password_reset_sent", lang)}


@app.post("/reset-password")
async def reset_password(request: ResetPasswordRequest, db=Depends(get_db)):
    """
    Reset het wachtwoord met een geldige token.
    """
    conn, c = db
    
    # Zoek geldige token
    c.execute(
        """
        SELECT prt.user_id, prt.expires_at, COALESCE(u.language,'nl')
        FROM password_reset_tokens prt
        JOIN users u ON u.id = prt.user_id
        WHERE prt.token = %s AND prt.used = FALSE
        """,
        (request.token,)
    )
    row = c.fetchone()
    
    if not row:
        raise HTTPException(status_code=400, detail=t("invalid_or_expired_token", "en"))
    
    user_id, expires_at, lang = row
    lang = get_lang({"language": lang})
    
    # Controleer of token verlopen is
    if datetime.utcnow() > expires_at.replace(tzinfo=None):
        raise HTTPException(status_code=400, detail=t("token_expired", lang))
    
    # Update wachtwoord
    password_hash = get_password_hash(request.new_password)
    c.execute("UPDATE users SET password_hash = %s WHERE id = %s", (password_hash, user_id))
    
    # Markeer token als gebruikt
    c.execute("UPDATE password_reset_tokens SET used = TRUE WHERE token = %s", (request.token,))
    
    logger.info("Wachtwoord gereset voor gebruiker %s", user_id)
    return {"status": "success", "message": t("password_reset_success", lang)}


@app.get("/users/{user_id}", response_model=UserProfile)
async def read_user(user_id: int, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    conn, c = db
    lang = get_lang(current_user)
    c.execute(
        """
        SELECT id, name, age, bio
        FROM users
        WHERE id = %s AND deleted_at IS NULL
        """,
        (user_id,),
    )
    user = c.fetchone()
    if not user:
        raise HTTPException(status_code=404, detail=t("user_not_found", lang))
    # Photos (urls + metadata)
    c.execute(
        "SELECT id, photo_url, is_profile_pic FROM user_photos WHERE user_id = %s ORDER BY id ASC",
        (user_id,),
    )
    rows = c.fetchall()
    photos = [r[1] for r in rows]
    photos_meta = [{"id": r[0], "photo_url": r[1], "is_profile_pic": bool(r[2])} for r in rows]
    profile_photo_url = next((r[1] for r in rows if r[2] == 1), None)
    has_profile_photo = profile_photo_url is not None
    logger.info("Gebruiker %s bekijkt profiel van gebruiker %s.", current_user["id"], user_id)
    return {
        "id": user[0],
        "name": user[1],
        "age": user[2],
        "bio": user[3],
        "photos": photos,
        "photos_meta": photos_meta,
        "has_profile_photo": has_profile_photo,
        "profile_photo_url": profile_photo_url,
    }

@app.post("/users/{user_id}/preferences")
async def update_user_preferences(
    user_id: int,
    preferences: UserPreferences,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    lang = get_lang(current_user)
    if user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail=t("forbidden", lang))
    conn, c = db
    try:
        c.execute(
            """
            UPDATE users
            SET preferred_min_age = %s, preferred_max_age = %s
            WHERE id=%s AND deleted_at IS NULL
            """,
            (preferences.preferred_min_age, preferences.preferred_max_age, user_id),
        )
        logger.info("Voorkeuren van gebruiker %s succesvol bijgewerkt.", user_id)
        return {"status": "success", "message": t("ok", lang)}
    except psycopg2.Error:
        logger.exception("Databasefout bij het bijwerken van voorkeuren.")
        raise HTTPException(status_code=500, detail=t("db_error", lang))

@app.get("/suggestions")
async def get_suggestions(current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    conn, c = db
    user_id = current_user["id"]
    min_age = current_user.get("preferred_min_age")
    max_age = current_user.get("preferred_max_age")
    
    c.execute(
        "SELECT preferred_gender, max_distance_km FROM user_settings WHERE user_id = %s",
        (user_id,)
    )
    settings_row = c.fetchone()
    if settings_row:
        preferred_gender, max_distance_km = settings_row
    else:
        preferred_gender, max_distance_km = "any", 25
    
    c.execute(
        "SELECT latitude, longitude FROM users WHERE id = %s",
        (user_id,)
    )
    user_location = c.fetchone()
    user_lat, user_lon = user_location if user_location else (None, None)
    
    query = """
        SELECT
            u.id, u.name, u.age, u.bio, u.gender, u.latitude, u.longitude, u.city,
            prof.photo_url AS profile_photo_url,
            photos.photos AS photos
        FROM users u
        LEFT JOIN LATERAL (
            SELECT up.photo_url
            FROM user_photos up
            WHERE up.user_id = u.id AND up.is_profile_pic = 1
            ORDER BY up.id DESC
            LIMIT 1
        ) prof ON TRUE
        LEFT JOIN LATERAL (
            SELECT array_agg(up2.photo_url ORDER BY (up2.is_profile_pic=1) DESC, up2.id ASC) AS photos
            FROM user_photos up2
            WHERE up2.user_id = u.id
        ) photos ON TRUE
        WHERE u.id <> %s
          AND u.deleted_at IS NULL
          AND NOT EXISTS (SELECT 1 FROM user_blocks b WHERE b.blocker_id = %s AND b.blocked_id = u.id)
          AND NOT EXISTS (SELECT 1 FROM user_blocks b WHERE b.blocker_id = u.id AND b.blocked_id = %s)
          AND NOT EXISTS (SELECT 1 FROM swipes s WHERE s.swiper_id = %s AND s.swipee_id = u.id)
    """
    params: List[Any] = [user_id, user_id, user_id, user_id]
    
    if preferred_gender and preferred_gender != "any":
        gender_map = {"male": "man", "female": "woman", "non_binary": "non_binary"}
        mapped_gender = gender_map.get(preferred_gender, preferred_gender)
        query += " AND u.gender = %s"
        params.append(mapped_gender)
    
    if min_age:
        query += " AND u.age >= %s"
        params.append(min_age)
    if max_age:
        query += " AND u.age <= %s"
        params.append(max_age)
    
    query += " ORDER BY CASE WHEN u.name = 'Greta Hoffman' THEN 0 WHEN u.name IN ('Emma de Vries', 'Lucas Janssen', 'Sophie Bakker', 'Mike van Dijk') THEN 1 ELSE 2 END, u.id LIMIT 200"
    c.execute(query, tuple(params))
    rows = c.fetchall()
    
    suggestions = []
    for r in rows:
        _photos = r[9] if isinstance(r[9], list) else []
        
        # Zorg dat elk profiel minimaal 3 foto's heeft voor de swipeable gallery
        user_name = r[1]
        if user_name == "Greta Hoffman":
            _photos = [
                "/static/young_woman_fitness__d16ff150.jpg",
                "/static/young_woman_fitness__d999d5d6.jpg",
                "/static/man_doing_crossfit_w_01ad1dbd.jpg"
            ]
        elif user_name == "Emma de Vries":
            _photos = [
                "/static/athletic_woman_cycli_aa0c899a.jpg",
                "/static/man_mountain_biking__23a83e22.jpg",
                "/static/man_mountain_biking__afa1f0d0.jpg"
            ]
        elif user_name == "Lucas Janssen":
            _photos = [
                "/static/athletic_man_running_2d831f2d.jpg",
                "/static/man_marathon_runner__15184a79.jpg",
                "/static/man_marathon_runner__c97ed512.jpg"
            ]
        elif user_name == "Sophie Bakker":
            _photos = [
                "/static/athletic_woman_swimm_d163d388.jpg",
                "/static/woman_swimming_triat_25d4acc8.jpg",
                "/static/woman_swimming_triat_cac09f49.jpg"
            ]
        elif user_name == "Mike van Dijk":
            _photos = [
                "/static/athletic_man_triathl_e5456b59.jpg",
                "/static/man_marathon_runner__15184a79.jpg",
                "/static/athletic_woman_swimm_d163d388.jpg"
            ]
        else:
            # Als er database foto's zijn, gebruik die als eerste foto
            db_photo = _photos[0] if _photos else None
            
            # Default foto's voor andere profielen
            gender = r[4]
            if gender == "man":
                _photos = [
                    "/static/man_playing_tennis_a_54f6d78c.jpg",
                    "/static/man_soccer_player_at_0512128e.jpg",
                    "/static/man_marathon_runner__c97ed512.jpg"
                ]
            else:
                _photos = [
                    "/static/young_woman_running__0e2f1233.jpg",
                    "/static/woman_rock_climbing__0a088eb5.jpg",
                    "/static/young_woman_yoga_ins_1713cba9.jpg"
                ]
            
            # Als er een database foto was, voeg die toe als eerste
            if db_photo and db_photo not in _photos:
                _photos = [db_photo] + _photos[:2]
        
        distance_km = None
        if user_lat and user_lon and r[5] and r[6]:
            distance_km = haversine((user_lat, user_lon), (r[5], r[6]), unit=Unit.KILOMETERS)
            if max_distance_km and distance_km > max_distance_km:
                continue
        
        # Mock sportstatistieken met realistische YTD data voor testusers
        mock_activities = []
        # Default YTD stats voor users zonder specifieke data (recreatief sporter - wandeltempo)
        ytd_stats = {
            "total_workouts": 52,  # ~1x per week
            "total_distance": 260000,  # ~260 km (5 km per workout)
            "total_time": 234000  # ~65 uur (~4 km/u wandel/looptempo)
        }
        
        if r[1] == "Greta Hoffman":  # crossfit - intensief maar korte afstanden (vooral kracht)
            mock_activities = [
                {"name": "CrossFit WOD", "distance": 5000, "moving_time": 3600, "start_date": "2025-11-22T06:00:00Z"},
                {"name": "AMRAP workout", "distance": 3000, "moving_time": 2700, "start_date": "2025-11-20T17:00:00Z"},
                {"name": "Strength training", "distance": 0, "moving_time": 4500, "start_date": "2025-11-18T18:00:00Z"}
            ]
            ytd_stats = {
                "total_workouts": 156,  # 3x per week
                "total_distance": 156000,  # 156 km (~1 km per workout - vooral kracht/statisch)
                "total_time": 561600  # 156 uur (1 uur per workout - veel rust tussen sets)
            }
        elif r[1] == "Emma de Vries":  # wielrenster - lange afstanden, redelijk tempo
            mock_activities = [
                {"name": "Ochtend fietstocht", "distance": 42500, "moving_time": 5400, "start_date": "2025-11-20T08:00:00Z"},
                {"name": "Middag rit", "distance": 35000, "moving_time": 4200, "start_date": "2025-11-18T14:00:00Z"},
                {"name": "Weekend tour", "distance": 68000, "moving_time": 7800, "start_date": "2025-11-16T09:00:00Z"}
            ]
            ytd_stats = {
                "total_workouts": 180,  # 3-4x per week
                "total_distance": 7200000,  # 7200 km (40 km per rit gemiddeld)
                "total_time": 864000  # 240 uur (30 km/u gemiddeld - realistisch voor wielrenner)
            }
        elif r[1] == "Lucas Janssen":  # marathon hardloper
            mock_activities = [
                {"name": "Hardloop training", "distance": 10000, "moving_time": 3000, "start_date": "2025-11-21T07:00:00Z"},
                {"name": "Interval run", "distance": 8000, "moving_time": 2400, "start_date": "2025-11-19T06:30:00Z"},
                {"name": "Long run", "distance": 15000, "moving_time": 4500, "start_date": "2025-11-17T08:00:00Z"}
            ]
            ytd_stats = {
                "total_workouts": 260,  # 5x per week
                "total_distance": 2600000,  # 2600 km (10 km per run gemiddeld)
                "total_time": 780000  # 217 uur (5 min/km pace - goed voor marathon runner)
            }
        elif r[1] == "Sophie Bakker":  # zwemcoach
            mock_activities = [
                {"name": "Zwem training", "distance": 2000, "moving_time": 2400, "start_date": "2025-11-22T18:00:00Z"},
                {"name": "Baantjes trekken", "distance": 1500, "moving_time": 1800, "start_date": "2025-11-20T19:00:00Z"},
                {"name": "Open water", "distance": 3000, "moving_time": 3600, "start_date": "2025-11-18T10:00:00Z"}
            ]
            ytd_stats = {
                "total_workouts": 208,  # 4x per week
                "total_distance": 520000,  # 520 km (2.5 km per sessie)
                "total_time": 520000  # 144 uur (goed zwemtempo)
            }
        elif r[1] == "Mike van Dijk":  # triatleet - mix van sporten
            mock_activities = [
                {"name": "Triathlon training", "distance": 25000, "moving_time": 5400, "start_date": "2025-11-21T06:00:00Z"},
                {"name": "Bike + Run brick", "distance": 30000, "moving_time": 6000, "start_date": "2025-11-19T07:00:00Z"},
                {"name": "Zwem sessie", "distance": 2500, "moving_time": 2700, "start_date": "2025-11-17T18:00:00Z"}
            ]
            ytd_stats = {
                "total_workouts": 312,  # 6x per week (zwemmen, fietsen, hardlopen)
                "total_distance": 5200000,  # 5200 km (mix van disciplines)
                "total_time": 1123200  # 312 uur (3.6 uur per training - realistisch voor triatleet)
            }
        
        # Per-sport breakdown based on profile type
        sport_stats = {
            "cycling": {"total_workouts": 0, "total_distance": 0, "total_time": 0},
            "running": {"total_workouts": 0, "total_distance": 0, "total_time": 0},
            "swimming": {"total_workouts": 0, "total_distance": 0, "total_time": 0},
            "triathlon": {"total_workouts": 0, "total_distance": 0, "total_time": 0},
            "gym": {"total_workouts": 0, "total_distance": 0, "total_time": 0},
        }
        
        # Distribute stats based on user's primary sport
        if r[1] == "Emma de Vries":  # cyclist
            sport_stats["cycling"] = ytd_stats
            sport_stats["running"] = {"total_workouts": 24, "total_distance": 120000, "total_time": 28800}
        elif r[1] == "Lucas Janssen":  # runner
            sport_stats["running"] = ytd_stats
            sport_stats["gym"] = {"total_workouts": 104, "total_distance": 0, "total_time": 124800}
        elif r[1] == "Sophie Bakker":  # swimmer
            sport_stats["swimming"] = ytd_stats
            sport_stats["running"] = {"total_workouts": 52, "total_distance": 260000, "total_time": 78000}
        elif r[1] == "Mike van Dijk":  # triathlete - split across all sports
            sport_stats["swimming"] = {"total_workouts": 104, "total_distance": 260000, "total_time": 144000}
            sport_stats["cycling"] = {"total_workouts": 104, "total_distance": 3120000, "total_time": 374400}
            sport_stats["running"] = {"total_workouts": 104, "total_distance": 1560000, "total_time": 468000}
            sport_stats["triathlon"] = ytd_stats
        elif r[1] == "Greta Hoffman":  # crossfit/gym
            sport_stats["gym"] = ytd_stats
        else:
            # Default recreational - mix of activities
            sport_stats["running"] = {"total_workouts": 26, "total_distance": 130000, "total_time": 97500}
            sport_stats["cycling"] = {"total_workouts": 26, "total_distance": 390000, "total_time": 78000}
        
        suggestions.append({
            "id": r[0],
            "name": r[1],
            "age": r[2],
            "bio": r[3],
            "gender": r[4],
            "city": r[7],
            "distance_km": round(distance_km, 1) if distance_km else None,
            "profile_photo_url": r[8],
            "photos": _photos,
            "activities": mock_activities,
            "ytd_stats": ytd_stats,
            "sport_stats": sport_stats,
        })
    
    logger.info("Suggesties gegenereerd voor gebruiker %s. Aantal: %d", user_id, len(suggestions))
    return {"suggestions": suggestions}

@app.post("/swipe/{swipee_id}")
async def swipe(
    swipee_id: int,
    liked: bool,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    conn, c = db
    swiper_id = current_user["id"]
    lang = get_lang(current_user)
    if swiper_id == swipee_id:
        raise HTTPException(status_code=400, detail=t("cannot_swipe_self", lang))
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
        return {"status": "success", "message": t("match_success", lang) if match else t("swipe_registered", lang), "match": match}
    except psycopg2.Error:
        logger.exception("Databasefout bij het swipen.")
        raise HTTPException(status_code=500, detail=t("db_error", lang))

@app.get("/matches")
async def get_matches(current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    conn, c = db
    user_id = current_user["id"]
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
    user_id = current_user["id"]
    lang = get_lang(current_user)
    match_id = message.match_id
    plain_message = message.message
    timestamp = datetime.now(timezone.utc)
    # check wederzijdse like
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
        raise HTTPException(status_code=403, detail=t("no_match_cannot_message", lang))
    encrypted_message = cipher_suite.encrypt(plain_message.encode("utf-8")).decode("utf-8")
    c.execute(
        """
        INSERT INTO chats (match_id, sender_id, encrypted_message, timestamp)
        VALUES (%s, %s, %s, %s)
        """,
        (match_id, user_id, encrypted_message, timestamp),
    )
    logger.info("Chatbericht van gebruiker %s naar gebruiker %s opgeslagen.", user_id, match_id)
    return {"status": "success", "message": t("message_sent", lang)}

@app.get("/chat/{match_id}/messages")
async def get_chat_messages(match_id: int, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    conn, c = db
    user_id = current_user["id"]
    lang = get_lang(current_user)
    # toegang checken
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
        raise HTTPException(status_code=403, detail=t("chat_access_denied", lang))
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
            iso_ts = _to_isoz(ts)
            chat_history.append(ChatMessage(sender_id=sender_id, message=decrypted, timestamp=iso_ts))
        except Exception:
            logger.exception("Fout bij decoderen van bericht.")
            continue
    return {"chat_history": chat_history}

@app.post("/report_user")
async def report_user(report: ReportRequest, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    conn, c = db
    reporter_id = current_user["id"]
    lang = get_lang(current_user)
    if reporter_id == report.reported_id:
        raise HTTPException(status_code=400, detail=t("cannot_report_self", lang))
    try:
        c.execute(
            """
            INSERT INTO user_reports (reporter_id, reported_id, reason, timestamp)
            VALUES (%s, %s, %s, %s)
            """,
            (reporter_id, report.reported_id, report.reason, datetime.now(timezone.utc)),
        )
        logger.info("Gebruiker %s gerapporteerd door gebruiker %s.", report.reported_id, reporter_id)
        return {"status": "success", "message": t("user_reported", lang)}
    except psycopg2.Error:
        logger.exception("Databasefout bij rapporteren van gebruiker.")
        raise HTTPException(status_code=500, detail=t("db_error", lang))

@app.post("/block_user")
async def block_user(user_to_block_id: int, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    conn, c = db
    blocker_id = current_user["id"]
    lang = get_lang(current_user)
    if blocker_id == user_to_block_id:
        raise HTTPException(status_code=400, detail=t("cannot_block_self", lang))
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
            return {"status": "success", "message": t("user_already_blocked", lang)}
        logger.info("Gebruiker %s succesvol geblokkeerd door gebruiker %s.", user_to_block_id, blocker_id)
        return {"status": "success", "message": t("user_blocked", lang)}
    except psycopg2.Error:
        logger.exception("Databasefout bij het blokkeren van gebruiker.")
        raise HTTPException(status_code=500, detail=t("db_error", lang))

@app.delete("/delete/match/{match_id}")
async def delete_match(match_id: int, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    conn, c = db
    user_id = current_user["id"]
    lang = get_lang(current_user)
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
    return {"status": "success", "message": t("match_deleted", lang)}

@app.delete("/delete_photo/{photo_id}")
async def delete_photo(photo_id: int, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    conn, c = db
    user_id = current_user["id"]
    lang = get_lang(current_user)
    try:
        c.execute(
            "SELECT is_profile_pic FROM user_photos WHERE id = %s AND user_id = %s",
            (photo_id, user_id),
        )
        row = c.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=t("photo_not_found", lang))
        was_profile = row[0] == 1
        c.execute("DELETE FROM user_photos WHERE id = %s AND user_id = %s", (photo_id, user_id))
        if c.rowcount == 0:
            raise HTTPException(status_code=404, detail=t("photo_not_found", lang))
        if was_profile:
            c.execute("SELECT id FROM user_photos WHERE user_id = %s LIMIT 1", (user_id,))
            new_pic = c.fetchone()
            if new_pic:
                c.execute("UPDATE user_photos SET is_profile_pic = 1 WHERE id = %s", (new_pic[0],))
                logger.info("Nieuwe profielfoto %s toegewezen voor gebruiker %s.", new_pic[0], user_id)
            else:
                logger.warning("Gebruiker %s heeft geen profielfoto meer.", user_id)
        logger.info("Foto %s verwijderd voor gebruiker %s.", photo_id, user_id)
        return {"status": "success", "message": t("photo_deleted", lang)}
    except psycopg2.Error:
        logger.exception("Databasefout bij foto-verwijderen.")
        raise HTTPException(status_code=500, detail=t("db_error", lang))

@app.post("/upload_photo")
async def upload_photo(photo: PhotoUpload, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    conn, c = db
    user_id = current_user["id"]
    photo_url = str(photo.photo_url)
    lang = get_lang(current_user)
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
        return {"status": "success", "message": t("photo_uploaded", lang)}
    except psycopg2.Error:
        logger.exception("Databasefout bij foto-upload.")
        raise HTTPException(status_code=500, detail=t("db_error", lang))

# ------------------------- WebSocket -------------------------------
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
        with DB() as (conn, c):
            c.execute("SELECT id FROM users WHERE username = %s AND deleted_at IS NULL", (username,))
            row = c.fetchone()
            if not row or row[0] != user_id:
                await websocket.close(code=4403)  # forbidden
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

# ------------------------- Route Suggestion ------------------------
@app.get("/suggest_route/{match_id}")
async def get_route_suggestion(match_id: int, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    conn, c = db
    user_id = current_user["id"]
    lang = get_lang(current_user)
    # check wederzijdse like
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
        raise HTTPException(status_code=403, detail=t("chat_access_denied", lang))
    # Strava tokens ophalen
    user_strava_token = current_user.get("strava_token")
    c.execute("SELECT strava_token FROM users WHERE id = %s AND deleted_at IS NULL", (match_id,))
    row = c.fetchone()
    match_strava_token = row[0] if row else None

    user_loc = get_latest_strava_coords(user_strava_token)
    match_loc = get_latest_strava_coords(match_strava_token)
    if not user_loc or not match_loc:
        raise HTTPException(
            status_code=400,
            detail=t("route_suggestion_error", lang),
        )
    distance_km = haversine(user_loc, match_loc, unit=Unit.KILOMETERS)
    map_link = f"https://www.google.com/maps/dir/{user_loc[0]},{user_loc[1]}/{match_loc[0]},{match_loc[1]}"
    popular_route = {
        "name": "Voorstel gezamenlijke route",
        "description": "Suggestie gebaseerd op meest recente Strava-activiteiten (mock of echte integratie).",
        "distance_km": round(distance_km / 2, 2),
        "map_link": map_link,
    }
    logger.info("Routevoorstel gegenereerd voor match %s-%s.", user_id, match_id)
    return {"status": "success", "message": t("route_suggestion_success", lang), "route_suggestion": popular_route}

# ------------------------- STRAVA OAUTH ---------------------------
import urllib.parse
import httpx

@app.get("/strava/auth-url")
async def get_strava_auth_url(current_user: dict = Depends(get_current_user)):
    """Genereer de Strava OAuth authorization URL"""
    if not STRAVA_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Strava niet geconfigureerd")
    
    # Bouw redirect URI op basis van Replit domain
    if REPLIT_DEV_DOMAIN:
        redirect_uri = f"https://{REPLIT_DEV_DOMAIN}/strava/callback"
    else:
        redirect_uri = STRAVA_REDIRECT_URI
    
    # State bevat user_id voor later
    state = str(current_user["id"])
    
    params = {
        "client_id": STRAVA_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "read,activity:read_all",
        "state": state,
    }
    auth_url = f"https://www.strava.com/oauth/authorize?{urllib.parse.urlencode(params)}"
    return {"auth_url": auth_url}

@app.get("/strava/callback")
async def strava_callback(code: str, state: str, db=Depends(get_db)):
    """Strava OAuth callback - wissel code om voor access token"""
    if not STRAVA_CLIENT_ID or not STRAVA_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="Strava niet geconfigureerd")
    
    conn, c = db
    user_id = int(state)
    
    # Wissel authorization code om voor access token
    if REPLIT_DEV_DOMAIN:
        redirect_uri = f"https://{REPLIT_DEV_DOMAIN}/strava/callback"
    else:
        redirect_uri = STRAVA_REDIRECT_URI
    
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://www.strava.com/oauth/token",
            data={
                "client_id": STRAVA_CLIENT_ID,
                "client_secret": STRAVA_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
            }
        )
    
    if token_response.status_code != 200:
        logger.error("Strava token exchange failed: %s", token_response.text)
        raise HTTPException(status_code=400, detail="Strava authenticatie mislukt")
    
    token_data = token_response.json()
    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")
    expires_at = token_data.get("expires_at")
    athlete = token_data.get("athlete", {})
    
    # Sla tokens op in database (encrypted)
    encrypted_access = cipher_suite.encrypt(access_token.encode()).decode()
    encrypted_refresh = cipher_suite.encrypt(refresh_token.encode()).decode()
    
    c.execute(
        """
        UPDATE users 
        SET strava_token = %s, 
            strava_refresh_token = %s,
            strava_expires_at = %s,
            strava_athlete_id = %s
        WHERE id = %s
        """,
        (encrypted_access, encrypted_refresh, expires_at, athlete.get("id"), user_id)
    )
    conn.commit()
    
    logger.info("Strava gekoppeld voor user %s (athlete: %s)", user_id, athlete.get("id"))
    
    # Redirect terug naar app
    return HTMLResponse("""
        <html>
            <head><title>Strava Gekoppeld</title></head>
            <body style="font-family: sans-serif; text-align: center; margin-top: 50px;">
                <h1>✅ Strava Account Gekoppeld!</h1>
                <p>Je kunt dit venster sluiten en terugkeren naar de app.</p>
                <script>
                    setTimeout(function() {
                        window.close();
                    }, 2000);
                </script>
            </body>
        </html>
    """)

@app.post("/strava/disconnect")
async def disconnect_strava(current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    """Ontkoppel Strava account"""
    conn, c = db
    user_id = current_user["id"]
    
    c.execute(
        """
        UPDATE users 
        SET strava_token = NULL, 
            strava_refresh_token = NULL,
            strava_expires_at = NULL,
            strava_athlete_id = NULL
        WHERE id = %s
        """,
        (user_id,)
    )
    conn.commit()
    
    logger.info("Strava ontkoppeld voor user %s", user_id)
    return {"status": "success", "message": "Strava account ontkoppeld"}

@app.get("/strava/activities")
async def get_strava_activities(current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    """Haal recente Strava activiteiten op"""
    conn, c = db
    user_id = current_user["id"]
    
    # Haal Strava tokens op
    c.execute(
        "SELECT strava_token, strava_refresh_token, strava_expires_at FROM users WHERE id = %s",
        (user_id,)
    )
    row = c.fetchone()
    if not row or not row[0]:
        raise HTTPException(status_code=400, detail="Strava niet gekoppeld")
    
    encrypted_access, encrypted_refresh, expires_at = row
    
    # Check if refresh token exists
    if not encrypted_access or not encrypted_refresh:
        # Cleanup incomplete Strava linking
        c.execute(
            """
            UPDATE users 
            SET strava_token = NULL, 
                strava_refresh_token = NULL,
                strava_expires_at = NULL,
                strava_athlete_id = NULL
            WHERE id = %s
            """,
            (user_id,)
        )
        conn.commit()
        raise HTTPException(status_code=400, detail="Strava niet volledig gekoppeld - probeer opnieuw")
    
    # Decrypt access token
    try:
        access_token = cipher_suite.decrypt(encrypted_access.encode()).decode()
        refresh_token = cipher_suite.decrypt(encrypted_refresh.encode()).decode()
    except Exception as e:
        logger.error("Failed to decrypt Strava token: %s", e)
        # Cleanup corrupted tokens
        c.execute(
            """
            UPDATE users 
            SET strava_token = NULL, 
                strava_refresh_token = NULL,
                strava_expires_at = NULL,
                strava_athlete_id = NULL
            WHERE id = %s
            """,
            (user_id,)
        )
        conn.commit()
        raise HTTPException(status_code=500, detail="Token decryptie mislukt - koppel Strava opnieuw")
    
    # Check if token expired and refresh if needed
    import time
    current_time = int(time.time())
    if expires_at and current_time >= expires_at:
        logger.info("Strava token expired, refreshing for user %s", user_id)
        
        # Exchange refresh token for new access token
        async with httpx.AsyncClient() as client:
            refresh_response = await client.post(
                "https://www.strava.com/oauth/token",
                data={
                    "client_id": STRAVA_CLIENT_ID,
                    "client_secret": STRAVA_CLIENT_SECRET,
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                }
            )
        
        if refresh_response.status_code != 200:
            error_detail = refresh_response.text
            logger.error("Strava token refresh failed (status %d): %s", refresh_response.status_code, error_detail)
            
            # Alleen cleanup bij permanente failures (401/403 = revoked access)
            if refresh_response.status_code in [401, 403]:
                logger.warning("Strava access revoked for user %s, cleaning up", user_id)
                c.execute(
                    """
                    UPDATE users 
                    SET strava_token = NULL, 
                        strava_refresh_token = NULL,
                        strava_expires_at = NULL,
                        strava_athlete_id = NULL
                    WHERE id = %s
                    """,
                    (user_id,)
                )
                conn.commit()
                raise HTTPException(
                    status_code=401, 
                    detail="Strava toegang ingetrokken - koppel opnieuw"
                )
            else:
                # Transient error - behoud tokens, return error
                raise HTTPException(
                    status_code=503,
                    detail=f"Strava tijdelijk onbereikbaar (status {refresh_response.status_code}) - probeer later"
                )
        
        token_data = refresh_response.json()
        access_token = token_data.get("access_token")
        new_refresh_token = token_data.get("refresh_token")
        new_expires_at = token_data.get("expires_at")
        
        # Validate refresh response
        if not access_token or not new_refresh_token:
            logger.error("Strava refresh response missing tokens: %s", token_data)
            # Dit duidt op een Strava API probleem - behoud bestaande tokens
            raise HTTPException(
                status_code=503, 
                detail="Strava API error - probeer later opnieuw"
            )
        
        # Update database with new tokens
        encrypted_access = cipher_suite.encrypt(access_token.encode()).decode()
        encrypted_refresh_new = cipher_suite.encrypt(new_refresh_token.encode()).decode()
        
        c.execute(
            """
            UPDATE users 
            SET strava_token = %s, 
                strava_refresh_token = %s,
                strava_expires_at = %s
            WHERE id = %s
            """,
            (encrypted_access, encrypted_refresh_new, new_expires_at, user_id)
        )
        conn.commit()
        logger.info("Strava token refreshed successfully for user %s", user_id)
    
    # Haal activiteiten op van Strava API
    async with httpx.AsyncClient() as client:
        activities_response = await client.get(
            "https://www.strava.com/api/v3/athlete/activities",
            headers={"Authorization": f"Bearer {access_token}"},
            params={"per_page": 10}
        )
    
    if activities_response.status_code != 200:
        logger.error("Strava activities fetch failed: %s", activities_response.text)
        raise HTTPException(status_code=400, detail="Kan activiteiten niet ophalen")
    
    activities = activities_response.json()
    
    # Formatteer activiteiten
    formatted = []
    for activity in activities:
        formatted.append({
            "id": activity.get("id"),
            "name": activity.get("name"),
            "type": activity.get("type"),
            "distance": round(activity.get("distance", 0) / 1000, 2),  # meters naar km
            "moving_time": activity.get("moving_time"),
            "elapsed_time": activity.get("elapsed_time"),
            "start_date": activity.get("start_date"),
            "start_latlng": activity.get("start_latlng"),
        })
    
    return {"status": "success", "activities": formatted}

# ------------------------- Health & Home ---------------------------
@app.get("/healthz")
def healthz(db=Depends(get_db)):
    conn, c = db
    c.execute("SELECT 1")
    return {"status": "ok"}

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <html>
      <head><title>Sports Match API</title></head>
      <body style="font-family: sans-serif; text-align: center; margin-top: 50px;">
        <h1>Sports Match API is live! ✅</h1>
        <p>Bekijk de /docsSwagger UI</a> of /redocRedoc</a>.</p>
      </body>
    </html>
    """

# ------------------------- Main -----------------------------------
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8000")),
        reload=True,
    )


