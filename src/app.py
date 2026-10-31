"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi import Depends, Request, Response
from pydantic import BaseModel
import base64
import hmac
import json
import os
from pathlib import Path
import time

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

SESSION_COOKIE_NAME = "teacher_session"
SESSION_MAX_AGE = 8 * 60 * 60


class LoginRequest(BaseModel):
    username: str
    password: str


def _session_secret() -> bytes:
    return os.environ.get("SESSION_SECRET", "").encode()


def _teacher_credentials() -> tuple[str, str] | None:
    username = os.environ.get("TEACHER_USERNAME")
    password = os.environ.get("TEACHER_PASSWORD")
    if not username or not password or len(_session_secret()) < 32:
        return None
    return username, password


def _cookie_is_secure() -> bool:
    return os.environ.get("COOKIE_SECURE", "true").lower() != "false"


def _create_session_token(username: str) -> str:
    payload = json.dumps({
        "username": username,
        "expires": int(time.time()) + SESSION_MAX_AGE,
    }, separators=(",", ":")).encode()
    encoded_payload = base64.urlsafe_b64encode(payload).decode().rstrip("=")
    signature = hmac.new(
        _session_secret(), encoded_payload.encode(), "sha256"
    ).hexdigest()
    return f"{encoded_payload}.{signature}"


def _is_teacher_authenticated(request: Request) -> bool:
    credentials = _teacher_credentials()
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if credentials is None or token is None:
        return False

    try:
        encoded_payload, signature = token.split(".", 1)
        expected_signature = hmac.new(
            _session_secret(), encoded_payload.encode(), "sha256"
        ).hexdigest()
        if not hmac.compare_digest(signature, expected_signature):
            return False

        payload_bytes = base64.urlsafe_b64decode(
            encoded_payload + "=" * (-len(encoded_payload) % 4)
        )
        payload = json.loads(payload_bytes)
        return (
            isinstance(payload["username"], str)
            and hmac.compare_digest(
                payload["username"].encode(), credentials[0].encode()
            )
            and isinstance(payload["expires"], int)
            and payload["expires"] > int(time.time())
        )
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        return False


def require_teacher(request: Request) -> None:
    if not _is_teacher_authenticated(request):
        raise HTTPException(status_code=401, detail="Teacher login required")


# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


@app.get("/auth/status")
def get_auth_status(request: Request):
    return {"authenticated": _is_teacher_authenticated(request)}


@app.post("/auth/login")
def login(credentials: LoginRequest, response: Response):
    configured_credentials = _teacher_credentials()
    if configured_credentials is None:
        raise HTTPException(
            status_code=503,
            detail="Teacher authentication is not configured",
        )

    username_matches = hmac.compare_digest(
        credentials.username.encode(), configured_credentials[0].encode()
    )
    password_matches = hmac.compare_digest(
        credentials.password.encode(), configured_credentials[1].encode()
    )
    if not (username_matches and password_matches):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=_create_session_token(configured_credentials[0]),
        max_age=SESSION_MAX_AGE,
        httponly=True,
        secure=_cookie_is_secure(),
        samesite="strict",
        path="/",
    )
    return {"message": "Logged in"}


@app.post("/auth/logout")
def logout(response: Response):
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        httponly=True,
        secure=_cookie_is_secure(),
        samesite="strict",
        path="/",
    )
    return {"message": "Logged out"}


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(
    activity_name: str,
    email: str,
    _: None = Depends(require_teacher),
):
    """Sign up a student for an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(
    activity_name: str,
    email: str,
    _: None = Depends(require_teacher),
):
    """Unregister a student from an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}
