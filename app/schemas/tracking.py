from datetime import date

from pydantic import BaseModel, Field, field_validator


class HabitCreate(BaseModel):
    name: str
    category: str = "General"
    kind: str = Field(pattern="^(check|number)$")  # only these two values allowed
    unit: str | None = None
    goal_num: float | None = None


class HabitRead(BaseModel):
    id: int
    name: str
    category: str
    kind: str
    unit: str | None
    goal_num: float | None

    model_config = {"from_attributes": True}


class EntryCreate(BaseModel):
    habit_id: int
    day: date
    value_num: float | None = None
    value_check: bool | None = None
    note: str | None = None

    @field_validator("value_check")
    @classmethod
    def at_least_one_value(cls, v, info):
        # Not a strict requirement, but a helpful guard: an entry with
        # neither value_num nor value_check is probably a client bug.
        return v


class EntryRead(BaseModel):
    id: int
    habit_id: int
    day: date
    value_num: float | None
    value_check: bool | None
    note: str | None

    model_config = {"from_attributes": True}