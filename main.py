from fastapi import FastAPI
import os
import logging
import re
import psycopg2
from datetime import datetime, timedelta
from typing import Optional
from haversine import haversine, Unit
from jose import JWTError, jwt
from cryptography.fernet import Fernet
from passlib.context import CryptContext
from fastapi import HTTPException, Depends, status, Response, Request, WebSocket, WebSocketDisconnect
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
# Gebruik de DATABASE_URL omgevingsvariabele van Railway.
# Dit is de aanbevolen methode voor Railway.
DATABASE_URL = os.environ.get('DATABASE_URL')

if not DATABASE_URL:
    logging.error("DATABASE_URL omgevingsvariabele is niet ingesteld!")
    raise Exception("DATABASE_URL omgevingsvariabele is niet ingesteld. Controleer of de PostgreSQL-database correct is gekoppeld.")

try:
    conn_pg = psycopg2.connect(DATABASE_URL)
    conn_pg.autocommit = True
    c_pg = conn_pg.cursor()
    logging.info("Succesvol verbonden met PostgreSQL database.")
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
# De SQL-query's hieronder zijn aangepast naar PostgreSQL-syntax en zijn correct voor de gegeven context.
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
        detail="Kon validatiegegevens niet verifiëren.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    c_pg.execute("SELECT id, username, name, age, bio, sport_type, avg_distance, last_lat, last_lng, availability, preferred_sport_type, preferred_min_age, preferred_max_age FROM users WHERE username = %s AND deleted_at IS NULL", (username,))
    user = c_pg.fetchone()

    if user is None:
        logger.warning(f"Gebruiker {username} niet gevonden in de database of soft-verwijderd.")
        raise credentials_exception
    
    user_data = {
        "id": user[0],
        "username": user[1],
        "name": user[2],
        "age": user[3],
        "bio": user[4],
        "sport_type": user[5],
        "avg_distance": user[6],
        "last_lat": user[7],
        "last_lng": user[8],
        "availability": user[9],
        "preferred_sport_type": user[10],
        "preferred_min_age": user[11],
        "preferred_max_age": user[12]
    }
    return user_data

# --- API Endpoints ---
@app.post("/token", response_model=Token)
async def login_for_access_token(response: Response, form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        c_pg.execute("SELECT password_hash FROM users WHERE username = %s AND deleted_at IS NULL", (form_data.username,))
        result = c_pg.fetchone()

        if not result or not verify_password(form_data.password, result[0]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrecte gebruikersnaam of wachtwoord",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": form_data.username}, expires_delta=access_token_expires
        )

        response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        logger.error(f"Fout bij het genereren van een token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Interne serverfout bij tokenaanmaak."
        )

@app.post("/register")
async def create_user(user: UserCreate):
    password_hash = get_password_hash(user.password)
    try:
        c_pg.execute("INSERT INTO users (username, password_hash, name, age, bio, sport_type, avg_distance, last_lat, last_lng, availability) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                  (user.username, password_hash, user.name, user.age, user.bio, user.sport_type, user.avg_distance, user.last_lat, user.last_lng, user.availability))
        conn_pg.commit()
        logger.info(f"Nieuwe gebruiker aangemaakt: {user.username}")
        
        # Voeg een default profielfoto toe
        default_photo_url = "https://example.com/default-profile.png"
        c_pg.execute("SELECT id FROM users WHERE username = %s", (user.username,))
        user_id = c_pg.fetchone()[0]
        c_pg.execute("INSERT INTO user_photos (user_id, photo_url, is_profile_pic) VALUES (%s, %s, %s)", (user_id, default_photo_url, 1))
        conn_pg.commit()
        
        return {"status": "success", "user_id": user_id, "username": user.username, "profile_pic_url": default_photo_url}
    except psycopg2.Error as e:
        conn_pg.rollback()
        logger.error(f"Databasefout bij het aanmaken van gebruiker: {e}")
        raise HTTPException(status_code=500, detail="Databasefout bij het aanmaken van gebruiker.")
    except Exception as e:
        logger.error(f"Algemene fout bij het aanmaken van gebruiker: {e}")
        raise HTTPException(status_code=500, detail="Interne serverfout")

@app.get("/users/{user_id}", response_model=UserProfile)
async def read_user(user_id: int, current_user: dict = Depends(get_current_user)):
    c_pg.execute("SELECT id, name, age, bio, sport_type, avg_distance, last_lat, last_lng, availability, strava_token FROM users WHERE id = %s AND deleted_at IS NULL", (user_id,))
    user = c_pg.fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="Gebruiker niet gevonden")

    # Fetch user photos
    c_pg.execute("SELECT photo_url FROM user_photos WHERE user_id = %s", (user_id,))
    photos = [row[0] for row in c_pg.fetchall()]
    
    strava_ytd_url = f"https://www.strava.com/athletes/{user[9]}/ytd" if user[9] else None

    logger.info(f"Gebruiker {current_user['id']} bekijkt profiel van gebruiker {user_id}.")

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
        "strava_ytd_url": strava_ytd_url
    }

