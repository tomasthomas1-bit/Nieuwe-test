# Sports Match App - Replit Configuration

## Overview

Sports Match App (Athlo) is a **mobile-first social matching platform** built with **React Native (Expo)** for the frontend and **FastAPI** for the backend. The application enables users to find sports partners based on location, preferences, and activity data from fitness platforms like Strava and Garmin. Core features include user authentication, profile management, swipe-based matching, real-time messaging, and route suggestions based on workout data.

The app supports **internationalization (i18n)** with translations for Dutch (nl), English (en), French (fr), and German (de).

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture (React Native + Expo)

**Technology Stack:**
- **React Native 0.80.2** with **Expo 54.0.21** for cross-platform mobile development (iOS, Android, Web)
- **React Navigation** (Native Stack + Bottom Tabs) for navigation flows
- **Expo Vector Icons (Ionicons)** for iconography
- **Expo Linear Gradient** for visual polish
- **Expo Secure Store** for secure token storage
- **Expo Google Fonts (Montserrat)** for typography

**Design Decisions:**
- **Theme System**: Custom theme context (`ThemeContext`) supporting multiple presets (iOS-style, WhatsApp-style) with automatic dark mode detection
- **Gesture Handling**: Uses `react-native-gesture-handler` for swipe interactions (matching interface)
- **Secure Authentication**: JWT tokens stored in Expo SecureStore for platform-specific secure storage
- **Responsive UI**: Adaptive layouts using React Native's responsive components and color scheme detection

**Rationale**: Expo provides rapid development with native capabilities while maintaining cross-platform compatibility. The theme system allows users to customize their experience while respecting system preferences.

### Backend Architecture (FastAPI + Python)

**Technology Stack:**
- **FastAPI** - Modern async Python web framework for RESTful APIs
- **PostgreSQL** with **psycopg2** - Relational database with connection pooling (ThreadedConnectionPool)
- **JWT (python-jose)** - Token-based authentication
- **bcrypt** - Password hashing
- **Pydantic** - Request/response validation and serialization
- **Cryptography (Fernet)** - Symmetric encryption for sensitive data

**Core Architectural Patterns:**
- **RESTful API Design**: Resource-based endpoints with proper HTTP methods
- **JWT Authentication**: OAuth2PasswordBearer flow with secure token generation
- **Connection Pooling**: ThreadedConnectionPool for efficient database connection management
- **Email Verification Flow**: Token-based email verification with HTML templates
- **Internationalization**: Server-side translation system (`translations.py`) matching user language preferences

**Key Endpoints:**
- Authentication: `/login`, `/register`, `/verify-email`
- User Management: `/users/{user_id}`, `/users/{user_id}/settings`
- Matching: Swipe-based matching logic, match management
- Messaging: Real-time chat between matched users
- Reporting: User reporting and blocking functionality

**Security Measures:**
- Password hashing with bcrypt
- JWT token expiration
- Secure token storage for email verification
- CORS middleware for controlled frontend access
- Input validation via Pydantic models

**Rationale**: FastAPI offers excellent performance for async operations, automatic OpenAPI documentation, and native Pydantic integration. PostgreSQL provides robust relational data storage for user profiles, matches, and messages.

### Data Architecture

**Database Schema (PostgreSQL):**
- **Users Table**: Core user data including credentials, profile information (name, age, bio), verification status, location data
- **Matches Table**: Swipe interactions and mutual matches
- **Messages Table**: Chat history between matched users
- **User Settings**: Preferences including sports interests, location visibility, messaging permissions, fitness platform tokens, matching criteria (goals, gender preferences, max distance)
- **Photos Table**: User profile photos with references
- **Reports/Blocks**: User safety features

**Data Models (Pydantic):**
- `UserPublic`: Public-facing user profile with age constraints (18-99)
- `UserUpdate`: Validated profile update schema
- `UserSettings`: Comprehensive user preference model with enums for message preferences, match goals, and gender preferences

**Location-Based Matching:**
- Uses **haversine** library for distance calculations between users
- Configurable max distance preference (default 50km)
- Support for Strava/Garmin location data integration

