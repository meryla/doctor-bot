from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.crud.tracking import (
    create_habit,
    get_entries_for_user,
    get_habit_owned_by_user,
    get_habits_for_user,
    upsert_entry,
)
from app.db.models import User
from app.db.session import get_db
from app.schemas.tracking import EntryCreate, EntryRead, HabitCreate, HabitRead

router = APIRouter(prefix="/tracking", tags=["tracking"])


@router.post("/habits", response_model=HabitRead, status_code=status.HTTP_201_CREATED)
async def add_habit(
    payload: HabitCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await create_habit(db, current_user.id, payload)


@router.get("/habits", response_model=list[HabitRead])
async def list_habits(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_habits_for_user(db, current_user.id)


@router.post("/entries", response_model=EntryRead, status_code=status.HTTP_201_CREATED)
async def add_entry(
    payload: EntryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # THIS is the line that actually enforces "you can only log entries
    # against YOUR OWN habits" -- without it, any logged-in user could
    # write entries onto any habit_id, including someone else's.
    habit = await get_habit_owned_by_user(db, current_user.id, payload.habit_id)
    if habit is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Habit not found")

    return await upsert_entry(
        db,
        habit_id=payload.habit_id,
        day=payload.day,
        value_num=payload.value_num,
        value_check=payload.value_check,
        note=payload.note,
    )


@router.get("/entries", response_model=list[EntryRead])
async def list_entries(
    start: date,
    end: date,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_entries_for_user(db, current_user.id, start, end)