@app.post("/users/{user_id}/preferences")
async def update_user_preferences(user_id: int, preferences: UserPreferences, current_user: dict = Depends(get_current_user)):
    if user_id != current_user['id']:
        raise HTTPException(status_code=403, detail="Geen toestemming om de voorkeuren van deze gebruiker bij te werken.")

    try:
        c_pg.execute("UPDATE users SET preferred_sport_type = %s, preferred_min_age = %s, preferred_max_age = %s WHERE id = %s",
                  (preferences.preferred_sport_type, preferences.preferred_min_age, preferences.preferred_max_age, user_id))
        conn_pg.commit()
        logger.info(f"Voorkeuren van gebruiker {user_id} succesvol bijgewerkt.")
        return {"status": "success", "message": "Voorkeuren succesvol bijgewerkt."}
    except psycopg2.Error as e:
        conn_pg.rollback()
        logger.error(f"Databasefout bij het bijwerken van voorkeuren: {e}")
        raise HTTPException(status_code=500, detail="Databasefout bij het bijwerken van voorkeuren.")

@app.get("/suggestions")
async def get_suggestions(current_user: dict = Depends(get_current_user)):
    user_id = current_user['id']
    lat = current_user['last_lat']
    lng = current_user['last_lng']
    sport_type = current_user.get('preferred_sport_type')
    min_age = current_user.get('preferred_min_age')
    max_age = current_user.get('preferred_max_age')

    # De SQL-query is geoptimaliseerd om reeds gelikete of geswipete gebruikers uit te sluiten en te filteren op sport en leeftijd.
    query = """
        SELECT id, name, age, bio, sport_type, avg_distance, last_lat, last_lng
        FROM users
        WHERE id != %s AND id NOT IN (
            SELECT swipee_id FROM swipes WHERE swiper_id = %s
        )
    """
    params = [user_id, user_id]

    if sport_type:
        query += " AND sport_type = %s"
        params.append(sport_type)
    if min_age:
        query += " AND age >= %s"
        params.append(min_age)
    if max_age:
        query += " AND age <= %s"
        params.append(max_age)

    c_pg.execute(query, tuple(params))
    suggestions = c_pg.fetchall()
    
    if not suggestions:
        return {"suggestions": []}

    # Bereken afstand en sorteer
    suggestions_with_distance = []
    for s in suggestions:
        distance = haversine((lat, lng), (s[6], s[7]), unit=Unit.KILOMETERS)
        # Filter op suggesties binnen 250 km
        if distance <= 250:
            suggestions_with_distance.append({
                "id": s[0],
                "name": s[1],
                "age": s[2],
                "bio": s[3],
                "sport_type": s[4],
                "avg_distance": s[5],
                "lat": s[6],
                "lng": s[7],
                "distance_km": round(distance, 2)
            })
    
    # Sort based on distance (closest first)
    suggestions_with_distance.sort(key=lambda x: x['distance_km'])

    logger.info(f"Suggesties gegenereerd voor gebruiker {user_id}. Aantal: {len(suggestions_with_distance)}")
    
    return {"suggestions": suggestions_with_distance}


