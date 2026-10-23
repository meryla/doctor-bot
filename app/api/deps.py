from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.crud.user import get_user_by_email
from app.db.models import User
from app.db.session import get_db

# tokenUrl is just documentation for FastAPI's auto-generated /docs page --
# it tells the "Authorize" button in Swagger where login happens.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Use this as a dependency on any route that should require login:

        @router.get("/something")
        async def something(user: User = Depends(get_current_user)):
            ...

    FastAPI automatically reads the "Authorization: Bearer <token>" header,
    passes it in as `token`, and this function does the rest.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    email = decode_access_token(token)
    if email is None:
        raise credentials_exception

    user = await get_user_by_email(db, email)
    if user is None:
        raise credentials_exception

    return user