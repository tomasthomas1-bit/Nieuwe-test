import os
import json
import logging
import re
import psycopg2
from datetime import datetime, timedelta
from typing import Optional
from haversine import haversine, Unit
from jose import JWTError, jwt
from cryptography.fernet import Fernet
from passlib.context import CryptContext
from fastapi import FastAPI, HTTPException, Depends, status, Response, Request, WebSocket, WebSocketDisconnect
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator, HttpUrl
import uvicorn

# --- Configuratie en Initialisatie ---

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- PostgreSQL Database Verbinding ---
import psycopg2

# Zorg ervoor dat psycopg2 is geïnstalleerd met 'pip install psycopg2-binary'

try:
    conn_pg = psycopg2.connect(
        host=os.environ.get("PGHOST"),
        database=os.environ.get("PGDATABASE"),
        user=os.environ.get("PGUSER"),
        password=os.environ.get("PGPASSWORD"),
        port=os.environ.get("PGPORT")
    )
    conn_pg.autocommit = True
    c_pg = conn_pg.cursor()
    logging.info("Verbonden met PostgreSQL database.")
except Exception as e:
    logging.error(f"Fout bij het verbinden met de database: {e}")
    # Deze 'raise' zorgt ervoor dat de container stopt als de verbinding mislukt
    raise Exception("Databaseverbinding mislukt")
















# --- Geheime Sleutels ophalen ---
SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY omgevingsvariabele is niet ingesteld!")

ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY")
if not ENCRYPTION_KEY:
    raise RuntimeError("ENCRYPTION_KEY omgevingsvariabele is niet ingesteld!")
cipher_suite = Fernet(ENCRYPTION_KEY.encode('utf-8'))

# --- Rest van de Code (Zelfde, maar met PostgreSQL syntax) ---

# De volledige, bijgewerkte code voor main.py volgt hieronder.
# Let op: de SQL-query's zijn aangepast naar PostgreSQL-syntax.

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# --- Logging Configuratie ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("fastapi_app")
logger.info("Applicatie wordt gestart...")

# --- Database Tabellen aanmaken in PostgreSQL ---
c_pg.execute('''CREATE TABLE IF NOT EXISTS users (
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
                deleted_at TIMESTAMP
            )''')
conn_pg.commit()

c_pg.execute('''CREATE TABLE IF NOT EXISTS swipes (
                swiper_id INTEGER,
                swipee_id INTEGER,
                liked INTEGER,
                PRIMARY KEY(swiper_id, swipee_id),
                deleted_at TIMESTAMP
            )''')
conn_pg.commit()

c_pg.execute('''CREATE TABLE IF NOT EXISTS chats (
                id SERIAL PRIMARY KEY,
                match_id INTEGER,
                sender_id INTEGER,
                encrypted_message TEXT,
                timestamp TEXT,
                deleted_at TIMESTAMP
            )''')
conn_pg.commit()

c_pg.execute('''CREATE TABLE IF NOT EXISTS user_photos (
                id SERIAL PRIMARY KEY,
                user_id INTEGER,
                photo_url TEXT,
                is_profile_pic INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )''')
conn_pg.commit()

c_pg.execute('''CREATE TABLE IF NOT EXISTS user_blocks (
                blocker_id INTEGER,
                blocked_id INTEGER,
                timestamp TIMESTAMP,
                PRIMARY KEY(blocker_id, blocked_id)
            )''')
conn_pg.commit()

c_pg.execute('''CREATE TABLE IF NOT EXISTS user_reports (
                id SERIAL PRIMARY KEY,
                reporter_id INTEGER,
                reported_id INTEGER,
                reason TEXT,
                timestamp TIMESTAMP
            )''')
conn_pg.commit()

# --- Pydantic Modellen voor Datavalidatie ---
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    name: str = Field(..., min_length=2, max_length=50)
    age: int = Field(..., gt=17, lt=100)
    bio: Optional[str] = Field(None, max_length=500)
    sport_type: str
    avg_distance: float
    last_lat: float
    last_lng: float
    availability: str

