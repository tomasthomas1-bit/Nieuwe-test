# Sports Match App - Replit Configuration

## Overview

The Sports Match App (Athlo) is a **mobile-first social matching platform** designed to connect sports enthusiasts. Built with **React Native (Expo)** for the frontend and **FastAPI** for the backend, its primary purpose is to help users find sports partners based on location, preferences, and activity data from fitness platforms like Strava and Garmin. Key features include user authentication, profile management, swipe-based matching with **Year-To-Date (YTD) sports statistics** prominently displayed **twice** on discovery cards (gradient header + bio section), real-time messaging, and personalized route suggestions. The application supports **internationalization (i18n)** in **7 languages** (Dutch, English, French, German, Spanish, Italian, Portuguese), aiming to create a vibrant community for athletes worldwide.

## Recent Changes (November 25, 2025)

### Complete Onboarding Flow Implementation
- **VerificationPendingScreen**: New screen shown after registration with resend verification email option
- **ProfileSetupScreen**: First-time user setup with photo upload, sports selection (running, cycling, swimming, fitness, other), and location detection
- **Navigation Flow**: AuthScreen → VerificationPending → Login → ProfileSetup (if needed) → MainTabs
- **Backend Updates**:
  - Added `profile_setup_complete` (BOOLEAN) and `sports_interests` (TEXT[]) columns to users table
  - Extended `get_current_user`, `/me` endpoint, and `PATCH /users` to support new fields
  - Added `parse_pg_array()` helper for safe PostgreSQL array handling
  - Extended `UserPublic` and `UserUpdate` Pydantic models
- **Translations**: Added all onboarding screen translations in 7 languages (NL, EN, FR, DE, ES, IT, PT)

### Email Verification & Password Reset - Resend Integration
- **Resend API Integration**: Replaced SMTP with Resend for reliable email delivery
- **Fixed Email Verification**: 
  - Updated `/register` endpoint to send verification emails to user's actual email address (was incorrectly using username)
  - Updated `/resend-verification` endpoint to fetch and use email from database
  - Added email validation error handling for users without email addresses
- **Password Reset Flow**: Already working correctly, now uses Resend API
- **All 7 Languages Supported**: 
  - Added translations for all missing error messages (NL, EN, FR, DE, ES, IT, PT)
  - New error: `no_email_address` for when user tries to resend verification without email on file
- **Frontend Translations**: 
  - Added missing translations to App.js for all 6 remaining languages (DE, ES, IT, PT, FR, EN already had some)
  - `forgotPassword`, `enterEmail`, `sendResetLink`, `backToLogin`, `resetLinkSent`

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture (React Native + Expo)

The frontend is developed using **React Native 0.80.2** with **Expo 54.0.21** for cross-platform compatibility (iOS, Android, Web). It utilizes **React Navigation** for navigation, **Expo Vector Icons (Ionicons)** for iconography, and **Expo Google Fonts (Montserrat)** for typography. A custom **Theme System** (`ThemeContext`) supports multiple presets and automatic dark mode detection, enhancing UI/UX. **Gesture Handling** via `react-native-gesture-handler` powers the swipe-based matching interface, while **Expo Secure Store** is used for secure JWT token storage, ensuring robust authentication.

### Backend Architecture (FastAPI + Python)

The backend is built with **FastAPI**, a modern async Python web framework, providing a **RESTful API**. It uses **PostgreSQL** with `psycopg2` for data persistence, managed with connection pooling. **JWT (python-jose)** handles authentication, with **bcrypt** for secure password hashing. **Pydantic** is used for request/response validation and serialization. Core architectural patterns include JWT Authentication (OAuth2PasswordBearer), token-based email verification, and a server-side internationalization system. Security measures include password hashing, JWT token expiration, and CORS middleware.

### Data Architecture

The **PostgreSQL** database schema includes tables for `Users` (credentials, profile info, location, verification), `Matches`, `Messages`, `User Settings` (sports interests, location visibility, fitness platform tokens), `Photos`, and `Reports/Blocks`. **Pydantic** models define data structures and validation. **Location-based matching** uses the `haversine` library for distance calculations, supporting configurable max distances and integration with Strava/Garmin location data.

### Email System

An **Resend API-based email delivery system** is implemented, supporting multi-format (plain text + HTML) and internationalized email templates across seven languages. It facilitates token-based email verification with configurable environment variables and Resend API key for secure email delivery.

**Email Configuration:**
- Sender: `noreply@athlo.be` (verified domain in Resend)
- Supports: Email verification + Password reset
- Languages: NL, EN, FR, DE, ES, IT, PT

## External Dependencies

### Third-Party Services

-   **Strava API**: Integrated for activity data fetching, workout location, and route suggestions. Uses OAuth tokens for secure access.
-   **Garmin Connect**: Planned integration for alternative fitness tracking.
-   **Resend API**: Used for reliable email delivery for user verification and password reset notifications.

### Database

-   **PostgreSQL**: The primary relational database used for all persistent data storage (users, matches, messages, settings).

### Environment Configuration

Key environment variables/secrets are required for:
- Database connection (DATABASE_URL, PGHOST, PGPORT, PGUSER, PGPASSWORD, PGDATABASE)
- JWT signing (SECRET_KEY, ENCRYPTION_KEY)
- Frontend URL for email verification links (FRONTEND_URL)
- Strava OAuth (STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET)
- Resend API (RESEND_API_KEY) - for email delivery

### Frontend Dependencies

-   **Expo SDK**: Provides core native functionalities.
-   **React Navigation**: Handles application navigation.
-   **Gesture Handler**: Powers touch interactions for swipe gestures.
-   **Vector Icons**: Provides a comprehensive icon set.
-   **react-native-web**: Enables web deployment of the React Native codebase.

### Development Tools

-   **Ruff**: Python linting and formatting.
-   **Pytest**: Testing framework for the backend.
-   **Uvicorn**: ASGI server for running FastAPI applications.
