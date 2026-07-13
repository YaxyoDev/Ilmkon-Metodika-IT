"""Ma'lumotlar bazasi: async engine, sessiya va Base.

DATABASE_URL .env faylidan olinadi. Misollar:
  dev (SQLite):      sqlite+aiosqlite:///./metodika.db
  prod (PostgreSQL): postgresql+asyncpg://user:parol@localhost:5432/metodikait
"""

import os

from dotenv import load_dotenv
from sqlalchemy import inspect, text
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


async def _ensure_points_events_schema(conn) -> None:
    """create_all mavjud jadvalni o'zgartirmaydi (migration emas). Agar
    points_events eski sxema bilan qolgan bo'lsa, uni qayta quramiz —
    ma'lumot backfill_points_events_if_empty() orqali jurnal yozuvlaridan
    qayta tiklanadi, shuning uchun DROP xavfsiz."""

    def _needs_rebuild(sync_conn) -> bool:
        insp = inspect(sync_conn)
        if not insp.has_table("points_events"):
            return False  # jadval yo'q — create_all o'zi yaratadi
        cols = {c["name"] for c in insp.get_columns("points_events")}
        required = {"seq", "student_id", "date", "delta", "source", "reason", "badge_id"}
        return not required.issubset(cols)

    if await conn.run_sync(_needs_rebuild):
        await conn.execute(text("DROP TABLE points_events"))


async def init_db() -> None:
    """Jadvallarni yaratadi (dev uchun; prod'da Alembic ishlatiladi) va
    baza bo'sh bo'lsa demo ma'lumotlarni to'ldiradi."""
    from database import models  # noqa: F401 — modellarni ro'yxatga olish

    async with engine.begin() as conn:
        await _ensure_points_events_schema(conn)
        await conn.run_sync(Base.metadata.create_all)

    from database.seed import backfill_points_events_if_empty, seed_if_empty

    await seed_if_empty()
    await backfill_points_events_if_empty()


async def close_db() -> None:
    await engine.dispose()
