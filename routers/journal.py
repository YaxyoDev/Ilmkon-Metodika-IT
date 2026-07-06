"""Jurnal: yozuvlar, ustunlar, katakcha upsert + ball deltasi (spec 7.6, 6.1)."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select

from database.models import ClassGroup, JournalColumn, JournalEntry, Student
from schemas import (
    JournalCellRequest,
    JournalCellResponse,
    JournalColumnCreate,
    JournalColumnOut,
    JournalEntryOut,
    StudentOut,
)
from utils.deps import (
    CurrentUser,
    assert_can_grade,
    current_user_dependency,
    db_dependency,
    require_roles,
)
from utils.points import cell_points

router = APIRouter(prefix="/api", tags=["journal"])


@router.get("/journal", response_model=list[JournalEntryOut])
async def get_journal(
    db: db_dependency,
    me: current_user_dependency,
    class_id: str = Query(alias="classId"),
):
    entries = await db.scalars(select(JournalEntry).where(JournalEntry.class_id == class_id))
    return entries.all()


@router.get("/journal/columns", response_model=list[JournalColumnOut])
async def get_journal_columns(
    db: db_dependency,
    me: current_user_dependency,
    class_id: str = Query(alias="classId"),
):
    columns = await db.scalars(
        select(JournalColumn)
        .where(JournalColumn.class_id == class_id)
        .order_by(JournalColumn.date)
    )
    return columns.all()


@router.post("/journal/columns", response_model=JournalColumnOut, status_code=201)
async def add_journal_column(
    body: JournalColumnCreate,
    db: db_dependency,
    me: CurrentUser = Depends(require_roles("admin", "teacher")),
):
    """«Dars o'tish»: admin — istalgan sinf, teacher — faqat o'z sinfi."""
    klass = await db.get(ClassGroup, body.class_id)
    if klass is None:
        raise HTTPException(404, "Sinf topilmadi")
    assert_can_grade(me, klass)

    duplicate = await db.scalar(
        select(func.count(JournalColumn.id)).where(
            JournalColumn.class_id == body.class_id, JournalColumn.date == body.date
        )
    )
    if duplicate:
        raise HTTPException(409, "Bu sana uchun dars allaqachon ochilgan")

    column = JournalColumn(
        id=f"jc-{body.class_id}-{body.date}",
        class_id=body.class_id,
        date=body.date,
        lesson_id=body.lesson_id,
    )
    db.add(column)
    await db.commit()
    await db.refresh(column)
    return column


@router.put("/journal/cell", response_model=JournalCellResponse)
async def set_journal_cell(
    body: JournalCellRequest,
    db: db_dependency,
    me: CurrentUser = Depends(require_roles("admin", "teacher")),
):
    """Upsert (spec 7.6): yuborilmagan maydon eski qiymatini saqlaydi,
    ball deltasi 6.1-band bo'yicha qo'llanadi."""
    klass = await db.get(ClassGroup, body.class_id)
    if klass is None:
        raise HTTPException(404, "Sinf topilmadi")
    assert_can_grade(me, klass)

    student = await db.get(Student, body.student_id)
    if student is None:
        raise HTTPException(404, "O'quvchi topilmadi")

    prev = await db.scalar(
        select(JournalEntry).where(
            JournalEntry.student_id == body.student_id, JournalEntry.date == body.date
        )
    )

    # "grade yuborilmagan" (eski qiymat qoladi) va "grade: null" (baho
    # o'chiriladi) holatlarini model_fields_set ajratadi
    sent = body.model_fields_set
    grade = body.grade if "grade" in sent else (prev.grade if prev else None)
    if "attendance" in sent and body.attendance:
        attendance = body.attendance
    else:
        attendance = prev.attendance if prev else "keldi"
    if attendance == "kelmadi":  # kelmagan o'quvchiga baho qo'yilmaydi (spec 6.1)
        grade = None

    old_pts = cell_points(prev.grade, prev.attendance) if prev else 0
    new_pts = cell_points(grade, attendance)
    student.points = max(0, student.points + (new_pts - old_pts))

    if prev:
        prev.grade = grade
        prev.attendance = attendance
        entry = prev
    else:
        entry = JournalEntry(
            id=f"j-{body.student_id}-{body.date}",
            student_id=body.student_id,
            class_id=body.class_id,
            date=body.date,
            grade=grade,
            attendance=attendance,
        )
        db.add(entry)

    await db.commit()
    await db.refresh(entry)
    await db.refresh(student)
    return JournalCellResponse(
        entry=JournalEntryOut.model_validate(entry),
        student=StudentOut.model_validate(student),
    )
