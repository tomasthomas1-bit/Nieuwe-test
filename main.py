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
        refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

        access_token = create_access_token(
            data={"sub": form_data.username}, expires_delta=access_token_expires
        )
        refresh_token = create_access_token(
            data={"sub": form_data.username}, expires_delta=refresh_token_expires
        )

        # Set the refresh token as a cookie
        response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, secure=True, samesite="strict")
        logger.info(f"Gebruiker {form_data.username} succesvol ingelogd.")
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        logger.error(f"Fout bij inloggen voor gebruiker {form_data.username}: {e}")
        raise HTTPException(status_code=500, detail="Interne serverfout bij inloggen")

@app.post("/refresh-token", response_model=Token)
async def refresh_access_token(request: Request, response: Response):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Geen refresh token gevonden")

    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Ongeldig refresh token")

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        new_access_token = create_access_token(data={"sub": username}, expires_delta=access_token_expires)
        
        logger.info(f"Access token vernieuwd voor gebruiker {username}.")
        return {"access_token": new_access_token, "token_type": "bearer"}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Ongeldig refresh token")

@app.post("/users", response_model=UserProfile)
async def create_user(user: UserCreate):
    try:
        # Check if the username already exists
        c_pg.execute("SELECT id FROM users WHERE username = %s AND deleted_at IS NULL", (user.username,))
        existing_user = c_pg.fetchone()
        if existing_user:
            raise HTTPException(status_code=400, detail="Gebruikersnaam bestaat al")

        # Hash the password
        hashed_password = get_password_hash(user.password)

        # Insert new user into the database
        c_pg.execute("INSERT INTO users (username, password_hash, name, age, bio, sport_type, avg_distance, last_lat, last_lng, availability) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                     (user.username, hashed_password, user.name, user.age, user.bio, user.sport_type, user.avg_distance, user.last_lat, user.last_lng, user.availability))
        conn_pg.commit()

        # Fetch the newly created user's ID
        c_pg.execute("SELECT id FROM users WHERE username = %s AND deleted_at IS NULL", (user.username,))
        user_id = c_pg.fetchone()[0]

        logger.info(f"Nieuwe gebruiker {user.username} (ID: {user_id}) aangemaakt.")
        return {**user.dict(exclude={'password'}), "id": user_id, "lat": user.last_lat, "lng": user.last_lng, "photos": []}
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
        "strava_ytd_url": user[9] if user[9] else None
    }

@app.put("/users/me", response_model=UserProfile)
async def update_current_user(updated_user: UserBase, current_user: dict = Depends(get_current_user)):
    user_id = current_user['id']
    try:
        # Update user data in the database
        c_pg.execute("UPDATE users SET name = %s, age = %s, bio = %s, sport_type = %s, avg_distance = %s, last_lat = %s, last_lng = %s, availability = %s WHERE id = %s",
                     (updated_user.name, updated_user.age, updated_user.bio, updated_user.sport_type, updated_user.avg_distance, updated_user.last_lat, updated_user.last_lng, updated_user.availability, user_id))
        conn_pg.commit()
        logger.info(f"Profiel van gebruiker {user_id} succesvol bijgewerkt.")
        return {**updated_user.dict(), "id": user_id, "lat": updated_user.last_lat, "lng": updated_user.last_lng, "photos": []}
    except psycopg2.Error as e:
        conn_pg.rollback()
        logger.error(f"Databasefout bij het bijwerken van gebruiker {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Databasefout bij het bijwerken van gebruiker.")

@app.put("/users/me/preferences")
async def update_user_preferences(preferences: UserPreferences, current_user: dict = Depends(get_current_user)):
    user_id = current_user['id']
    try:
        c_pg.execute("UPDATE users SET preferred_sport_type = %s, preferred_min_age = %s, preferred_max_age = %s WHERE id = %s",
                     (preferences.preferred_sport_type, preferences.preferred_min_age, preferences.preferred_max_age, user_id))
        conn_pg.commit()
        logger.info(f"Voorkeuren van gebruiker {user_id} succesvol bijgewerkt.")
        return {"status": "success", "message": "Voorkeuren succesvol bijgewerkt."}
    except psycopg2.Error as e:
        conn_pg.rollback()
        logger.error(f"Databasefout bij het bijwerken van voorkeuren voor gebruiker {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Databasefout bij het bijwerken van voorkeuren.")

