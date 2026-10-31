# Mergington High School Activities API

A FastAPI application that allows students to view extracurricular activities and teachers to manage signups.

## Features

- View all available extracurricular activities
- Teacher-only signup and unregistration, protected by a signed session cookie
- Public viewing of activity participants

## Getting Started

1. Install the dependencies:

   ```
   pip install -r requirements.txt
   ```

2. Configure a teacher account and a secret of at least 32 characters used to sign session cookies:

   ```
   export TEACHER_USERNAME=teacher
   export TEACHER_PASSWORD='choose-a-strong-password'
   export SESSION_SECRET="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
   ```

   For local HTTP development, also run `export COOKIE_SECURE=false`. Keep these values in a deployment secret store; do not commit credentials.

3. Run the application:

   ```
   uvicorn app:app --app-dir src --reload
   ```

4. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                              | Description                                              |
| ------ | --------------------------------------------------------------------- | -------------------------------------------------------- |
| GET    | `/activities`                                                         | Get all activities, details, and registered participants |
| GET    | `/auth/status`                                                        | Check whether the current browser has a teacher session  |
| POST   | `/auth/login`                                                         | Sign in with `{"username": "...", "password": "..."}`      |
| POST   | `/auth/logout`                                                        | Clear the current teacher session                       |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu`     | (Teacher only) Sign up a student for an activity         |
| DELETE | `/activities/{activity_name}/unregister?email=student@mergington.edu` | (Teacher only) Unregister a student                  |

Teacher sessions expire after eight hours. The session cookie is HTTP-only and SameSite strict; secure cookies are enabled by default. Set `COOKIE_SECURE=false` only for local HTTP development.

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

All data is stored in memory, which means data will be reset when the server restarts.