### Email System

**Architecture:**
- SMTP-based email delivery with SSL/TLS
- Multi-format emails: Plain text + HTML with responsive design
- Template system supporting 4 languages (nl, en, fr, de)
- Token-based verification links pointing to frontend URL

**Email Templates:**
- `email_templates.py`: HTML email rendering with internationalization
- `email_utils.py`: SMTP sending logic, token generation, plain text rendering
- Configurable via environment variables (`FRONTEND_URL`, SMTP credentials)

## External Dependencies

### Third-Party Services

**Fitness Platform Integrations:**
- **Strava API**: Activity data fetching, route suggestions based on workout locations
- **Garmin Connect**: Alternative fitness tracking integration
- Both use OAuth tokens stored in user settings

**Email Service:**
- **SMTP Server**: Email delivery for verification and notifications
- Configuration: Environment variables for SMTP host, port, credentials

### Database

**PostgreSQL:**
- Primary relational data store
- Connection managed via psycopg2 with connection pooling
- Required for user data, matches, messages, settings persistence

### Environment Configuration

**Required Environment Variables:**
- `DATABASE_URL` / PostgreSQL connection details
- `SECRET_KEY`: JWT signing key
- `FRONTEND_URL`: Base URL for email verification links
- `SMTP_*`: Email server configuration (host, port, username, password)
- `STRAVA_CLIENT_ID`, `STRAVA_CLIENT_SECRET`: Strava OAuth
- `GARMIN_*`: Garmin integration credentials

### Frontend Dependencies

**React Native Ecosystem:**
- **Expo SDK**: Core native functionality (secure storage, fonts, linear gradients)
- **React Navigation**: Navigation library with stack and tab navigators
- **Gesture Handler**: Touch interaction library for swipe mechanics
- **Vector Icons**: Icon library from Expo

**Web Compatibility:**
- `react-native-web`: Enables web deployment of React Native codebase
- Metro bundler for web builds

### Development Tools

**Backend:**
- **Ruff 0.6.9**: Python linting and formatting
- **Pytest**: Testing framework
- **Uvicorn**: ASGI server for FastAPI

