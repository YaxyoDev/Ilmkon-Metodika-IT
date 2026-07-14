"""O'quvchilar CRUD, rag'bat ballari, nishonlar (spec 7.5, 6.6)."""

from datetime import date as date_cls
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import delete, func, select

from database.models import JournalEntry, PointsEvent, Student
from schemas import (
    AchievementOut,
    BadgeDef,
    PointsEventOut,
    PointsRequest,
    StudentCreate,
    StudentOut,
    StudentUpdate,
)
from utils.achievements import compute_achievements
from utils.badges import BADGE_DEFS
from utils.deps import CurrentUser, current_user_dependency, db_dependency, require_roles

router = APIRouter(prefix="/api", tags=["students"])


@router.get("/students", response_model=list[StudentOut])
async def get_students(
    db: db_dependency,
    me: current_user_dependency,
    class_id: str | None = Query(default=None, alias="classId"),
):
    q = select(Student).order_by(Student.name)
    if class_id:
        q = q.where(Student.class_id == class_id)
    students = await db.scalars(q)
    return students.all()


@router.post("/students", response_model=StudentOut, status_code=201)
async def create_student(
    body: StudentCreate,
    db: db_dependency,
    me: CurrentUser = Depends(require_roles("admin", "teacher")),
):
    student = Student(
        id=f"s-{uuid4().hex[:8]}",
        name=body.name,
        class_id=body.class_id,
        points=max(0, body.points),
        badges=list(dict.fromkeys(body.badges)),  # takrorsiz, tartib saqlanadi
    )
    db.add(student)
    await db.commit()
    await db.refresh(student)
    return student


@router.patch("/students/{student_id}", response_model=StudentOut)
async def update_student(
    student_id: str,
    body: StudentUpdate,
    db: db_dependency,
    me: CurrentUser = Depends(require_roles("admin", "teacher")),
):
    student = await db.get(Student, student_id)
    if student is None:
        raise HTTPException(404, "O'quvchi topilmadi")

    patch = body.model_dump(exclude_unset=True, exclude_none=True)
    if "points" in patch:
        patch["points"] = max(0, patch["points"])
    if "badges" in patch:
        patch["badges"] = list(dict.fromkeys(patch["badges"]))
    for field, value in patch.items():
        setattr(student, field, value)

    await db.commit()
    await db.refresh(student)
    return student


@router.delete("/students/{student_id}", status_code=204)
async def delete_student(
    student_id: str,
    db: db_dependency,
    me: CurrentUser = Depends(require_roles("admin", "teacher")),
):
    """Jurnal yozuvlari ham o'chadi (spec 6.6)."""
    student = await db.get(Student, student_id)
    if student is None:
        raise HTTPException(404, "O'quvchi topilmadi")

    await db.execute(delete(JournalEntry).where(JournalEntry.student_id == student_id))
    await db.delete(student)
    await db.commit()
    return None


@router.post("/students/{student_id}/points", response_model=StudentOut)
async def add_points(
    student_id: str,
    body: PointsRequest,
    db: db_dependency,
    me: CurrentUser = Depends(require_roles("admin", "teacher")),
):
    """Rag'bat: points musbat/manfiy, natija max(0, ...); badge takrorsiz (spec 6.6)."""
    if body.points == 0:
        raise HTTPException(422, "Ball 0 bo'lishi mumkin emas")

    student = await db.get(Student, student_id)
    if student is None:
        raise HTTPException(404, "O'quvchi topilmadi")

    student.points = max(0, student.points + body.points)
    if body.badge_id and body.badge_id not in student.badges:
        # JSON ustun mutatsiyani kuzatmaydi — yangi ro'yxat beriladi
        student.badges = student.badges + [body.badge_id]

    # Ball tarixi (gamifikatsiya 1-band): har rag'bat alohida event
    db.add(PointsEvent(
        student_id=student_id,
        date=date_cls.today().isoformat(),
        delta=body.points,
        source="reward",
        reason=body.reason or "Rag'bat",
        badge_id=body.badge_id,
    ))

    await db.commit()
    await db.refresh(student)
    return student


@router.delete("/points-events/{event_seq}", status_code=204)
async def delete_points_event(
    event_seq: int,
    db: db_dependency,
    me: CurrentUser = Depends(require_roles("admin", "teacher")),
):
    """Faqat "reward" eventni bekor qiladi: ball qaytariladi, event bilan
    berilgan nishon (boshqa event'da takrorlanmagan bo'lsa) olib tashlanadi.
    "journal" event'lar jurnal katakchasi orqali boshqariladi — bu yerda taqiq.

    Frontend event id'ni "pe-{seq}" ko'rinishida oladi (models.py) — u yerda
    "pe-" prefiksini kesib, faqat seq (int) yuboradi."""
    event = await db.get(PointsEvent, event_seq)
    if event is None:
        raise HTTPException(404, "Ball yozuvi topilmadi")
    if event.source != "reward":
        raise HTTPException(400, "Jurnal balini jurnal katakchasi orqali o'zgartiring")

    student = await db.get(Student, event.student_id)
    if student:
        student.points = max(0, student.points - event.delta)
        if event.badge_id and event.badge_id in student.badges:
            others = await db.scalar(
                select(func.count(PointsEvent.seq)).where(
                    PointsEvent.student_id == event.student_id,
                    PointsEvent.badge_id == event.badge_id,
                    PointsEvent.seq != event.seq,
                )
            )
            if not others:
                student.badges = [b for b in student.badges if b != event.badge_id]

    await db.delete(event)
    await db.commit()
    return None


@router.get("/students/{student_id}/points-history", response_model=list[PointsEventOut])
async def get_points_history(
    student_id: str,
    db: db_dependency,
    me: current_user_dependency,
    limit: int = Query(default=20, ge=1, le=200),
):
    """O'quvchining so'nggi ball o'zgarishlari — eng yangisi birinchi (1-band)."""
    student = await db.get(Student, student_id)
    if student is None:
        raise HTTPException(404, "O'quvchi topilmadi")
    events = await db.scalars(
        select(PointsEvent)
        .where(PointsEvent.student_id == student_id)
        .order_by(PointsEvent.date.desc(), PointsEvent.seq.desc())
        .limit(limit)
    )
    return events.all()


@router.get("/students/{student_id}/achievements", response_model=list[AchievementOut])
async def get_achievements(
    student_id: str,
    db: db_dependency,
    me: current_user_dependency,
):
    """O'quvchining ochilgan yutuqlari (spec 6.6). Shartlar `utils/achievements.py`
    da (frontend ro'yxatiga qarab moslashtiriladi)."""
    student = await db.get(Student, student_id)
    if student is None:
        raise HTTPException(404, "O'quvchi topilmadi")

    entries = (
        await db.scalars(
            select(JournalEntry)
            .where(JournalEntry.student_id == student_id)
            .order_by(JournalEntry.date)
        )
    ).all()

    # Umumiy reytingdagi o'rin (top-3 yutug'i uchun)
    higher = await db.scalar(
        select(func.count(Student.id)).where(Student.points > student.points)
    )
    rank = (higher or 0) + 1

    return compute_achievements(entries, student.points, student.badges, rank)


@router.get("/badges", response_model=list[BadgeDef])
async def get_badges():
    """Statik lug'at — token talab qilinmaydi (spec 7.5)."""
    return BADGE_DEFS