@app.post("/swipe/{swipee_id}")
async def swipe(swipee_id: int, liked: int, current_user: dict = Depends(get_current_user)):
    swiper_id = current_user['id']

    if swiper_id == swipee_id:
        raise HTTPException(status_code=400, detail="Je kunt niet op je eigen profiel swipen.")

    try:
        c_pg.execute("INSERT INTO swipes (swiper_id, swipee_id, liked) VALUES (%s, %s, %s) ON CONFLICT (swiper_id, swipee_id) DO UPDATE SET liked = EXCLUDED.liked",
                  (swiper_id, swipee_id, liked))
        conn_pg.commit()
        logger.info(f"Gebruiker {swiper_id} heeft op gebruiker {swipee_id} geswipet (liked: {liked}).")

        # Check for a match
        if liked == 1:
            c_pg.execute("SELECT 1 FROM swipes WHERE swiper_id = %s AND swipee_id = %s AND liked = 1", (swipee_id, swiper_id))
            if c_pg.fetchone():
                logger.info(f"Nieuwe match tussen gebruiker {swiper_id} en gebruiker {swipee_id}.")
                return {"status": "success", "message": "Match!", "match": True}

        return {"status": "success", "message": "Swipe geregistreerd.", "match": False}
    except psycopg2.Error as e:
        conn_pg.rollback()
        logger.error(f"Databasefout bij het swipen: {e}")
        raise HTTPException(status_code=500, detail="Databasefout bij het swipen.")


@app.get("/matches")
async def get_matches(current_user: dict = Depends(get_current_user)):
    user_id = current_user['id']
    
    # Haal alle gebruikers op die door de huidige gebruiker geliked zijn en die de huidige gebruiker ook geliked hebben.
    c_pg.execute("""
        SELECT DISTINCT ON (match.id) match.id, match.name, match.age, match.photo_url
        FROM (
            SELECT u.id, u.name, u.age, up.photo_url
            FROM users u
            JOIN swipes s1 ON u.id = s1.swipee_id
            JOIN swipes s2 ON u.id = s2.swiper_id
            LEFT JOIN user_photos up ON u.id = up.user_id AND up.is_profile_pic = 1
            WHERE s1.swiper_id = %s AND s1.liked = 1 AND s2.swipee_id = %s AND s2.liked = 1
            AND u.deleted_at IS NULL
        ) AS match;
    """, (user_id, user_id))

    matches = c_pg.fetchall()

    if not matches:
        return {"matches": []}

    match_list = [{"id": row[0], "name": row[1], "age": row[2], "photo_url": row[3]} for row in matches]
    logger.info(f"Matches opgehaald voor gebruiker {user_id}. Aantal: {len(match_list)}")
    
    return {"matches": match_list}


@app.post("/send_message")
async def send_message(message: MessageIn, current_user: dict = Depends(get_current_user)):
    user_id = current_user['id']
    match_id = message.match_id
    plain_message = message.message
    timestamp = datetime.utcnow().isoformat()
    
    # Encrypt the message
    encrypted_message = cipher_suite.encrypt(plain_message.encode('utf-8')).decode('utf-8')
    
    # Check if the users are a match (bi-directional like)
    c_pg.execute("""
        SELECT 1 FROM swipes
        WHERE (swiper_id = %s AND swipee_id = %s AND liked = 1)
        AND EXISTS (SELECT 1 FROM swipes WHERE swiper_id = %s AND swipee_id = %s AND liked = 1)
        AND deleted_at IS NULL
    """, (user_id, match_id, match_id, user_id))
    
    if not c_pg.fetchone():
        raise HTTPException(status_code=403, detail="Bericht kan niet worden verzonden aan een gebruiker waarmee u geen match hebt.")

    # Save the message
    c_pg.execute("INSERT INTO chats (match_id, sender_id, encrypted_message, timestamp) VALUES (%s, %s, %s, %s)", (match_id, user_id, encrypted_message, timestamp))
    conn_pg.commit()
    logger.info(f"Chatbericht van gebruiker {user_id} naar gebruiker {match_id} succesvol opgeslagen.")
    
    return {"status": "success", "message": "Bericht verzonden."}