class UserCreate(UserBase):
    password: str

    @validator('password')
    def validate_password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Wachtwoord moet minimaal 8 karakters lang zijn.')
        if not re.search(r"[a-z]", v):
            raise ValueError('Wachtwoord moet minimaal één kleine letter bevatten.')
        if not re.search(r"[A-Z]", v):
            raise ValueError('Wachtwoord moet minimaal één hoofdletter bevatten.')
        if not re.search(r"[0-9]", v):
            raise ValueError('Wachtwoord moet minimaal één cijfer bevatten.')
        if not re.search(r"[#?!@$%^&*-]", v):
            raise ValueError('Wachtwoord moet minimaal één speciaal karakter bevatten.')
        return v

class UserInDB(UserBase):
    password_hash: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UserProfile(BaseModel):
    id: int
    name: str
    age: int
    bio: Optional[str] = None
    sport_type: str
    avg_distance: float
    lat: float
    lng: float
    photos: list[str] = []
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
    timestamp: str

class ReportRequest(BaseModel):
    reported_id: int
    reason: str

class PhotoUpload(BaseModel):
    photo_url: HttpUrl
    is_profile_pic: Optional[bool] = False

# --- Authenticatie Hulpmiddelen ---
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        logger.error(f"JWT Error: {credentials_exception.detail}")
        raise credentials_exception
    
    c_pg.execute("SELECT id, username, name, age, bio, sport_type, avg_distance, last_lat, last_lng, availability, preferred_sport_type, preferred_min_age, preferred_max_age FROM users WHERE username = %s AND deleted_at IS NULL", (username,))
    user = c_pg.fetchone()
    if user is None:
        logger.warning(f"Gebruiker '{username}' niet gevonden of verwijderd tijdens authenticatie.")
        raise HTTPException(status_code=404, detail="Gebruiker niet gevonden of verwijderd")
    
    user_dict = {
        "id": user[0], "username": user[1], "name": user[2], "age": user[3], "bio": user[4],
        "sport_type": user[5], "avg_distance": user[6], "last_lat": user[7], "last_lng": user[8], "availability": user[9],
        "preferred_sport_type": user[10], "preferred_min_age": user[11], "preferred_max_age": user[12]
    }
    return user_dict

# --- Logica en Hulpmiddelen ---
def get_bounding_box(lat: float, lon: float, distance_in_km: float):
    lat_deg = distance_in_km / 111.0
    lon_deg = distance_in_km / (111.0 * abs(lat_deg))
    min_lat, max_lat = lat - lat_deg, lat + lat_deg
    min_lon, max_lon = lon - lon_deg, lon + lon_deg
    return min_lat, max_lat, min_lon, max_lon

def send_push_notification(user_id: int, message: str):
    c_pg.execute("SELECT push_token FROM users WHERE id = %s", (user_id,))
    push_token = c_pg.fetchone()
    if push_token and push_token[0]:
        logger.info(f"Stuur push melding naar gebruiker {user_id}: '{message}'")
    else:
        logger.info(f"Geen push token gevonden voor gebruiker {user_id}. Geen melding verstuurd.")

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f"Gebruiker {user_id} verbonden via WebSocket.")

    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        logger.info(f"Gebruiker {user_id} ontkoppeld.")

    async def send_message(self, message: dict, user_id: int):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_json(message)

manager = ConnectionManager()

# --- Endpoint Definities ---