@app.get("/suggestions")
async def get_suggestions(current_user: dict = Depends(get_current_user)):
    user_id = current_user['id']
    lat, lng = current_user['last_lat'], current_user['last_lng']
    sport_type = current_user.get('preferred_sport_type')
    min_age = current_user.get('preferred_min_age')
    max_age = current_user.get('preferred_max_age')

    # Base query to find potential matches
    query = """
    SELECT id, name, age, bio, sport_type, avg_distance, last_lat, last_lng
    FROM users
    WHERE id != %s AND deleted_at IS NULL
    AND id NOT IN (SELECT swipee_id FROM swipes WHERE swiper_id = %s)
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

    logger.info(f"Suggesties gegenereerd voor gebruiker {user_id}.")
    return {"suggestions": suggestions_with_distance}


@app.post("/swipe")
async def record_swipe(swipe_data: dict, current_user: dict = Depends(get_current_user)):
    swiper_id = current_user['id']
    swipee_id = swipe_data.get("swipee_id")
    liked = swipe_data.get("liked")

    if not swipee_id or liked is None:
        raise HTTPException(status_code=400, detail="Ontbrekende gegevens: swipee_id en liked zijn verplicht")

    try:
        # Record the swipe
        c_pg.execute("INSERT INTO swipes (swiper_id, swipee_id, liked) VALUES (%s, %s, %s) ON CONFLICT (swiper_id, swipee_id) DO UPDATE SET liked = EXCLUDED.liked, deleted_at = NULL",
                     (swiper_id, swipee_id, liked))
        conn_pg.commit()

        if liked:
            # Check for a match (the other user also liked this user)
            c_pg.execute("SELECT liked FROM swipes WHERE swiper_id = %s AND swipee_id = %s", (swipee_id, swiper_id))
            result = c_pg.fetchone()
            
            if result and result[0] == 1:
                logger.info(f"Nieuwe match: {swiper_id} en {swipee_id}.")
                return {"status": "match", "message": "Het is een match!"}
            else:
                logger.info(f"Gebruiker {swiper_id} veegt rechts op {swipee_id}.")
                return {"status": "success", "message": "Swipe succesvol opgeslagen."}
        else:
            logger.info(f"Gebruiker {swiper_id} veegt links op {swipee_id}.")
            return {"status": "success", "message": "Swipe succesvol opgeslagen."}

    except psycopg2.Error as e:
        conn_pg.rollback()
        logger.error(f"Databasefout bij het opslaan van swipe: {e}")
        raise HTTPException(status_code=500, detail="Databasefout bij het opslaan van de swipe.")

@app.post("/chat")
async def send_chat_message(message_data: MessageIn, current_user: dict = Depends(get_current_user)):
    user_id = current_user['id']
    match_id = message_data.match_id
    message = message_data.message

    # Encrypt the message
    encrypted_message = cipher_suite.encrypt(message.encode('utf-8')).decode('utf-8')
    timestamp = datetime.utcnow().isoformat()

    try:
        # Check if a match exists between the users
        c_pg.execute("""
            SELECT 1 FROM swipes WHERE
            (swiper_id = %s AND swipee_id = %s AND liked = 1) OR
            (swiper_id = %s AND swipee_id = %s AND liked = 1)
        """, (user_id, match_id, match_id, user_id))
        
        if not c_pg.fetchone():
            raise HTTPException(status_code=403, detail="Bericht kan niet worden verzonden aan een gebruiker waarmee u geen match hebt.")

        # Save the message
        c_pg.execute("INSERT INTO chats (match_id, sender_id, encrypted_message, timestamp) VALUES (%s, %s, %s, %s)",
                     (match_id, user_id, encrypted_message, timestamp))
        conn_pg.commit()
        logger.info(f"Chatbericht van gebruiker {user_id} naar gebruiker {match_id} succesvol opgeslagen.")
        return {"status": "success", "message": "Bericht verzonden."}
    except psycopg2.Error as e:
        conn_pg.rollback()
        logger.error(f"Databasefout bij het verzenden van chatbericht: {e}")
        raise HTTPException(status_code=500, detail="Databasefout bij het verzenden van chatbericht.")


@app.get("/chat/{match_id}/messages")
async def get_chat_messages(match_id: int, current_user: dict = Depends(get_current_user)):
    user_id = current_user['id']

    # Check if the user is part of the match
    c_pg.execute("""
        SELECT 1 FROM swipes WHERE
        (swiper_id = %s AND swipee_id = %s AND liked = 1) OR
        (swiper_id = %s AND swipee_id = %s AND liked = 1)
    """, (user_id, match_id, match_id, user_id))
    
    if not c_pg.fetchone():
        raise HTTPException(status_code=403, detail="U bent geen onderdeel van deze chat.")

    c_pg.execute("SELECT sender_id, encrypted_message, timestamp FROM chats WHERE match_id = %s ORDER BY timestamp", (match_id,))
    messages = c_pg.fetchall()
    
    decrypted_messages = []
    for sender_id, encrypted_msg, timestamp in messages:
        decrypted_msg = cipher_suite.decrypt(encrypted_msg.encode('utf-8')).decode('utf-8')
        decrypted_messages.append(ChatMessage(
            sender_id=sender_id,
            message=decrypted_msg,
            timestamp=timestamp
        ))
    
    logger.info(f"Chatgeschiedenis opgehaald voor match {match_id} door gebruiker {user_id}.")
    return {"messages": decrypted_messages}

@app.post("/report")
async def report_user(report_request: ReportRequest, current_user: dict = Depends(get_current_user)):
    reporter_id = current_user['id']
    reported_id = report_request.reported_id
    reason = report_request.reason
    timestamp = datetime.utcnow()

    if reporter_id == reported_id:
        raise HTTPException(status_code=400, detail="Je kunt jezelf niet rapporteren.")

    try:
        c_pg.execute("INSERT INTO user_reports (reporter_id, reported_id, reason, timestamp) VALUES (%s, %s, %s, %s)",
                     (reporter_id, reported_id, reason, timestamp))
        conn_pg.commit()
        logger.info(f"Gebruiker {reporter_id} heeft gebruiker {reported_id} gerapporteerd om de volgende reden: {reason}.")
        return {"status": "success", "message": "Gebruiker succesvol gerapporteerd."}
    except psycopg2.Error as e:
        conn_pg.rollback()
        logger.error(f"Databasefout bij het rapporteren van gebruiker {reported_id}: {e}")
        raise HTTPException(status_code=500, detail="Databasefout bij het rapporteren van de gebruiker.")

@app.post("/block")
async def block_user(block_data: dict, current_user: dict = Depends(get_current_user)):
    blocker_id = current_user['id']
    blocked_id = block_data.get("blocked_id")
    timestamp = datetime.utcnow()

    if blocker_id == blocked_id:
        raise HTTPException(status_code=400, detail="Je kunt jezelf niet blokkeren.")

    try:
        c_pg.execute("INSERT INTO user_blocks (blocker_id, blocked_id, timestamp) VALUES (%s, %s, %s) ON CONFLICT (blocker_id, blocked_id) DO NOTHING",
                     (blocker_id, blocked_id, timestamp))
        conn_pg.commit()
        logger.info(f"Gebruiker {blocker_id} heeft gebruiker {blocked_id} geblokkeerd.")
        return {"status": "success", "message": "Gebruiker succesvol geblokkeerd."}
    except psycopg2.Error as e:
        conn_pg.rollback()
        logger.error(f"Databasefout bij het blokkeren van gebruiker {blocked_id}: {e}")
        raise HTTPException(status_code=500, detail="Databasefout bij het blokkeren van de gebruiker.")
    
@app.post("/upload_photo")
async def upload_photo(photo: PhotoUpload, current_user: dict = Depends(get_current_user)):
    user_id = current_user['id']
    photo_url = str(photo.photo_url)
    is_profile_pic = photo.is_profile_pic

    try:
        # Handle profile picture logic
        if is_profile_pic:
            # Set all existing profile pictures for this user to is_profile_pic = 0
            c_pg.execute("UPDATE user_photos SET is_profile_pic = 0 WHERE user_id = %s AND is_profile_pic = 1", (user_id,))
            conn_pg.commit()

        c_pg.execute("INSERT INTO user_photos (user_id, photo_url, is_profile_pic) VALUES (%s, %s, %s)",
                     (user_id, photo_url, 1 if is_profile_pic else 0))
        conn_pg.commit()

        logger.info(f"Foto geüpload voor gebruiker {user_id}. URL: {photo_url}, Profielfoto: {is_profile_pic}")
        return {"status": "success", "message": "Foto succesvol geüpload."}
    except psycopg2.Error as e:
        conn_pg.rollback()
        logger.error(f"Databasefout bij het uploaden van foto voor gebruiker {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Databasefout bij het uploaden van foto.")

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Bericht ontvangen: {data}")
    except WebSocketDisconnect:
        print(f"Websocket met gebruiker {user_id} verbroken")

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

    logger.info(f"Chatbericht {chat_id} succesvol soft-verwijderd door gebruiker {user_id}.")
    return {"status": "success", "message": "Bericht succesvol verwijderd."}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
