from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """What the client must send to register."""
    email: EmailStr
    password: str = Field(min_length=8)


class UserLogin(BaseModel):
    """What the client must send to log in."""
    email: EmailStr
    password: str


class UserRead(BaseModel):
    """What we send back about a user -- notice: no password field, ever."""
    id: int
    email: EmailStr

    model_config = {"from_attributes": True}  # lets us build this directly from a SQLAlchemy User object


class Token(BaseModel):
    """What we send back after a successful login."""
    access_token: str
    token_type: str = "bearer"