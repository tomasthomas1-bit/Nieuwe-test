# main.py
from __future__ import annotations

import logging
import os
import re
import traceback
from datetime import datetime, timedelta, timezone
from typing import Any, List, Optional, Tuple, Dict

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
    Header,  # voor eigen token-extractor
)
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from haversine import Unit, haversine
from jose import JWTError, jwt
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
# Token-expiratie via ENV configureerbaar (default 30 min)
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = 7  # (niet gebruikt nu, handig voor later)
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

GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY")  # (optioneel)
FRONTEND_ORIGINS = os.environ.get("FRONTEND_ORIGINS", "")  # bv. "https://app...,https://staging..."
_allowed_origins = [o.strip() for o in FRONTEND_ORIGINS.split(",") if o.strip()]


# -------------------- App init --------------------
app = FastAPI(title="Sports Match API", version="2.2.0")


# Middleware: log of auth header/cookie aanwezig is (zonder secrets te loggen)
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
            content={"detail": "Interne serverfout", "error": str(e)},
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
        content={"detail": "Interne serverfout", "error": str(exc)},
    )


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


# -------------------- Models --------------------
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    name: str = Field(..., min_length=2, max_length=50)
    age: int = Field(..., gt=17, lt=100)
    bio: Optional[str] = Field(None, max_length=500)


class UserInDB(UserBase):
    password_hash: str


class UserCreate(UserBase):
    password: str

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
        if not re.search(r"[\\#\\?!@$%^&*\-]", v):
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


# -------------------- Password & Token --------------------
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")  # (niet meer gebruikt als dependency, ok)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def get_password_hash(plain_password: str) -> str:
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def create_access_token(data: Dict[str, Any], expires_delta: timedelta) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# -------------------- Timestamp normalisatie helper --------------------
def _to_isoz(ts) -> str:
    """
    Converteer een datetime of string naar ISO-8601 met 'Z' (UTC).
    Vangt diverse stringformaten op; faalt nooit hard (geeft desnoods input terug).
    """
    if isinstance(ts, datetime):
        return ts.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    if isinstance(ts, str):
        s = ts.strip()
        try:
            # ' ' -> 'T'
            if "T" not in s and " " in s:
                s = s.replace(" ", "T")
            # '+00' -> '+00:00'
            if s.endswith("+00"):
                s = s + ":00"
            # 'Z' suffix accepteren
            if s.endswith("Z"):
                dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
            else:
                dt = datetime.fromisoformat(s)
            return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        except Exception:
            return s
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


# -------------------- Strava helpers (mock) --------------------
def get_latest_strava_coords(strava_token: Optional[str]) -> Optional[Tuple[float, float]]:
    """
    MOCK: haalt coördinaten uit strava_token als die begint met 'mock:LAT,LNG'.
    Voorbeeld: 'mock:51.2194,4.4025' -> (51.2194, 4.4025)
    TODO: echte Strava API call implementeren.
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


# -------------------- Auth Dependency (header of cookie) --------------------
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
        SELECT id, username, name, age, bio, preferred_min_age, preferred_max_age, strava_token
        FROM users
        WHERE username = %s AND deleted_at IS NULL
        """,
        (username,),
    )
    row = c.fetchone()
    if not row:
        raise HTTPException(status_code=401, detail="Gebruiker niet gevonden of gedeactiveerd.")
    return {
        "id": row[0],
        "username": row[1],
        "name": row[2],
        "age": row[3],
        "bio": row[4],
        "preferred_min_age": row[5],
        "preferred_max_age": row[6],
        "strava_token": row[7],
    }


# -------------------- Startup / Shutdown --------------------
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

            
       # === User settings (nieuw) ===
        c.execute("""
        CREATE TABLE IF NOT EXISTS user_settings (
            user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
            match_goal TEXT,
            preferred_gender TEXT,
            max_distance_km INTEGER,
            notifications_enabled BOOLEAN
        )
        """)
        # === User availability (nieuw) ===
        c.execute("""
        CREATE TABLE IF NOT EXISTS user_availabilities (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            day_of_week SMALLINT NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),  -- 0=Maandag ... 6=Zondag
            start_time TIME NOT NULL,
            end_time TIME NOT NULL,
            timezone TEXT DEFAULT 'Europe/Brussels'
        )
        """)
        c.execute("CREATE INDEX IF NOT EXISTS idx_avail_user ON user_availabilities(user_id)")

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

        # Migratie: swipes.liked -> BOOLEAN (idempotent)
        c.execute(
            """
            SELECT data_type
            FROM information_schema.columns
            WHERE table_name = 'swipes' AND column_name = 'liked'
            """
        )
        row = c.fetchone()
        if row and row[0] != 'boolean':
            logger.warning("Migrating swipes.liked from %s to boolean ...", row[0])
            c.execute("ALTER TABLE swipes ALTER COLUMN liked TYPE BOOLEAN USING (liked <> 0)")
            logger.info("Migratie voltooid: swipes.liked is nu BOOLEAN.")

        # Migratie: chats.timestamp -> TIMESTAMPTZ (idempotent)
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


