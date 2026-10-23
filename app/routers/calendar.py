import secrets

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.models import CalendarCredential, User
from app.db.session import get_db
from app.services.google_calendar import (
    add_event,
    exchange_code_for_credentials,
    get_authorization_url,
    get_events,
    save_credentials_for_user,
)

router = APIRouter(prefix="/calendar", tags=["calendar"])

# In-memory state store for the OAuth "state" CSRF check.
# Fine for a single-process dev setup; once Celery/Docker multi-worker
# is in place, this should move to Redis instead so all workers share it.
_pending_states: dict[str, int] = {}


class EventCreate(BaseModel):
    title: str
    start_time: str
    end_time: str | None = None
    description: str = ""
    location: str = ""


@router.get("/oauth/login")
async def oauth_login(current_user: User = Depends(get_current_user)):
    """
    Step 1: the logged-in user hits this route, we generate a random
    state tied to THEIR user_id, and redirect their browser to Google's
    consent screen.
    """
    state = secrets.token_urlsafe(32)
    _pending_states[state] = current_user.id
    return RedirectResponse(get_authorization_url(state))


@router.get("/oauth/callback")
async def oauth_callback(code: str, state: str, db: AsyncSession = Depends(get_db)):
    """
    Step 2: Google redirects the browser back here with a one-time code.
    We check `state` matches something WE generated (prevents another
    site from tricking a user into linking the wrong account), then
    exchange the code for real tokens and save them for that user.
    """
    user_id = _pending_states.pop(state, None)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired OAuth state")

    creds = exchange_code_for_credentials(code)
    await save_credentials_for_user(db, user_id, creds)
    return {"status": "success", "message": "Google Calendar connected"}


async def _get_credential_or_400(db: AsyncSession, user_id: int) -> CalendarCredential:
    record = await db.get(CalendarCredential, user_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google Calendar not connected yet -- visit /calendar/oauth/login first",
        )
    return record


@router.post("/events")
async def create_event(
    payload: EventCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    record = await _get_credential_or_400(db, current_user.id)
    return add_event(
        record,
        title=payload.title,
        start_time=payload.start_time,
        end_time=payload.end_time,
        description=payload.description,
        location=payload.location,
    )


@router.get("/events")
async def list_events(
    max_results: int = Query(default=10, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    record = await _get_credential_or_400(db, current_user.id)
    return get_events(record, max_results=max_results)