@app.post("/register", response_model=UserInDB)
async def register(user_data: UserCreate):
    c_pg.execute("SELECT id FROM users WHERE username = %s", (user_data.username,))
    if c_pg.fetchone():
        logger.warning(f"Registratiepoging mislukt: gebruikersnaam '{user_data.username}' bestaat al.")
        raise HTTPException(status_code=400, detail="Gebruikersnaam bestaat al")
    
    try:
        hashed_password = get_password_hash(user_data.password)
        c_pg.execute(
            "INSERT INTO users (username, password_hash, name, age, bio, sport_type, avg_distance, last_lat, last_lng, availability, strava_token, preferred_sport_type, preferred_min_age, preferred_max_age) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id",
            (user_data.username, hashed_password, user_data.name, user_data.age, user_data.bio, user_data.sport_type, user_data.avg_distance, user_data.last_lat, user_data.last_lng, user_data.availability, None, None, None, None)
        )
        conn_pg.commit()
        logger.info(f"Nieuwe gebruiker geregistreerd: '{user_data.username}'")
        
        c_pg.execute("SELECT id, username, name, password_hash, age, bio, sport_type, avg_distance, last_lat, last_lng, availability FROM users WHERE username = %s", (user_data.username,))
        user = c_pg.fetchone()
        
        return {
            "id": user[0], "username": user[1], "name": user[2], "password_hash": user[3],
            "age": user[4], "bio": user[5], "sport_type": user[6], "avg_distance": user[7],
            "last_lat": user[8], "last_lng": user[9], "availability": user[10]
        }
    except Exception as e:
        logger.error(f"Fout tijdens registratie: {e}")
        raise HTTPException(status_code=500, detail="Er is een onbekende fout opgetreden. Probeer het later opnieuw.")

@app.post("/token")
async def login_for_access_token(response: Response, form_data: OAuth2PasswordRequestForm = Depends()):
    c_pg.execute("SELECT password_hash FROM users WHERE username = %s AND deleted_at IS NULL", (form_data.username,))
    user_hash = c_pg.fetchone()
    if not user_hash or not verify_password(form_data.password, user_hash[0]):
        logger.warning(f"Mislukte inlogpoging voor gebruiker '{form_data.username}'.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": form_data.username}, expires_delta=access_token_expires)

    refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = create_access_token(data={"sub": form_data.username}, expires_delta=refresh_token_expires)
    
    logger.info(f"Gebruiker '{form_data.username}' succesvol ingelogd.")
    
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        samesite="strict",
        secure=True if os.environ.get("ENV") == "production" else False
    )

    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/refresh_token", response_model=Token)