# -------------------- Endpoints --------------------

# === Profiel-modellen ===
class UserPublic(BaseModel):
    id: int
    username: str
    name: str
    age: int
    bio: Optional[str] = None

class UserUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    bio: Optional[str] = None

# === /me ===
@app.get("/me", response_model=UserPublic)
async def me(current_user: dict = Depends(get_current_user)):
    return {
        "id": current_user["id"],
        "username": current_user["username"],
        "name": current_user["name"],
        "age": current_user["age"],
        "bio": current_user["bio"],
    }

# === PATCH /users/{id} ===
@app.patch("/users/{user_id}", response_model=UserPublic)
async def patch_user(
    user_id: int,
    payload: UserUpdate,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    if user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Forbidden")
    conn, c = db

    updates = []
    values: List[Any] = []
    for k, v in payload.dict(exclude_unset=True).items():
        updates.append(f"{k}=%s")
        values.append(v)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    values.append(user_id)
    c.execute(
        f"UPDATE users SET {', '.join(updates)} WHERE id=%s AND deleted_at IS NULL",
        tuple(values)
    )
    c.execute("SELECT id, username, name, age, bio FROM users WHERE id=%s", (user_id,))
    row = c.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")

    return {"id": row[0], "username": row[1], "name": row[2], "age": row[3], "bio": row[4]}

# === User-settings model ===
class UserSettingsModel(BaseModel):
    match_goal: Optional[str] = None
    preferred_gender: Optional[str] = None
    max_distance_km: Optional[int] = None
    notifications_enabled: Optional[bool] = None
DEFAULT_SETTINGS = {
    "match_goal": "friendship",
    "preferred_gender": "any",
    "max_distance_km": 25,
    "notifications_enabled": True,
}

# === GET /users/{id}/settings ===
@app.get("/users/{user_id}/settings")
async def get_user_settings(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    if user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Forbidden")
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
        # als nog niet gezet: defaults teruggeven
        return DEFAULT_SETTINGS
    return {
        "match_goal": row[0],
        "preferred_gender": row[1],
        "max_distance_km": row[2],
        "notifications_enabled": row[3],
    }

# === POST /users/{id}/settings ===
@app.post("/users/{user_id}/settings")
async def save_user_settings(
    user_id: int,
    payload: UserSettingsModel,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    if user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Forbidden")
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
    return {"status": "success"}

from typing import Iterable

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
    if user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Forbidden")
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

# === Beschikbaarheden opslaan ===
@app.post("/users/{user_id}/availability")
async def save_availability(
    user_id: int,
    payload: List[AvailabilityItem],
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    if user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Forbidden")
    conn, c = db

    # Validatie
    for it in payload:
        if it.day_of_week < 0 or it.day_of_week > 6:
            raise HTTPException(status_code=422, detail="day_of_week moet 0..6 zijn")
        try:
            sh, sm = _validate_time(it.start_time)
            eh, em = _validate_time(it.end_time)
        except Exception as e:
            raise HTTPException(status_code=422, detail=str(e))
        if (eh, em) <= (sh, sm):
            raise HTTPException(status_code=422, detail="end_time moet later zijn dan start_time")

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
        return {"status": "success"}
    except psycopg2.Error:
        logger.exception("Databasefout bij het opslaan van beschikbaarheden.")
        raise HTTPException(status_code=500, detail="Databasefout bij het opslaan van beschikbaarheden.")


# === Profielfoto instellen ===
@app.post("/photos/{photo_id}/set_profile")
async def set_profile_photo(
    photo_id: int,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    conn, c = db
    user_id = current_user["id"]

    # Check eigendom
    c.execute("SELECT id FROM user_photos WHERE id=%s AND user_id=%s", (photo_id, user_id))
    row = c.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Foto niet gevonden of geen permissie.")

    # Reset en zet nieuwe
    c.execute("UPDATE user_photos SET is_profile_pic=0 WHERE user_id=%s", (user_id,))
    c.execute("UPDATE user_photos SET is_profile_pic=1 WHERE id=%s", (photo_id,))
    return {"status": "success"}

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
            # 401 doorgeven
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrecte gebruikersnaam of wachtwoord",
                headers={"WWW-Authenticate": "Bearer"},
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
        raise HTTPException(status_code=500, detail="Interne serverfout bij tokenaanmaak.")


@app.post("/register")
async def create_user(user: UserCreate, db=Depends(get_db)):
    conn, c = db
    password_hash = get_password_hash(user.password)
    try:
        c.execute(
            """
            INSERT INTO users (username, password_hash, name, age, bio, strava_token,
                               preferred_min_age, preferred_max_age, push_token, deleted_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,NULL)
            RETURNING id
            """,
            (
                user.username,
                password_hash,
                user.name,
                user.age,
                user.bio,
                None,  # strava_token initieel None
                None,  # preferred_min_age
                None,  # preferred_max_age
                None,  # push_token
            ),
        )
        
        
        user_id = c.fetchone()[0]
          logger.info("Nieuwe gebruiker aangemaakt: %s", user.username)
          return {
           "status": "success",
           "user_id": user_id,
           "username": user.username,
           "profile_pic_url": None,
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
        SELECT id, name, age, bio
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


    # Bepaal profielfoto (als die er is)
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
    if user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Geen toestemming om deze voorkeuren bij te werken.")
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
        return {"status": "success", "message": "Voorkeuren succesvol bijgewerkt."}
    except psycopg2.Error:
        logger.exception("Databasefout bij het bijwerken van voorkeuren.")
        raise HTTPException(status_code=500, detail="Databasefout bij het bijwerken van voorkeuren.")


@app.get("/suggestions")
async def get_suggestions(current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    conn, c = db
    user_id = current_user["id"]
    min_age = current_user.get("preferred_min_age")
    max_age = current_user.get("preferred_max_age")
    
query = """
 SELECT
    u.id, u.name, u.age, u.bio,
    prof.photo_url AS profile_photo_url,
    photos.photos   AS photos
    FROM users u
    -- Profielfoto (één)
    LEFT JOIN LATERAL (
    SELECT up.photo_url
    FROM user_photos up
    WHERE up.user_id = u.id AND up.is_profile_pic = 1
    ORDER BY up.id DESC
    LIMIT 1
    ) prof ON TRUE
    -- Alle foto's (profielfoto eerst)
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
    if min_age:
        query += " AND u.age >= %s"
        params.append(min_age)
    if max_age:
        query += " AND u.age <= %s"
        params.append(max_age)
    query += " LIMIT 200"
    c.execute(query, tuple(params))
    rows = c.fetchall()
    suggestions = []
    for r in rows:
    _photos = r[5] if isinstance(r[5], list) else []
    suggestions.append({
        "id": r[0],
        "name": r[1],
        "age": r[2],
        "bio": r[3],
        "profile_photo_url": r[4],
        "photos": _photos,
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
    user_id = current_user["id"]

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
            iso_ts = _to_isoz(ts)  # <-- robuuste normalisatie
            chat_history.append(ChatMessage(sender_id=sender_id, message=decrypted, timestamp=iso_ts))
        except Exception:
            logger.exception("Fout bij decoderen van bericht.")
            continue

    return {"chat_history": chat_history}


@app.post("/report_user")
async def report_user(report: ReportRequest, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    conn, c = db
    reporter_id = current_user["id"]
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
    blocker_id = current_user["id"]
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
    user_id = current_user["id"]
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
    user_id = current_user["id"]
    try:
        c.execute(
            "SELECT is_profile_pic FROM user_photos WHERE id = %s AND user_id = %s",
            (photo_id, user_id),
        )
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
    user_id = current_user["id"]
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


# -------------------- WebSocket --------------------
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
        # (extra check) user_id matchen met token's gebruiker
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


# -------------------- Route Suggestion --------------------
@app.get("/suggest_route/{match_id}")
async def get_route_suggestion(match_id: int, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    conn, c = db
    user_id = current_user["id"]

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
        raise HTTPException(status_code=403, detail="Geen toegang tot routevoorstellen (geen match).")

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
            detail=(
                "Kon geen recente Strava-locaties bepalen. "
                "Zorg dat beide gebruikers een geldig strava_token hebben of gebruik 'mock:LAT,LNG' voor testen."
            ),
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
    return {"status": "success", "route_suggestion": popular_route}


# -------------------- Health & Home --------------------
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


# -------------------- Main --------------------
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8000")),
        reload=True,
    )








