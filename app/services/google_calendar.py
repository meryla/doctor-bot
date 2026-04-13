import os.path
from datetime import datetime, timedelta

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar"]
DEFAULT_TIMEZONE = "Europe/Brussels"


def get_calendar_service():
    creds = None

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json",
                SCOPES,
            )
            creds = flow.run_local_server(port=8080)

        with open("token.json", "w", encoding="utf-8") as token:
            token.write(creds.to_json())

    return build("calendar", "v3", credentials=creds)


def _normalize_datetime(value: str) -> str:
    value = value.strip()

    try:
        dt = datetime.fromisoformat(value)
        return dt.isoformat()
    except ValueError:
        pass

    try:
        dt = datetime.strptime(value, "%Y-%m-%d %H:%M")
        return dt.isoformat()
    except ValueError:
        raise ValueError(
            "Invalid datetime format. Use 'YYYY-MM-DDTHH:MM:SS' or 'YYYY-MM-DD HH:MM'."
        )


def add_event(
    title: str,
    start_time: str,
    end_time: str = None,
    description: str = "",
    location: str = "",
    timezone: str = DEFAULT_TIMEZONE,
):
    service = get_calendar_service()

    start_iso = _normalize_datetime(start_time)

    if end_time:
        end_iso = _normalize_datetime(end_time)
    else:
        start_dt = datetime.fromisoformat(start_iso)
        end_iso = (start_dt + timedelta(hours=1)).isoformat()

    event_body = {
        "summary": title,
        "description": description,
        "location": location,
        "start": {
            "dateTime": start_iso,
            "timeZone": timezone,
        },
        "end": {
            "dateTime": end_iso,
            "timeZone": timezone,
        },
    }

    created_event = (
        service.events()
        .insert(calendarId="primary", body=event_body)
        .execute()
    )

    return {
        "status": "success",
        "id": created_event.get("id"),
        "title": created_event.get("summary"),
        "start": created_event.get("start", {}).get("dateTime"),
        "end": created_event.get("end", {}).get("dateTime"),
        "link": created_event.get("htmlLink"),
    }


def get_events(max_results: int = 10, timezone: str = DEFAULT_TIMEZONE):
    service = get_calendar_service()

    now = datetime.utcnow().isoformat() + "Z"

    events_result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=now,
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime",
            timeZone=timezone,
        )
        .execute()
    )

    events = events_result.get("items", [])

    if not events:
        return {"status": "success", "events": []}

    cleaned = []
    for event in events:
        start = event.get("start", {}).get("dateTime") or event.get("start", {}).get("date")
        end = event.get("end", {}).get("dateTime") or event.get("end", {}).get("date")

        cleaned.append(
            {
                "id": event.get("id"),
                "title": event.get("summary", "No title"),
                "start": start,
                "end": end,
                "link": event.get("htmlLink"),
            }
        )

    return {"status": "success", "events": cleaned}