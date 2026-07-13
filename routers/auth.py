"""Auth va profil: login, me, logout, profil tahrirlash (spec 7.1)."""

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from database.models import Teacher, User
from schemas import LoginRequest, LoginResponse, ProfileUpdate, SessionUser
from utils.deps import TEACHER_TITLE, current_user_dependency, db_dependency
from utils.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/api", tags=["auth"])


@router.post("/auth/login", response_model=LoginResponse)
async def login(body: LoginRequest, db: db_dependency):
    """Avval users, keyin teachers'dan qidiriladi (spec 6.7)."""
    user = await db.scalar(select(User).where(User.login == body.login))
    if user and verify_password(body.password, user.password_hash):
        return LoginResponse(
            token=create_access_token(user.id, "user", user.role),
            user=SessionUser(
                id=user.id, name=user.name, login=user.login,
                role=user.role, title=user.title, photo=user.photo,
            ),
        )

    teacher = await db.scalar(select(Teacher).where(Teacher.login == body.login))
    if teacher and verify_password(body.password, teacher.password_hash):
        return LoginResponse(
            token=create_access_token(teacher.id, "teacher", "teacher"),
            user=SessionUser(
                id=teacher.id, name=teacher.name, login=teacher.login,
                role="teacher", title=TEACHER_TITLE, photo=teacher.photo,
            ),
        )

    raise HTTPException(401, "Login yoki parol noto'g'ri")


@router.get("/auth/me", response_model=SessionUser)
async def me(user: current_user_dependency):
    return user.to_session_user()


@router.post("/auth/logout", status_code=204)
async def logout(user: current_user_dependency):
    """JWT stateless — frontend tokenni o'chiradi, 204 yetarli (spec 7.1)."""
    return None


@router.patch("/profile", response_model=SessionUser)
async def update_profile(body: ProfileUpdate, me: current_user_dependency, db: db_dependency):
    """Faqat o'z profili. Bo'sh string kelgan maydon e'tiborga olinmaydi."""
    obj = await db.get(Teacher if me.kind == "teacher" else User, me.id)
    if obj is None:
        raise HTTPException(404, "Profil topilmadi")

    if body.name.strip():
        obj.name = body.name
    if body.photo:
        # Frontend rasm o'chirilganda "none" yuboradi (spec 2.3) — bo'sh saqlanadi
        obj.photo = "" if body.photo == "none" else body.photo
    if body.password:
        obj.password_hash = hash_password(body.password)
    if me.kind == "teacher":  # phone/email faqat teacher uchun ma'noli
        if body.phone:
            obj.phone = body.phone
        if body.email:
            obj.email = body.email

    await db.commit()
    await db.refresh(obj)

    return SessionUser(
        id=obj.id, name=obj.name, login=obj.login,
        role="teacher" if me.kind == "teacher" else obj.role,
        title=TEACHER_TITLE if me.kind == "teacher" else obj.title,
        photo=obj.photo,
    )
