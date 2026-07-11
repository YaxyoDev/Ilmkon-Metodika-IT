"""Jurnal: yozuvlar, ustunlar, katakcha upsert + ball deltasi (spec 7.6, 6.1)."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select

from database.models import ClassGroup, JournalColumn, JournalEntry, PointsEvent, Student
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
from utils.points import cell_points, journal_reason

router = APIRouter(prefix="/api", tags=["journal"])

STREAK_LEN = 5  # "streak" nishoni: shuncha dars ketma-ket "keldi" (gamifikatsiya 3-band)


async def _auto_award_badges(db, student: Student, grade: int | None) -> str | None:
    """Jurnal saqlanganda nishonlarni avtomatik beradi (gamifikatsiya 3-band).

    Chaqirilishidan oldin joriy katak `db.flush()` bilan yozilgan bo'lishi kerak
    (streak hisobi shu o'quvchining barcha yozuvlarini o'qiydi). Berilgan yangi
    nishon id'sini qaytaradi (event'ning `badgeId` maydoniga yoziladi); bir
    saqlashda ikki nishon tushsa birinchisi qaytadi, ikkalasi ham beriladi.
    """
    awarded: str | None = None

    # star — birinchi marta «5» baho
    if grade == 5 and "star" not in student.badges:
        student.badges = student.badges + ["star"]
        awarded = "star"

    # streak — STREAK_LEN dars ketma-ket "keldi"
    if "streak" not in student.badges:
        attendances = (
            await db.scalars(
                select(JournalEntry.attendance)
                .where(JournalEntry.student_id == student.id)
                .order_by(JournalEntry.date)
            )
        ).all()
        run = best = 0
        for att in attendances:
            run = run + 1 if att == "keldi" else 0
            best = max(best, run)
        if best >= STREAK_LEN:
            student.badges = student.badges + ["streak"]
            awarded = awarded or "streak"

    return awarded


@router.get("/journal", response_model=list[JournalEntryOut])
async def get_journal(
    db: db_dependency,
    me: current_user_dependency,
    class_id: str = Query(alias="classId"),
):
    entries = await db.scalars(select(JournalEntry).where(JournalEntry.class_id == class_id))
    return entries.all()


@router.get("/students/{student_id}/journal", response_model=list[JournalEntryOut])
async def get_student_journal(
    student_id: str,
    db: db_dependency,
    me: current_user_dependency,
):
    """O'quvchining barcha (sinfidan qat'i nazar) jurnal yozuvlari, sana bo'yicha
    o'sish tartibida (gamifikatsiya 2-band). Sinf o'zgarsa ham tarix saqlanadi."""
    student = await db.get(Student, student_id)
    if student is None:
        raise HTTPException(404, "O'quvchi topilmadi")
    entries = await db.scalars(
        select(JournalEntry)
        .where(JournalEntry.student_id == student_id)
        .order_by(JournalEntry.date)
    )
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

    # Nishonlarni avtomatik berish (3-band) — joriy katak yozilgach hisoblanadi
    await db.flush()
    awarded_badge = await _auto_award_badges(db, student, grade)

    # Ball tarixi (1-band): har (student, date) uchun bitta "journal" event.
    # Yakuniy ball bilan mos bo'lishi uchun event delta = katakning to'liq bali;
    # ball 0 bo'lsa event o'chiriladi.
    event = await db.scalar(
        select(PointsEvent).where(
            PointsEvent.student_id == body.student_id,
            PointsEvent.date == body.date,
            PointsEvent.source == "journal",
        )
    )
    if new_pts > 0:
        if event is None:
            event = PointsEvent(
                student_id=body.student_id,
                date=body.date,
                delta=new_pts,
                source="journal",
                reason=journal_reason(grade, attendance),
                badge_id=awarded_badge,
            )
            db.add(event)
        else:
            event.delta = new_pts
            event.reason = journal_reason(grade, attendance)
            if awarded_badge:  # yangi nishon bo'lsa yozamiz, aks holda eskisi qoladi
                event.badge_id = awarded_badge
    elif event is not None:  # ball 0 ga tushdi — eski eventni o'chiramiz
        await db.delete(event)

    await db.commit()
    await db.refresh(entry)
    await db.refresh(student)
    return JournalCellResponse(
        entry=JournalEntryOut.model_validate(entry),
        student=StudentOut.model_validate(student),
    )
