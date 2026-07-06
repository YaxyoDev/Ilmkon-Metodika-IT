"""Ma'lumotlar bazasi: async engine, sessiya va Base.

DATABASE_URL .env faylidan olinadi. Misollar:
  dev (SQLite):      sqlite+aiosqlite:///./metodika.db
  prod (PostgreSQL): postgresql+asyncpg://user:parol@localhost:5432/metodikait
"""

import os

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./metodika.db")

engine = create_async_engine(DATABASE_URL, echo=False)

# SQLite'da FK qoidalari (CASCADE/RESTRICT/SET NULL) sukut bo'yicha o'chiq —
# har ulanishda yoqamiz. PostgreSQL'da bunga hojat yo'q.
if DATABASE_URL.startswith("sqlite"):
    from sqlalchemy import event

    @event.listens_for(engine.sync_engine, "connect")
    def _enable_sqlite_fk(dbapi_conn, _record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    """FastAPI dependency — har bir so'rov uchun alohida sessiya."""
    async with AsyncSessionLocal() as session:
        yield session


async def init_db() -> None:
    """Jadvallarni yaratadi (dev uchun; prod'da Alembic ishlatiladi) va
    baza bo'sh bo'lsa demo ma'lumotlarni to'ldiradi."""
    from database import models  # noqa: F401 — modellarni ro'yxatga olish

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    from database.seed import seed_if_empty

    await seed_if_empty()


async def close_db() -> None:
    await engine.dispose()
