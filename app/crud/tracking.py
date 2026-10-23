from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Entry, Habit


async def create_habit(db: AsyncSession, user_id: int, data) -> Habit:
    habit = Habit(user_id=user_id, **data.model_dump())
    db.add(habit)
    await db.commit()
    await db.refresh(habit)
    return habit


async def get_habits_for_user(db: AsyncSession, user_id: int) -> list[Habit]:
    result = await db.execute(select(Habit).where(Habit.user_id == user_id))
    return list(result.scalars().all())


async def get_habit_owned_by_user(db: AsyncSession, user_id: int, habit_id: int) -> Habit | None:
    """
    THE key security check for this whole file: fetches a habit only if
    it belongs to this exact user. Every other function below calls this
    first -- if it returns None, the caller must refuse the request,
    even if the habit_id itself is valid for a DIFFERENT user.
    """
    result = await db.execute(
        select(Habit).where(Habit.id == habit_id, Habit.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def upsert_entry(db: AsyncSession, habit_id: int, day: date, value_num, value_check, note) -> Entry:
    result = await db.execute(
        select(Entry).where(Entry.habit_id == habit_id, Entry.day == day)
    )
    entry = result.scalar_one_or_none()

    if entry is None:
        entry = Entry(habit_id=habit_id, day=day, value_num=value_num, value_check=value_check, note=note)
        db.add(entry)
    else:
        entry.value_num = value_num
        entry.value_check = value_check
        entry.note = note

    await db.commit()
    await db.refresh(entry)
    return entry


async def get_entries_for_user(db: AsyncSession, user_id: int, start_day: date, end_day: date) -> list[Entry]:
    result = await db.execute(
        select(Entry)
        .join(Habit, Entry.habit_id == Habit.id)
        .where(Habit.user_id == user_id, Entry.day >= start_day, Entry.day <= end_day)
    )
    return list(result.scalars().all())