# Sports Match App - Replit Configuration

## Overview

The Sports Match App (Athlo) is a **mobile-first social matching platform** designed to connect sports enthusiasts. Built with **React Native (Expo)** for the frontend and **FastAPI** for the backend, its primary purpose is to help users find sports partners based on location, preferences, and activity data from fitness platforms like Strava and Garmin. Key features include user authentication, profile management, swipe-based matching with **Year-To-Date (YTD) sports statistics** prominently displayed **twice** on discovery cards (gradient header + bio section), real-time messaging, and personalized route suggestions. The application supports **internationalization (i18n)** in **7 languages** (Dutch, English, French, German, Spanish, Italian, Portuguese), aiming to create a vibrant community for athletes worldwide.

## Recent Changes (November 24, 2025)

### Interactive Sport-Specific Stats Feature - Final Implementation
- **Redesigned discovery card layout** for better UX flow (top to bottom):
  1. **Interactive gradient stats card** with sport selector
  2. **Swipeable photo gallery** with dots indicator
  3. **User information** (name, age, bio, location)
  4. **Swipe action buttons** (like/dislike)

- **Modern gradient stats card** with glassmorphism design:
  - **4-color gradients** unique to each sport type for visual differentiation
  - **Sport selector**: Horizontal scrollable selector with 6 sport types:
    - Alles (All) - shows overall YTD stats
    - Fietsen (Cycling) - blue gradient
    - Hardlopen (Running) - green gradient  
    - Zwemmen (Swimming) - cyan gradient
    - Triathlon - purple gradient
    - Gym/Fitness - orange gradient
  - **Dynamic stats display**: Stats change based on selected sport
  - **Sport-specific icons**: Trophy, bicycle, running, water, fitness icons
  - **Glassmorphism overlay**: Semi-transparent white overlay for modern look
  - **Modern typography**: Bold Montserrat font with text shadows

- **Swipeable photo gallery**:
  - Browse multiple photos per profile with left/right swipe gestures
  - Dots indicator shows current photo position
  - Photo index resets when changing profiles
  - Placeholder display for profiles without photos

- **Smart fallback logic**:
  - When selected sport has no data (0 workouts), automatically shows overall YTD stats
  - Stats card remains visible even when sport-specific data unavailable
  - Gradient/icon still reflect selected sport for consistency

- **Backend** (`/suggestions` endpoint) returns:
  - `ytd_stats`: Overall year-to-date statistics across all sports
  - `sport_stats`: Per-sport breakdown (cycling, running, swimming, triathlon, gym)
  - Realistic sport-specific data per profile:
    - Cyclist (Emma): 180 cycling workouts, 24 running workouts
    - Runner (Lucas): 260 running workouts, 104 gym workouts
    - Swimmer (Sophie): 208 swimming workouts, 52 running workouts
    - Triathlete (Mike): Balanced across swimming (104), cycling (104), running (104)
    - CrossFit (Greta): 156 gym workouts
  - `photos`: Array of photo URLs for swipeable gallery

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

An **SMTP-based email delivery system** is implemented, supporting multi-format (plain text + HTML) and internationalized email templates across four languages. It facilitates token-based email verification with configurable environment variables for SMTP credentials and frontend URLs.

## External Dependencies

### Third-Party Services

-   **Strava API**: Integrated for activity data fetching, workout location, and route suggestions. Uses OAuth tokens for secure access.
-   **Garmin Connect**: Planned integration for alternative fitness tracking.
-   **SMTP Server**: Used for email delivery for user verification and notifications.

### Database

-   **PostgreSQL**: The primary relational database used for all persistent data storage (users, matches, messages, settings).

### Environment Configuration

Key environment variables are required for database connection, JWT signing, frontend URL for email verification, SMTP server details, and Strava/Garmin API credentials.

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