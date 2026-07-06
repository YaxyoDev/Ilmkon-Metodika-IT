"""Darslar: summary, CRUD, choraklar (spec 7.2, 6.2, 6.3)."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import case, func, select

from database.models import JournalColumn, Lesson, QuarterInfo
from schemas import GradeSummary, LessonCreate, LessonOut, LessonUpdate, QuarterInfoOut
from utils.deps import CurrentUser, current_user_dependency, db_dependency, require_roles
from utils.lesson_template import (
    EQUIPMENT_BASE,
    homework_for,
    objective_for,
    outcomes_for,
    practice_for,
    theory_for,
)

router = APIRouter(prefix="/api", tags=["lessons"])


@router.get("/lessons/summary", response_model=list[GradeSummary])
async def lessons_summary(db: db_dependency, me: current_user_dependency):
    """Har grade uchun statistika — 1–11 hammasi qaytadi (bo'sh bo'lsa 0)."""
    rows = (
        await db.execute(
            select(
                Lesson.grade,
                func.count(Lesson.id),
                func.sum(case((Lesson.status == "ready", 1), else_=0)),
            ).group_by(Lesson.grade)
        )
    ).all()
    stats = {grade: (count, ready or 0) for grade, count, ready in rows}
    return [
        GradeSummary(
            grade=g,
            lesson_count=stats.get(g, (0, 0))[0],
            ready_count=stats.get(g, (0, 0))[1],
        )
        for g in range(1, 12)
    ]


@router.get("/lessons", response_model=list[LessonOut])
async def get_lessons(grade: int, db: db_dependency, me: current_user_dependency):
    lessons = await db.scalars(
        select(Lesson).where(Lesson.grade == grade).order_by(Lesson.quarter, Lesson.order)
    )
    return lessons.all()


@router.get("/lessons/{lesson_id}", response_model=LessonOut)
async def get_lesson(lesson_id: str, db: db_dependency, me: current_user_dependency):
    lesson = await db.get(Lesson, lesson_id)
    if lesson is None:
        raise HTTPException(404, "Dars topilmadi")
    return lesson


@router.post("/lessons", response_model=LessonOut, status_code=201)
async def add_lesson(
    body: LessonCreate,
    db: db_dependency,
    me: CurrentUser = Depends(require_roles("admin", "teacher")),
):
    """Shablon tana backend'da yaratiladi, muallif tokendan olinadi (spec 6.3)."""
    max_order = await db.scalar(
        select(func.max(Lesson.order)).where(
            Lesson.grade == body.grade, Lesson.quarter == body.quarter
        )
    )
    order = (max_order or 0) + 1

    lesson = Lesson(
        id=f"l-{body.grade}-{body.quarter}-{order}",
        grade=body.grade,
        quarter=body.quarter,
        order=order,
        title=body.title,
        author_id=me.id,
        author_name=me.name,
        objective=objective_for(body.title, body.grade),
        theory=theory_for(body.title),
        practice=practice_for(body.title),
        homework=homework_for(body.title),
        equipment=list(EQUIPMENT_BASE),
        outcomes=outcomes_for(body.title),
        video_url="",
        duration_min=body.duration_min,
        status="draft",
    )
    db.add(lesson)
    await db.commit()
    await db.refresh(lesson)
    return lesson


@router.patch("/lessons/{lesson_id}", response_model=LessonOut)
async def update_lesson(
    lesson_id: str,
    body: LessonUpdate,
    db: db_dependency,
    me: CurrentUser = Depends(require_roles("admin", "teacher")),
):
    """id/grade/quarter/order/author* o'zgartirilmaydi — LessonUpdate'da yo'q."""
    lesson = await db.get(Lesson, lesson_id)
    if lesson is None:
        raise HTTPException(404, "Dars topilmadi")

    for field, value in body.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(lesson, field, value)

    await db.commit()
    await db.refresh(lesson)
    return lesson


@router.delete("/lessons/{lesson_id}", status_code=204)
async def delete_lesson(
    lesson_id: str,
    db: db_dependency,
    me: CurrentUser = Depends(require_roles("admin", "teacher")),
):
    """Faqat admin yoki muallif; jurnalga bog'langan bo'lsa taqiq (spec 6.2)."""
    lesson = await db.get(Lesson, lesson_id)
    if lesson is None:
        raise HTTPException(404, "Dars topilmadi")

    if me.role != "admin" and lesson.author_id != me.id:
        raise HTTPException(403, "Bu darsni faqat admin yoki uni yaratgan o'qituvchi o'chira oladi")

    used = await db.scalar(
        select(func.count(JournalColumn.id)).where(JournalColumn.lesson_id == lesson_id)
    )
    if used:
        raise HTTPException(
            400, "Bu dars jurnalda o'tilgan darslarga biriktirilgan — avval jurnalni tekshiring"
        )

    await db.delete(lesson)
    await db.commit()
    return None


@router.get("/quarters", response_model=list[QuarterInfoOut])
async def get_quarters(grade: int, db: db_dependency, me: current_user_dependency):
    infos = await db.scalars(
        select(QuarterInfo).where(QuarterInfo.grade == grade).order_by(QuarterInfo.quarter)
    )
    return infos.all()