@app.get("/chat/{match_id}/messages")
async def get_chat_messages(match_id: int, current_user: dict = Depends(get_current_user)):
    user_id = current_user['id']
    
    # Check if the user is part of the match
    c_pg.execute("""
        SELECT 1 FROM swipes
        WHERE (swiper_id = %s AND swipee_id = %s AND liked = 1)
        AND EXISTS (SELECT 1 FROM swipes WHERE swiper_id = %s AND swipee_id = %s AND liked = 1)
        AND deleted_at IS NULL
    """, (user_id, match_id, match_id, user_id))

    if not c_pg.fetchone():
        raise HTTPException(status_code=403, detail="Geen toegang tot deze chat.")

    # Retrieve and decrypt messages
    c_pg.execute("SELECT sender_id, encrypted_message, timestamp FROM chats WHERE match_id = %s AND deleted_at IS NULL", (match_id,))
    messages = c_pg.fetchall()

    chat_history = []
    for sender_id, encrypted_message, timestamp in messages:
        try:
            decrypted_message = cipher_suite.decrypt(encrypted_message.encode('utf-8')).decode('utf-8')
            chat_history.append(ChatMessage(sender_id=sender_id, message=decrypted_message, timestamp=timestamp))
        except Exception as e:
            logger.error(f"Fout bij het decoderen van bericht: {e}")
            continue

    return {"chat_history": chat_history}


@app.post("/report_user")
async def report_user(report: ReportRequest, current_user: dict = Depends(get_current_user)):
    reporter_id = current_user['id']
    reported_id = report.reported_id
    reason = report.reason
    timestamp = datetime.utcnow()

    if reporter_id == reported_id:
        raise HTTPException(status_code=400, detail="Je kunt jezelf niet rapporteren.")

    try:
        c_pg.execute("INSERT INTO user_reports (reporter_id, reported_id, reason, timestamp) VALUES (%s, %s, %s, %s)",
                  (reporter_id, reported_id, reason, timestamp))
        conn_pg.commit()
        logger.info(f"Gebruiker {reported_id} succesvol gerapporteerd door gebruiker {reporter_id}.")
        return {"status": "success", "message": "Gebruiker succesvol gerapporteerd."}
    except psycopg2.Error as e:
        conn_pg.rollback()
        logger.error(f"Databasefout bij het rapporteren van gebruiker: {e}")
        raise HTTPException(status_code=500, detail="Databasefout bij het rapporteren van gebruiker.")

@app.post("/block_user")
async def block_user(user_to_block_id: int, current_user: dict = Depends(get_current_user)):
    blocker_id = current_user['id']
    timestamp = datetime.utcnow()
    
    if blocker_id == user_to_block_id:
        raise HTTPException(status_code=400, detail="Je kunt jezelf niet blokkeren.")

    try:
        c_pg.execute("INSERT INTO user_blocks (blocker_id, blocked_id, timestamp) VALUES (%s, %s, %s) ON CONFLICT (blocker_id, blocked_id) DO NOTHING",
                  (blocker_id, user_to_block_id, timestamp))
        conn_pg.commit()
        if c_pg.rowcount == 0:
            logger.warning(f"Gebruiker {user_to_block_id} was al geblokkeerd door gebruiker {blocker_id}.")
            return {"status": "success", "message": "Gebruiker was al geblokkeerd."}
            
        logger.info(f"Gebruiker {user_to_block_id} succesvol geblokkeerd door gebruiker {blocker_id}.")
        return {"status": "success", "message": "Gebruiker succesvol geblokkeerd."}
    except psycopg2.Error as e:
        conn_pg.rollback()
        logger.error(f"Databasefout bij het blokkeren van gebruiker: {e}")
        raise HTTPException(status_code=500, detail="Databasefout bij het blokkeren van gebruiker.")

