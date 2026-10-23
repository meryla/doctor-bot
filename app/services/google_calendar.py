from datetime import datetime, timedelta, timezone

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.models import CalendarCredential

settings = get_settings()
SCOPES = ["https://www.googleapis.com/auth/calendar"]
DEFAULT_TIMEZONE = "Europe/Brussels"


def _build_flow() -> Flow:
    """
    Builds the OAuth2 'Flow' object using OUR app's client id/secret
    (from Google Cloud Console, stored in .env) -- NOT the old
    InstalledAppFlow, which only worked for one person on one machine.
    """
    client_config = {
        "web": {
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [settings.google_redirect_uri],
        }
    }
    return Flow.from_client_config(client_config, scopes=SCOPES, redirect_uri=settings.google_redirect_uri)


def get_authorization_url(state: str) -> str:
    """
    Step 1 of the web OAuth flow: build the URL we send the user's
    BROWSER to, where THEY log into Google and approve access.
    `state` is a random per-request token we generate to prevent
    CSRF -- we check it matches when Google redirects back.
    """
    flow = _build_flow()
    auth_url, _ = flow.authorization_url(
        access_type="offline",  # "offline" is what gets us a refresh_token, not just a short-lived access_token
        include_granted_scopes="true",
        prompt="consent",
        state=state,
    )
    return auth_url


def exchange_code_for_credentials(code: str) -> Credentials:
    """
    Step 2: Google redirects the user's browser back to OUR callback
    URL with a one-time `code`. We exchange that code (server-to-server,
    never exposed to the browser again) for real access + refresh tokens.
    """
    flow = _build_flow()
    flow.fetch_token(code=code)
    return flow.credentials


async def save_credentials_for_user(db: AsyncSession, user_id: int, creds: Credentials) -> CalendarCredential:
    """
    Stores this user's tokens in OUR database, tied to their user_id --
    this is what replaces the single shared token.json file. Each user
    gets their own row.
    """
    existing = await db.get(CalendarCredential, user_id)  # note: works because user_id happens to be unique-indexed
    if existing is None:
        record = CalendarCredential(
            user_id=user_id,
            access_token=creds.token,
            refresh_token=creds.refresh_token,
            token_expiry=creds.expiry or (datetime.now(timezone.utc) + timedelta(hours=1)),
        )
        db.add(record)
    else:
        existing.access_token = creds.token
        existing.refresh_token = creds.refresh_token
        existing.token_expiry = creds.expiry or (datetime.now(timezone.utc) + timedelta(hours=1))
        record = existing

    await db.commit()
    await db.refresh(record)
    return record


def _credentials_from_record(record: CalendarCredential) -> Credentials:
    """Rebuilds a google Credentials object from what we stored in our DB."""
    creds = Credentials(
        token=record.access_token,
        refresh_token=record.refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        scopes=SCOPES,
    )

    # If the stored access_token has expired, use the refresh_token to
    # silently get a new one -- this is exactly what refresh_token is for,
    # and it's why we requested access_type="offline" earlier.
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())

    return creds


def add_event(record: CalendarCredential, title: str, start_time: str, end_time: str | None = None,
              description: str = "", location: str = "", timezone_name: str = DEFAULT_TIMEZONE) -> dict:
    creds = _credentials_from_record(record)
    service = build("calendar", "v3", credentials=creds)

    start_dt = datetime.fromisoformat(start_time)
    end_dt = datetime.fromisoformat(end_time) if end_time else start_dt + timedelta(hours=1)

    event_body = {
        "summary": title,
        "description": description,
        "location": location,
        "start": {"dateTime": start_dt.isoformat(), "timeZone": timezone_name},
        "end": {"dateTime": end_dt.isoformat(), "timeZone": timezone_name},
    }

    created = service.events().insert(calendarId="primary", body=event_body).execute()
    return {
        "id": created.get("id"),
        "title": created.get("summary"),
        "start": created.get("start", {}).get("dateTime"),
        "end": created.get("end", {}).get("dateTime"),
        "link": created.get("htmlLink"),
    }


def get_events(record: CalendarCredential, max_results: int = 10, timezone_name: str = DEFAULT_TIMEZONE) -> list[dict]:
    creds = _credentials_from_record(record)
    service = build("calendar", "v3", credentials=creds)

    now = datetime.now(timezone.utc).isoformat()
    result = service.events().list(
        calendarId="primary", timeMin=now, maxResults=max_results,
        singleEvents=True, orderBy="startTime", timeZone=timezone_name,
    ).execute()

    events = []
    for event in result.get("items", []):
        events.append({
            "id": event.get("id"),
            "title": event.get("summary", "No title"),
            "start": event.get("start", {}).get("dateTime") or event.get("start", {}).get("date"),
            "end": event.get("end", {}).get("dateTime") or event.get("end", {}).get("date"),
            "link": event.get("htmlLink"),
        })
    return events