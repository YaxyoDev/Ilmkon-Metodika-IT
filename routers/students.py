"""O'quvchilar CRUD, rag'bat ballari, nishonlar (spec 7.5, 6.6)."""

from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import delete, select

from database.models import JournalEntry, Student
from schemas import BadgeDef, PointsRequest, StudentCreate, StudentOut, StudentUpdate
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
    student = await db.get(Student, student_id)
    if student is None:
        raise HTTPException(404, "O'quvchi topilmadi")

    student.points = max(0, student.points + body.points)
    if body.badge_id and body.badge_id not in student.badges:
        # JSON ustun mutatsiyani kuzatmaydi — yangi ro'yxat beriladi
        student.badges = student.badges + [body.badge_id]

    await db.commit()
    await db.refresh(student)
    return student


@router.get("/badges", response_model=list[BadgeDef])
async def get_badges():
    """Statik lug'at — token talab qilinmaydi (spec 7.5)."""
    return BADGE_DEFS
