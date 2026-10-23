from datetime import date, datetime

from sqlalchemy import CheckConstraint, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True, index=True)
    hashed_password: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    habits: Mapped[list["Habit"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    conversations: Mapped[list["Conversation"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    meal_logs: Mapped[list["MealLog"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    calendar_credential: Mapped["CalendarCredential | None"] = relationship(
        back_populates="user", cascade="all, delete-orphan", uselist=False
    )


class Habit(Base):
    __tablename__ = "habits"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    category: Mapped[str] = mapped_column(default="General")
    name: Mapped[str]
    kind: Mapped[str]  # "check" or "number" -- enforced below
    unit: Mapped[str | None] = mapped_column(default=None)
    goal_num: Mapped[float | None] = mapped_column(default=None)

    user: Mapped["User"] = relationship(back_populates="habits")
    entries: Mapped[list["Entry"]] = relationship(back_populates="habit", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("kind IN ('check', 'number')", name="ck_habits_kind"),
    )


class Entry(Base):
    __tablename__ = "entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    habit_id: Mapped[int] = mapped_column(ForeignKey("habits.id"), index=True)

    day: Mapped[date]
    value_num: Mapped[float | None] = mapped_column(default=None)
    value_check: Mapped[bool | None] = mapped_column(default=None)
    note: Mapped[str | None] = mapped_column(default=None)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    habit: Mapped["Habit"] = relationship(back_populates="entries")

    __table_args__ = (
        UniqueConstraint("habit_id", "day", name="uq_entries_habit_day"),
    )


class MealLog(Base):
    __tablename__ = "meal_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    day: Mapped[date]
    image_path: Mapped[str | None] = mapped_column(default=None)

    predicted_label: Mapped[str | None] = mapped_column(default=None)
    confidence: Mapped[float | None] = mapped_column(default=None)

    portion_grams: Mapped[float | None] = mapped_column(default=None)
    calories: Mapped[float | None] = mapped_column(default=None)
    protein_g: Mapped[float | None] = mapped_column(default=None)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="meal_logs")


class CalendarCredential(Base):
    __tablename__ = "calendar_credentials"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True)

    access_token: Mapped[str]
    refresh_token: Mapped[str]
    token_expiry: Mapped[datetime]

    user: Mapped["User"] = relationship(back_populates="calendar_credential")


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="conversations")
    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"), index=True)

    role: Mapped[str]  # "user" | "assistant" | "tool" | "system"
    content: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")

    __table_args__ = (
        CheckConstraint("role IN ('user', 'assistant', 'tool', 'system')", name="ck_messages_role"),
    )