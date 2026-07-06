"""FastAPI dependency'lari: db sessiya, joriy foydalanuvchi, rol tekshiruvi.

Routerlarda ishlatish:

    from utils.deps import db_dependency, current_user_dependency, require_roles

    @router.get("/lessons")
    async def get_lessons(db: db_dependency, me: current_user_dependency): ...

    @router.post("/classes", dependencies=[Depends(require_roles("admin"))])
    async def create_class(db: db_dependency): ...
"""

from dataclasses import dataclass
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_db
from database.models import ClassGroup, Teacher, User
from schemas import SessionUser
from utils.security import decode_token

bearer_scheme = HTTPBearer(auto_error=False)

TEACHER_TITLE = "Informatika o'qituvchisi"  # spec 6.7 — o'zgarmas matn


@dataclass
class CurrentUser:
    """Token orqali aniqlangan foydalanuvchi (user yoki teacher)."""

    id: str
    name: str
    login: str
    role: str  # "admin" | "teacher" | "viewer"
    title: str
    photo: str
    kind: str  # "user" | "teacher"

    def to_session_user(self) -> SessionUser:
        return SessionUser(
            id=self.id, name=self.name, login=self.login,
            role=self.role, title=self.title, photo=self.photo,
        )


db_dependency = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(
    db: db_dependency,
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)] = None,
) -> CurrentUser:
    """Authorization: Bearer <token> ni tekshiradi, 401 da frontend login sahifasiga qaytadi."""
    if creds is None:
        raise HTTPException(401, "Token talab qilinadi")

    try:
        payload = decode_token(creds.credentials)
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Token yaroqsiz yoki muddati tugagan")

    sub, kind = payload.get("sub"), payload.get("kind")

    if kind == "teacher":
        teacher = await db.get(Teacher, sub)
        if teacher is None:
            raise HTTPException(401, "Token yaroqsiz yoki muddati tugagan")
        return CurrentUser(
            id=teacher.id, name=teacher.name, login=teacher.login,
            role="teacher", title=TEACHER_TITLE, photo=teacher.photo, kind="teacher",
        )

    user = await db.get(User, sub)
    if user is None:
        raise HTTPException(401, "Token yaroqsiz yoki muddati tugagan")
    return CurrentUser(
        id=user.id, name=user.name, login=user.login,
        role=user.role, title=user.title, photo=user.photo, kind="user",
    )


current_user_dependency = Annotated[CurrentUser, Depends(get_current_user)]


def require_roles(*roles: str):
    """Faqat ko'rsatilgan rollarga ruxsat — aks holda 403 (spec 10-band namunasi)."""

    def dep(user: current_user_dependency) -> CurrentUser:
        if user.role not in roles:
            raise HTTPException(403, "Bu amal uchun ruxsat yo'q")
        return user

    return dep


def assert_can_grade(user: CurrentUser, klass: ClassGroup) -> None:
    """Jurnal yozish ruxsati: admin — istalgan sinf, teacher — faqat o'z sinfi (spec 4-band)."""
    if user.role == "admin":
        return
    if user.role == "teacher" and klass.teacher_id == user.id:
        return
    raise HTTPException(403, "Bu sinfda baholash huquqingiz yo'q")
