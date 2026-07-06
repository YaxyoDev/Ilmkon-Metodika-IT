"""O'qituvchilar CRUD + profil (spec 7.4, 6.5). Yozish faqat admin."""

from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select, update

from database.models import ClassGroup, Teacher, User
from schemas import TeacherCreate, TeacherOut, TeacherUpdate
from utils.deps import CurrentUser, current_user_dependency, db_dependency, require_roles
from utils.security import hash_password

router = APIRouter(prefix="/api", tags=["teachers"])


async def _login_taken(db, login: str, exclude_teacher_id: str | None = None) -> bool:
    """login users va teachers bo'ylab birgalikda unikal (spec 5.1/5.2)."""
    in_users = await db.scalar(select(func.count(User.id)).where(User.login == login))
    q = select(func.count(Teacher.id)).where(Teacher.login == login)
    if exclude_teacher_id:
        q = q.where(Teacher.id != exclude_teacher_id)
    in_teachers = await db.scalar(q)
    return bool(in_users or in_teachers)


async def _class_ids_of(db, teacher_id: str) -> list[str]:
    ids = await db.scalars(
        select(ClassGroup.id)
        .where(ClassGroup.teacher_id == teacher_id)
        .order_by(ClassGroup.grade, ClassGroup.letter)
    )
    return list(ids.all())


async def _teacher_out(db, teacher: Teacher) -> TeacherOut:
    return TeacherOut(
        id=teacher.id, name=teacher.name, phone=teacher.phone, email=teacher.email,
        class_ids=await _class_ids_of(db, teacher.id), login=teacher.login, photo=teacher.photo,
    )


async def _sync_class_links(db, teacher_id: str, class_ids: list[str]) -> None:
    """Eski bog'lardan chiqarib, berilgan sinflarni shu o'qituvchiga o'tkazadi."""
    await db.execute(
        update(ClassGroup)
        .where(ClassGroup.teacher_id == teacher_id, ClassGroup.id.not_in(class_ids))
        .values(teacher_id=None)
    )
    if class_ids:
        await db.execute(
            update(ClassGroup).where(ClassGroup.id.in_(class_ids)).values(teacher_id=teacher_id)
        )


@router.get("/teachers", response_model=list[TeacherOut])
async def get_teachers(db: db_dependency, me: current_user_dependency):
    teachers = await db.scalars(select(Teacher).order_by(Teacher.name))
    return [await _teacher_out(db, t) for t in teachers.all()]


@router.get("/teachers/{teacher_id}/profile", response_model=TeacherOut | None)
async def get_teacher_profile(teacher_id: str, db: db_dependency, me: current_user_dependency):
    """Topilmasa 200 null — frontend null'ni ham ko'taradi (spec 7.1)."""
    teacher = await db.get(Teacher, teacher_id)
    if teacher is None:
        return None
    return await _teacher_out(db, teacher)


@router.post("/teachers", response_model=TeacherOut, status_code=201)
async def create_teacher(
    body: TeacherCreate,
    db: db_dependency,
    me: CurrentUser = Depends(require_roles("admin")),
):
    if not body.password.strip():
        raise HTTPException(400, "Yangi o'qituvchi uchun parol kiritilishi shart")
    if await _login_taken(db, body.login):
        raise HTTPException(409, "Bu login band — boshqasini tanlang")

    teacher = Teacher(
        id=f"t-{uuid4().hex[:8]}",
        name=body.name, phone=body.phone, email=body.email,
        login=body.login, password_hash=hash_password(body.password), photo="",
    )
    db.add(teacher)
    await db.flush()
    if body.class_ids:
        await _sync_class_links(db, teacher.id, body.class_ids)
    await db.commit()
    await db.refresh(teacher)
    return await _teacher_out(db, teacher)


@router.patch("/teachers/{teacher_id}", response_model=TeacherOut)
async def update_teacher(
    teacher_id: str,
    body: TeacherUpdate,
    db: db_dependency,
    me: CurrentUser = Depends(require_roles("admin")),
):
    teacher = await db.get(Teacher, teacher_id)
    if teacher is None:
        raise HTTPException(404, "O'qituvchi topilmadi")

    if body.login is not None and body.login != teacher.login:
        if await _login_taken(db, body.login, exclude_teacher_id=teacher_id):
            raise HTTPException(409, "Bu login band — boshqasini tanlang")

    patch = body.model_dump(exclude_unset=True, exclude_none=True, exclude={"password", "class_ids"})
    for field, value in patch.items():
        setattr(teacher, field, value)

    if body.password:  # bo'sh kelsa eski parol saqlanadi (spec 6.5)
        teacher.password_hash = hash_password(body.password)

    if body.class_ids is not None:
        await _sync_class_links(db, teacher_id, body.class_ids)

    await db.commit()
    await db.refresh(teacher)
    return await _teacher_out(db, teacher)


@router.delete("/teachers/{teacher_id}", status_code=204)
async def delete_teacher(
    teacher_id: str,
    db: db_dependency,
    me: CurrentUser = Depends(require_roles("admin")),
):
    """Sinflar qoladi, teacher_id NULL bo'ladi (spec 6.5)."""
    teacher = await db.get(Teacher, teacher_id)
    if teacher is None:
        raise HTTPException(404, "O'qituvchi topilmadi")

    await db.execute(
        update(ClassGroup).where(ClassGroup.teacher_id == teacher_id).values(teacher_id=None)
    )
    await db.delete(teacher)
    await db.commit()
    return None
