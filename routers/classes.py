"""Sinflar CRUD — yozish faqat admin (spec 7.3, 6.4)."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, func, select

from database.models import ClassGroup, JournalColumn, JournalEntry, Student
from schemas import ClassCreate, ClassGroupOut, ClassUpdate
from utils.deps import CurrentUser, current_user_dependency, db_dependency, require_roles

router = APIRouter(prefix="/api", tags=["classes"])


async def _duplicate_exists(db, grade: int, letter: str, exclude_id: str | None = None) -> bool:
    q = select(func.count(ClassGroup.id)).where(
        ClassGroup.grade == grade, ClassGroup.letter == letter
    )
    if exclude_id:
        q = q.where(ClassGroup.id != exclude_id)
    return bool(await db.scalar(q))


@router.get("/classes", response_model=list[ClassGroupOut])
async def get_classes(db: db_dependency, me: current_user_dependency):
    classes = await db.scalars(select(ClassGroup).order_by(ClassGroup.grade, ClassGroup.letter))
    return classes.all()


@router.post("/classes", response_model=ClassGroupOut, status_code=201)
async def create_class(
    body: ClassCreate,
    db: db_dependency,
    me: CurrentUser = Depends(require_roles("admin")),
):
    if await _duplicate_exists(db, body.grade, body.letter):
        raise HTTPException(409, "Bunday sinf allaqachon mavjud")

    klass = ClassGroup(
        id=f"c-{body.grade}{body.letter.lower()}",
        grade=body.grade,
        letter=body.letter,
        teacher_id=body.teacher_id,
    )
    db.add(klass)
    await db.commit()
    await db.refresh(klass)
    return klass


@router.patch("/classes/{class_id}", response_model=ClassGroupOut)
async def update_class(
    class_id: str,
    body: ClassUpdate,
    db: db_dependency,
    me: CurrentUser = Depends(require_roles("admin")),
):
    klass = await db.get(ClassGroup, class_id)
    if klass is None:
        raise HTTPException(404, "Sinf topilmadi")

    patch = body.model_dump(exclude_unset=True)
    new_grade = patch.get("grade", klass.grade)
    new_letter = patch.get("letter", klass.letter)
    if (new_grade, new_letter) != (klass.grade, klass.letter):
        if await _duplicate_exists(db, new_grade, new_letter, exclude_id=class_id):
            raise HTTPException(409, "Bunday sinf allaqachon mavjud")

    for field, value in patch.items():
        setattr(klass, field, value)

    await db.commit()
    await db.refresh(klass)
    return klass


@router.delete("/classes/{class_id}", status_code=204)
async def delete_class(
    class_id: str,
    db: db_dependency,
    me: CurrentUser = Depends(require_roles("admin")),
):
    """O'quvchisi bo'lsa o'chirilmaydi; jurnal yozuvlari cascade o'chadi (spec 6.4)."""
    klass = await db.get(ClassGroup, class_id)
    if klass is None:
        raise HTTPException(404, "Sinf topilmadi")

    student_count = await db.scalar(
        select(func.count(Student.id)).where(Student.class_id == class_id)
    )
    if student_count:
        raise HTTPException(400, "Bu sinfda o'quvchilar bor — avval ularni boshqa sinfga o'tkazing")

    await db.execute(delete(JournalEntry).where(JournalEntry.class_id == class_id))
    await db.execute(delete(JournalColumn).where(JournalColumn.class_id == class_id))
    await db.delete(klass)
    await db.commit()
    return None