async def refresh_token(request: Request):
    refresh_token_from_cookie = request.cookies.get("refresh_token")
    if not refresh_token_from_cookie:
        logger.warning("Token refresh mislukt: geen refresh token gevonden.")
        raise HTTPException(status_code=401, detail="Je sessie is verlopen. Log opnieuw in.")
    
    try:
        payload = jwt.decode(refresh_token_from_cookie, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Ongeldig refresh token")
    except JWTError:
        logger.error(f"Token refresh mislukt: ongeldige JWT.")
        raise HTTPException(status_code=401, detail="Je sessie is verlopen. Log opnieuw in.")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": username}, expires_delta=access_token_expires)
    
    logger.info(f"Access token vernieuwd voor gebruiker '{username}'.")
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/swipe/{swipee_id}/{liked}")
async def swipe(swipee_id: int, liked: int, current_user: dict = Depends(get_current_user)):
    swiper_id = current_user["id"]
    
    if liked not in [0, 1]:
        raise HTTPException(status_code=400, detail="Waarde voor 'liked' moet 0 of 1 zijn.")
    
    if swiper_id == swipee_id:
        raise HTTPException(status_code=400, detail="Je kunt jezelf niet swipen.")

    c_pg.execute("SELECT id FROM users WHERE id = %s AND deleted_at IS NULL", (swipee_id,))
    if not c_pg.fetchone():
        raise HTTPException(status_code=404, detail="Dit profiel bestaat niet meer.")

    c_pg.execute('''INSERT INTO swipes (swiper_id, swipee_id, liked) VALUES (%s, %s, %s) ON CONFLICT (swiper_id, swipee_id) DO UPDATE SET liked = EXCLUDED.liked, deleted_at = NULL''', (swiper_id, swipee_id, liked))
    conn_pg.commit()
    logger.info(f"Gebruiker {swiper_id} heeft geswipet op gebruiker {swipee_id} met liked={liked}.")

    if liked == 1:
        c_pg.execute('''
            SELECT 1 FROM swipes s1
            JOIN swipes s2 ON s1.swiper_id = s2.swipee_id AND s1.swipee_id = s2.swiper_id
            WHERE s1.swiper_id=%s AND s1.liked=1 AND s2.liked=1 AND s1.deleted_at IS NULL AND s2.deleted_at IS NULL
        ''', (swiper_id,))
        if c_pg.fetchone():
            send_push_notification(swipee_id, f"Je hebt een match met {current_user['name']}!")
            logger.info(f"Match gevonden tussen gebruiker {swiper_id} en {swipee_id}.")
            return {"status": "match_found", "message": "Gefeliciteerd! Je hebt een match!"}

    return {"status": "swipe_saved", "message": "Swipe succesvol opgeslagen."}

@app.get("/matches", response_model=list[UserProfile])
async def get_matches(current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]

    query = '''
        SELECT u.id, u.name, u.age, u.bio, u.sport_type, u.avg_distance, u.last_lat, u.last_lng, u.strava_token
        FROM swipes s1
        JOIN swipes s2 ON s1.swiper_id = s2.swipee_id AND s1.swipee_id = s2.swiper_id
        JOIN users u ON u.id = s1.swipee_id
        WHERE s1.swiper_id = %s AND s1.liked = 1 AND s2.liked = 1 AND s1.deleted_at IS NULL
    '''
    c_pg.execute(query, (user_id,))
    pre_filtered_matches = c_pg.fetchall()
    
    logger.info(f"Gebruiker {user_id} heeft zijn matches opgehaald.")

    final_matches = []
    for match in pre_filtered_matches:
        match_user_id = match[0]
        c_pg.execute("SELECT photo_url FROM user_photos WHERE user_id = %s", (match_user_id,))
        photos = [row[0] for row in c_pg.fetchall()]
        strava_token = match[8]
        strava_ytd_url = f"https://api.strava.com/ytd/{match_user_id}.jpg" if strava_token else None
        
        final_matches.append(UserProfile(
            id=match[0], name=match[1], age=match[2], bio=match[3], sport_type=match[4],
            avg_distance=match[5], lat=match[6], lng=match[7], photos=photos,
            strava_ytd_url=strava_ytd_url
        ))
    return final_matches

@app.get("/chats/{match_id}", response_model=list[ChatMessage])
async def get_chat_history(match_id: int, current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]

    c_pg.execute('''SELECT 1 FROM swipes s1 JOIN swipes s2
                 ON s1.swiper_id = s2.swipee_id AND s1.swipee_id = s2.swipee_id
                 WHERE ((s1.swiper_id = %s AND s1.swipee_id = %s) OR (s1.swiper_id = %s AND s1.swipee_id = %s))
                 AND s1.liked = 1 AND s2.liked = 1 AND s1.deleted_at IS NULL AND s2.deleted_at IS NULL
              ''', (user_id, match_id, match_id, user_id))
    if not c_pg.fetchone():
        logger.warning(f"Gebruiker {user_id} probeerde toegang te krijgen tot chat {match_id} zonder toestemming.")
        raise HTTPException(status_code=403, detail="Je hebt geen toegang tot deze chat.")

    c_pg.execute('SELECT sender_id, encrypted_message, timestamp FROM chats WHERE match_id = %s AND deleted_at IS NULL ORDER BY timestamp ASC', (match_id,))
    messages = c_pg.fetchall()
    
    logger.info(f"Chatgeschiedenis opgehaald voor match {match_id} door gebruiker {user_id}.")

    chat_history = []
    for sender_id, encrypted_message, timestamp in messages:
        decrypted_message = cipher_suite.decrypt(encrypted_message).decode('utf-8')
        chat_history.append(ChatMessage(
            sender_id=sender_id,
            message=decrypted_message,
            timestamp=timestamp
        ))
    
    return chat_history

@app.websocket("/ws/chat/{match_id}")
async def websocket_chat(websocket: WebSocket, match_id: int, token: str):
    try:
        current_user = get_current_user(token)
    except HTTPException:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        logger.warning("WebSocket connectie geweigerd vanwege ongeldige token.")
        return

    user_id = current_user['id']
    
    c_pg.execute('''SELECT 1 FROM swipes s1 JOIN swipes s2
                 ON s1.swiper_id = s2.swipee_id AND s1.swipee_id = s2.swipee_id
                 WHERE ((s1.swiper_id = %s AND s1.swipee_id = %s) OR (s1.swiper_id = %s AND s1.swipee_id = %s))
                 AND s1.liked = 1 AND s2.liked = 1
              ''', (user_id, match_id, match_id, user_id))
    if not c_pg.fetchone():
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        logger.warning(f"WebSocket connectie geweigerd voor gebruiker {user_id} naar match {match_id} vanwege geen toestemming.")
        return

    await manager.connect(websocket, user_id)
    
    c_pg.execute("SELECT swipee_id FROM swipes WHERE swiper_id = %s AND liked = 1", (user_id,))
    other_user_id = c_pg.fetchone()[0]

    try:
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type")

            if message_type == "message":
                message = data.get("content")
                if not message:
                    continue

                encrypted_message = cipher_suite.encrypt(message.encode('utf-8'))
                timestamp = datetime.now().isoformat()
                
                c_pg.execute('INSERT INTO chats (match_id, sender_id, encrypted_message, timestamp, deleted_at) VALUES (%s, %s, %s, %s, %s)',
                          (match_id, user_id, encrypted_message, timestamp, None))
                conn_pg.commit()
                
                chat_message = {
                    "type": "message",
                    "sender_id": user_id,
                    "content": message,
                    "timestamp": timestamp
                }
                
                await manager.send_message(chat_message, user_id)
                await manager.send_message(chat_message, other_user_id)
                
                send_push_notification(other_user_id, f"Nieuw bericht van {current_user['name']}!")
                logger.info(f"Bericht van gebruiker {user_id} verstuurd in match {match_id}.")

            elif message_type == "typing":
                await manager.send_message({"type": "typing", "is_typing": data.get("is_typing")}, other_user_id)
                
            elif message_type == "delivered":
                await manager.send_message({"type": "delivered"}, other_user_id)

            elif message_type == "read":
                await manager.send_message({"type": "read"}, other_user_id)

    except WebSocketDisconnect:
        manager.disconnect(user_id)
    except Exception as e:
        logger.error(f"WebSocket fout voor gebruiker {user_id}: {e}")
        manager.disconnect(user_id)

@app.get("/discover", response_model=list[UserProfile])
async def discover_users(
    max_distance: Optional[float] = 50.0,
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["id"]
    user_lat, user_lng = current_user["last_lat"], current_user["last_lng"]
    
    preferred_sport_type = current_user.get("preferred_sport_type")
    preferred_min_age = current_user.get("preferred_min_age")
    preferred_max_age = current_user.get("preferred_max_age")

    c_pg.execute("SELECT blocked_id FROM user_blocks WHERE blocker_id = %s", (user_id,))
    blocked_by_me = [row[0] for row in c_pg.fetchall()]

    c_pg.execute("SELECT blocker_id FROM user_blocks WHERE blocked_id = %s", (user_id,))
    blocked_me = [row[0] for row in c_pg.fetchall()]

    excluded_users = blocked_by_me + blocked_me + [user_id]
    
    query = '''
        SELECT u.id, u.name, u.age, u.bio, u.sport_type, u.avg_distance, u.last_lat, u.last_lng, u.strava_token
        FROM users u
        LEFT JOIN swipes s ON u.id = s.swipee_id AND s.swiper_id = %s
        WHERE s.swipee_id IS NULL AND u.deleted_at IS NULL AND u.id NOT IN %s
    '''
    
    params = tuple([user_id]) + (tuple(excluded_users),)
    c_pg.execute(query, params)
    potential_users = c_pg.fetchall()

    scored_users = []
    for user in potential_users:
        score = 0
        other_user_id, name, age, bio, sport_type, avg_distance, lat, lng, strava_token = user
        
        distance = haversine((user_lat, user_lng), (lat, lng), unit=Unit.KILOMETERS)
        if distance <= max_distance:
            score += max(0, 100 - (distance * 2))

        if preferred_sport_type and preferred_sport_type.lower() == sport_type.lower():
            score += 50
        
        if preferred_min_age and preferred_max_age and preferred_min_age <= age <= preferred_max_age:
            score += 50

        if score > 0:
            c_pg.execute("SELECT photo_url FROM user_photos WHERE user_id = %s", (other_user_id,))
            photos = [row[0] for row in c_pg.fetchall()]
            strava_ytd_url = f"https://api.strava.com/ytd/{other_user_id}.jpg" if strava_token else None
            
            scored_users.append({
                "score": score,
                "profile": UserProfile(
                    id=other_user_id, name=name, age=age, bio=bio, sport_type=sport_type,
                    avg_distance=avg_distance, lat=lat, lng=lng, photos=photos,
                    strava_ytd_url=strava_ytd_url
                )
            })
            
    scored_users.sort(key=lambda x: x["score"], reverse=True)
    
    logger.info(f"Gebruiker {user_id} heeft {len(scored_users)} profielen ontdekt.")
    
    return [item["profile"] for item in scored_users]

@app.post("/upload_photo")
async def upload_photo(photo_data: PhotoUpload, current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    is_profile_pic_int = 1 if photo_data.is_profile_pic else 0

    c_pg.execute("SELECT COUNT(*) FROM user_photos WHERE user_id = %s", (user_id,))
    current_photo_count = c_pg.fetchone()[0]
    
    if current_photo_count >= 5:
        logger.warning(f"Gebruiker {user_id} probeerde meer dan 5 foto's te uploaden.")
        raise HTTPException(status_code=400, detail="Je kunt niet meer dan 5 foto's uploaden.")
    
    if is_profile_pic_int == 1:
        c_pg.execute("UPDATE user_photos SET is_profile_pic = 0 WHERE user_id = %s", (user_id,))
        conn_pg.commit()

    c_pg.execute(
        "INSERT INTO user_photos (user_id, photo_url, is_profile_pic) VALUES (%s, %s, %s)",
        (user_id, str(photo_data.photo_url), is_profile_pic_int)
    )
    conn_pg.commit()
    logger.info(f"Foto succesvol geüpload door gebruiker {user_id}.")
    return {"status": "success", "message": "Foto succesvol geüpload."}

@app.post("/link_strava")
async def link_strava(strava_token: str, current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    
    c_pg.execute("UPDATE users SET strava_token = %s WHERE id = %s", (strava_token, user_id))
    conn_pg.commit()
    logger.info(f"Strava-account succesvol gekoppeld voor gebruiker {user_id}.")
    return {"status": "success", "message": "Strava-account succesvol gekoppeld."}

@app.post("/update_profile")
async def update_profile(
    preferences: UserPreferences,
    bio: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["id"]
    
    c_pg.execute('''
        UPDATE users
        SET bio = COALESCE(%s, bio),
            preferred_sport_type = COALESCE(%s, preferred_sport_type),
            preferred_min_age = COALESCE(%s, preferred_min_age),
            preferred_max_age = COALESCE(%s, preferred_max_age)
        WHERE id = %s
    ''', (
        bio,
        preferences.preferred_sport_type,
        preferences.preferred_min_age,
        preferences.preferred_max_age,
        user_id
    ))
    conn_pg.commit()
    
    logger.info(f"Profiel succesvol bijgewerkt voor gebruiker {user_id}.")
    
    return {"status": "success", "message": "Profiel succesvol bijgewerkt."}

# NIEUWE ENDPOINTS voor veiligheid en verwijdering
@app.post("/block/{blocked_id}")
async def block_user(blocked_id: int, current_user: dict = Depends(get_current_user)):
    blocker_id = current_user['id']
    if blocker_id == blocked_id:
        raise HTTPException(status_code=400, detail="Je kunt jezelf niet blokkeren.")
    
    c_pg.execute("INSERT INTO user_blocks (blocker_id, blocked_id, timestamp) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
              (blocker_id, blocked_id, datetime.utcnow().isoformat()))
    conn_pg.commit()
    logger.info(f"Gebruiker {blocker_id} heeft gebruiker {blocked_id} geblokkeerd.")
    return {"status": "success", "message": "Gebruiker succesvol geblokkeerd."}

@app.post("/report")
async def report_user(report: ReportRequest, current_user: dict = Depends(get_current_user)):
    reporter_id = current_user['id']
    if reporter_id == report.reported_id:
        raise HTTPException(status_code=400, detail="Je kunt jezelf niet rapporteren.")
    
    c_pg.execute("INSERT INTO user_reports (reporter_id, reported_id, reason, timestamp) VALUES (%s, %s, %s, %s)",
              (reporter_id, report.reported_id, report.reason, datetime.utcnow().isoformat()))
    conn_pg.commit()
    logger.info(f"Gebruiker {reporter_id} heeft gebruiker {report.reported_id} gerapporteerd met reden: '{report.reason}'.")
    return {"status": "success", "message": "Rapport succesvol ingediend."}

@app.delete("/delete/profile")
async def delete_profile(current_user: dict = Depends(get_current_user)):
    user_id = current_user['id']
    
    timestamp = datetime.utcnow().isoformat()
    
    c_pg.execute("UPDATE users SET deleted_at = %s WHERE id = %s", (timestamp, user_id))
    c_pg.execute("UPDATE swipes SET deleted_at = %s WHERE swiper_id = %s OR swipee_id = %s", (timestamp, user_id, user_id))
    c_pg.execute("UPDATE chats SET deleted_at = %s WHERE sender_id = %s", (timestamp, user_id))
    conn_pg.commit()
    
    logger.info(f"Profiel en gerelateerde data van gebruiker {user_id} zijn soft-verwijderd.")
    
    return {"status": "success", "message": "Profiel en gerelateerde data zijn soft-verwijderd."}

@app.delete("/delete/match/{match_id}")
async def delete_match(match_id: int, current_user: dict = Depends(get_current_user)):
    user_id = current_user['id']

    c_pg.execute('''
        UPDATE swipes
        SET deleted_at = %s
        WHERE (swiper_id = %s AND swipee_id = %s) OR (swiper_id = %s AND swipee_id = %s)
    ''', (datetime.utcnow().isoformat(), user_id, match_id, match_id, user_id))
    
    conn_pg.commit()
    logger.info(f"Match met gebruiker {match_id} soft-verwijderd door gebruiker {user_id}.")
    return {"status": "success", "message": "Match succesvol soft-verwijderd."}

@app.delete("/delete/chat/{chat_id}")
async def delete_chat_message(chat_id: int, current_user: dict = Depends(get_current_user)):
    user_id = current_user['id']

    c_pg.execute("UPDATE chats SET deleted_at = %s WHERE id = %s AND sender_id = %s",
              (datetime.utcnow().isoformat(), chat_id, user_id))
    conn_pg.commit()

    if c_pg.rowcount == 0:
        logger.warning(f"Gebruiker {user_id} kon chatbericht {chat_id} niet vinden om te verwijderen.")
        raise HTTPException(status_code=404, detail="Bericht niet gevonden of je hebt geen toestemming het te verwijderen.")
    
    logger.info(f"Chatbericht {chat_id} soft-verwijderd door gebruiker {user_id}.")
    return {"status": "success", "message": "Chatbericht succesvol soft-verwijderd."}

# --- Start de applicatie ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="debug")


