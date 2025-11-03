# Sports Match App - Replit Configuration

## Overview

The Sports Match App (Athlo) is a **mobile-first social matching platform** designed to connect sports enthusiasts. Built with **React Native (Expo)** for the frontend and **FastAPI** for the backend, its primary purpose is to help users find sports partners based on location, preferences, and activity data from fitness platforms like Strava and Garmin. Key features include user authentication, profile management, swipe-based matching, real-time messaging, and personalized route suggestions. The application supports **internationalization (i18n)** in Dutch, English, French, and German, aiming to create a vibrant community for athletes worldwide.

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