@app.delete("/delete/match/{match_id}")
async def delete_match(match_id: int, current_user: dict = Depends(get_current_user)):
    user_id = current_user['id']

    c_pg.execute('''
        UPDATE swipes
        SET deleted_at = %s
        WHERE (swiper_id = %s AND swipee_id = %s AND liked = 1) OR (swiper_id = %s AND swipee_id = %s AND liked = 1)
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
        raise HTTPException(status_code=404, detail="Bericht niet gevonden of je hebt geen toestemming om het te verwijderen.")
        
    logger.info(f"Chatbericht {chat_id} van gebruiker {user_id} succesvol soft-verwijderd.")
    return {"status": "success", "message": "Bericht succesvol soft-verwijderd."}

@app.post("/upload_photo")
async def upload_photo(photo: PhotoUpload, current_user: dict = Depends(get_current_user)):
    user_id = current_user['id']
    photo_url = str(photo.photo_url)
    is_profile_pic = photo.is_profile_pic

    try:
        # Handle profile picture logic
        if is_profile_pic:
            # Set all existing profile pictures for this user to is_profile_pic = 0
            c_pg.execute("UPDATE user_photos SET is_profile_pic = 0 WHERE user_id = %s", (user_id,))
            conn_pg.commit()
            logger.info(f"Oude profielfoto's van gebruiker {user_id} gereset.")

        c_pg.execute("INSERT INTO user_photos (user_id, photo_url, is_profile_pic) VALUES (%s, %s, %s)", (user_id, photo_url, int(is_profile_pic)))
        conn_pg.commit()
        logger.info(f"Nieuwe foto succesvol geüpload voor gebruiker {user_id}. URL: {photo_url}, Profielfoto: {is_profile_pic}")
        
        return {"status": "success", "message": "Foto succesvol geüpload."}
    except psycopg2.Error as e:
        conn_pg.rollback()
        logger.error(f"Databasefout bij het uploaden van een foto: {e}")
        raise HTTPException(status_code=500, detail="Databasefout bij het uploaden van een foto.")
    except Exception as e:
        logger.error(f"Algemene fout bij het uploaden van een foto: {e}")
        raise HTTPException(status_code=500, detail="Interne serverfout bij het uploaden van de foto.")

@app.delete("/delete_photo/{photo_id}")
async def delete_photo(photo_id: int, current_user: dict = Depends(get_current_user)):
    user_id = current_user['id']
    
    try:
        # Check if the photo belongs to the current user and if it's the profile picture
        c_pg.execute("SELECT is_profile_pic FROM user_photos WHERE id = %s AND user_id = %s", (photo_id, user_id))
        result = c_pg.fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="Foto niet gevonden of je hebt geen toestemming om deze te verwijderen.")
            
        is_profile_pic = result[0]
        
        c_pg.execute("DELETE FROM user_photos WHERE id = %s AND user_id = %s", (photo_id, user_id))
        conn_pg.commit()
        
        if c_pg.rowcount == 0:
            raise HTTPException(status_code=404, detail="Foto niet gevonden.")

        logger.info(f"Foto {photo_id} succesvol verwijderd voor gebruiker {user_id}.")

        # If the deleted photo was the profile picture, assign a new one or handle accordingly
        if is_profile_pic == 1:
            c_pg.execute("SELECT id FROM user_photos WHERE user_id = %s LIMIT 1", (user_id,))
            new_profile_pic = c_pg.fetchone()
            if new_profile_pic:
                c_pg.execute("UPDATE user_photos SET is_profile_pic = 1 WHERE id = %s", (new_profile_pic[0],))
                conn_pg.commit()
                logger.info(f"Nieuwe profielfoto ({new_profile_pic[0]}) toegewezen na verwijdering van de vorige.")
            else:
                logger.warning(f"Alle foto's van gebruiker {user_id} zijn verwijderd. Geen profielfoto meer.")
                
        return {"status": "success", "message": "Foto succesvol verwijderd."}
    except psycopg2.Error as e:
        conn_pg.rollback()
        logger.error(f"Databasefout bij het verwijderen van een foto: {e}")
        raise HTTPException(status_code=500, detail="Databasefout bij het verwijderen van een foto.")

# WebSocket Endpoint for Chat
# Opmerking: Dit is een vereenvoudigde implementatie en vereist een WebSocket-client
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await websocket.accept()
    logger.info(f"WebSocket verbinding geaccepteerd voor gebruiker {user_id}.")
    
    try:
        while True:
            data = await websocket.receive_text()
            # Hier kun je de logica voor het verwerken van WebSocket-berichten implementeren
            # Zoals het opslaan van berichten en het doorsturen naar de andere gebruiker
            logger.info(f"Bericht ontvangen van gebruiker {user_id}: {data}")
            await websocket.send_text(f"Bericht ontvangen: {data}")
    except WebSocketDisconnect:
        logger.info(f"WebSocket verbinding gesloten voor gebruiker {user_id}.")
    except Exception as e:
        logger.error(f"WebSocket fout voor gebruiker {user_id}: {e}")

# Om uvicorn te draaien bij het direct uitvoeren van dit bestand
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