**Deployment:**
- Backend deployed on **Replit** (port 8000) - publicly accessible at https://97bfdb52-3064-4532-9a91-48fd1291b1af-00-2t59ltt1vcb8u.riker.replit.dev:8000
- Frontend tested via **Expo Snack** (https://snack.expo.dev/@tomas.thomas1/07cfa1)
- Frontend also deployable via Expo build services or web hosting

## Recent Changes (November 3, 2025)

### Critical Backend Fixes

1. **Database Connection Pooling Fix** (main.py):
   - Added automatic stale connection detection and recovery in `DB.__enter__` method
   - Prevents "SSL connection has been closed unexpectedly" errors
   - Ensures stable API responses without 500 errors

2. **Expo Snack Compatibility Fix** (main.py):
   - Removed `WWW-Authenticate: Bearer` headers from 401 responses
   - Fixes iOS/Expo issue where requests with this header hang indefinitely
   - Affected endpoints: `/token` (login) and `get_current_user` dependency
   - Now Expo Snack can successfully connect and authenticate

3. **CORS Configuration Fix** (main.py):
   - Fixed missing CORS headers by setting `allow_origins=["*"]` for Expo Snack compatibility
   - Removed conditional CORS logic that was causing missing `Access-Control-Allow-Origin` headers
   - All API responses now include proper CORS headers for cross-origin requests

4. **Test User Created**:
   - Username: `testuser`
   - Password: `test123`
   - Ready for testing authentication flow

### Tinder-Style Swipe Interface (App.js)

**Complete Redesign - Single Card Layout:**
Replaced 2-column grid with Tinder-style single-card interface:

**UI Components:**
1. **Header Section**:
   - Profile avatar (top left) showing user's profile photo
   - Athlo logo with stylized heart icon (blue/green gradient) in center
   - "athlo" text in white with "Find your fit." tagline in green
   - Match counter badge (top right) showing number of matches with orange heart icon

2. **Stats Dashboard**:
   - Three-column stat display: Workouts, Distance (km), Hours
   - Separated by vertical dividers for clean layout

3. **Single Profile Card**:
   - Full-width card showing ONE user at a time
   - Large profile photo (400px height)
   - User info: name, age, distance, location
   - Bio text display
   - Like/Dislike buttons below card

**Swipe Flow Implementation:**
- Uses `useRef` hooks to avoid closure/stale state issues
- `suggestionsRef` and `currentIndexRef` synced with state via useEffect
- Mutual exclusion prevents race conditions:
  - `doSwipe` checks `if (swiping || loading) return`
  - `load` checks `if (swiping || loading) return []`
- Clearing `swiping` before calling `load()` prevents soft-lock at end of deck
- When user reaches end of suggestions, new batch loads automatically

**Technical Implementation:**
- Added `user` prop to DiscoverScreen to display current user's profile photo
- `doSwipe` callback handles Like/Dislike interactions
- Refs prevent stale closures in async operations
- Buttons disabled during loading/swiping states
- Comprehensive dark-theme styles for all components

**Race Condition Protection:**
- Fixed soft-lock issue by clearing `swiping` state before calling `load()`
- Mutual exclusion ensures load() and doSwipe() never run concurrently
- At end of deck: clears swiping → calls load() → fetches fresh suggestions
- On normal swipe: advances index → clears swiping
- On error: shows alert → clears swiping

**Design Rationale:**
- Single-card Tinder-style interface provides focused user experience
- Large profile photos showcase user's fitness activities
- Like/Dislike buttons provide clear, simple interaction
- Stats dashboard shows user's activity at a glance
- Dark theme with vibrant accent colors (blue, green, orange) creates energetic feel

### Static File Serving (main.py)

**Profile Photos & Images:**
- Added FastAPI StaticFiles mount at `/static` endpoint
- Serves images from `attached_assets/stock_images/` directory
- Images accessible via: `https://backend-url/static/<filename>.jpg`
- CORS configured to allow Expo Snack to fetch images
- 20 stock sports/fitness photos added for test users

**Implementation:**
- Imported `StaticFiles` from `fastapi.staticfiles`
- Mounted static directory after CORS middleware
- Directory path resolved using `os.path.join` for Replit compatibility
- Automatic logging on successful mount or missing directory warning

### Test Users & Data

**10 Test Users Created:**
All users have password: `Test123!`

| Username | Name | Age | Sport | Profile Photos |
|----------|------|-----|-------|----------------|
| sofia27 | Sofia | 27 | Running & Cycling | 2 photos |
| marco_athlete | Marco | 32 | CrossFit | 2 photos |
| emma_yoga | Emma | 24 | Yoga & Hiking | 2 photos |
| lucas_bike | Lucas | 29 | Mountain Biking | 2 photos |
| nina_swim | Nina | 26 | Triathlon | 2 photos |
| david_tennis | David | 35 | Tennis | 2 photos |
| lisa_climb | Lisa | 28 | Rock Climbing | 2 photos |
| alex_soccer | Alex | 30 | Soccer | 2 photos |
| mia_fitness | Mia | 23 | Fitness Coaching | 2 photos |
| ryan_runner | Ryan | 31 | Marathon Running | 2 photos |

**Photo Details:**
- Each user has 1 profile picture (is_profile_pic=1) + 1 additional photo
- All photos are sport/activity-specific stock images
- Images served via `/static` endpoint from backend
- Photos display correctly in suggestions and user profiles

### Configuration

**Backend URL for External Clients:**
```
https://97bfdb52-3064-4532-9a91-48fd1291b1af-00-2t59ltt1vcb8u.riker.replit.dev:8000
```

**Static Images URL Pattern:**
```
https://97bfdb52-3064-4532-9a91-48fd1291b1af-00-2t59ltt1vcb8u.riker.replit.dev:8000/static/<filename>.jpg
```

**Expo Snack Configuration:**
In App.js, set:
```javascript
const BASE_URL = 'https://97bfdb52-3064-4532-9a91-48fd1291b1af-00-2t59ltt1vcb8u.riker.replit.dev:8000';
```