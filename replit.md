# Sports Match App - Replit Configuration

## Overview

The Sports Match App (Athlo) is a **mobile-first social matching platform** designed to connect sports enthusiasts. Built with **React Native (Expo)** for the frontend and **FastAPI** for the backend, its primary purpose is to help users find sports partners based on location, preferences, and activity data from fitness platforms like Strava and Garmin. Key features include user authentication, profile management, swipe-based matching with **Year-To-Date (YTD) sports statistics** prominently displayed **twice** on discovery cards (gradient header + bio section), real-time messaging, and personalized route suggestions. The application supports **internationalization (i18n)** in **7 languages** (Dutch, English, French, German, Spanish, Italian, Portuguese), aiming to create a vibrant community for athletes worldwide.

## Recent Changes (November 24, 2025)

### YTD Sports Statistics Feature - Final Implementation
- **Dual display of YTD stats**: Statistics appear **TWICE** in discovery cards by design:
  1. **Primary display**: Gradient card (orange/yellow) as the FIRST element, replacing traditional photo-first layout
  2. **Secondary display**: Stats section beneath user bio for easy reference while scrolling
- **Three-metric display**: Each stats section shows:
  - Total workouts completed in 2025
  - Total distance covered (km)
  - Total active time (hours)
- **Intelligent fallback**: When `total_workouts === 0` or missing, both sections display localized "Stats coming soon" message with fitness icon
- **Photo placeholder**: Profiles without photos (e.g., Greta Hoffman) display person icon with "No photo available" message, preventing UI breakage
- **Full internationalization**: Stats labels and fallback messages localized across **7 languages** (nl, en, fr, de, es, it, pt) using translation keys:
  - `ytdStatsTitle`: "Sportgegevens 2025" (nl), "2025 Stats" (en), etc.
  - `ytdComingSoon`: Fallback message when stats unavailable
  - `workouts`, `distance`, `hours`: Metric labels with consistent unit formatting
- **Backend** (`/suggestions` endpoint) returns `ytd_stats` object with realistic sport-specific mock data:
  - CrossFit athlete (Greta): 156 workouts, 156km, 156h (strength-focused, minimal cardio distance)
  - Cyclist (Emma): 180 workouts, 7,200km, 240h (30 km/h average - competitive cyclist)
  - Marathon runner (Lucas): 260 workouts, 2,600km, 217h (12 km/h - 5 min/km pace)
  - Swimmer (Sophie): 208 workouts, 520km, 144h (3.6 km/h pool pace)
  - Triathlete (Mike): 312 workouts, 5,200km, 312h (16.7 km/h mixed-sport average)
  - Default/recreational: 52 workouts, 260km, 65h (4 km/h walking pace)
- **Discovery card layout** (top to bottom):
  1. YTD stats gradient card (or fallback)
  2. User info (name, age, bio, location)
  3. YTD stats section (or fallback)
  4. Photo (or placeholder)
  5. Swipe buttons (like/dislike)

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