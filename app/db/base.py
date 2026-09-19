from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Every SQLAlchemy model in the app inherits from this.
    Alembic will point at Base.metadata to know what tables should exist.
    """
    pass