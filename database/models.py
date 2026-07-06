"""SQLAlchemy modellari — BACKEND_SPEC.md 5-band jadvallari.

Kelishuvlar:
  - Barcha id'lar string (spec 3.2).
  - Sanalar ISO "YYYY-MM-DD" string ko'rinishida saqlanadi (spec 3.3) —
    ISO format bo'yicha string tartiblash xronologik tartib bilan bir xil.
  - JSON ustunlar (badges, theory, ...) SQLite'da ham, PostgreSQL'da ham ishlaydi.
"""

from sqlalchemy import (
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from database.db import Base


class User(Base):
    """Admin va viewer hisoblari (spec 5.1)."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # masalan "u-admin"
    name: Mapped[str] = mapped_column(String, nullable=False)
    login: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)  # "admin" | "viewer"
    title: Mapped[str] = mapped_column(String, default="", nullable=False)
    photo: Mapped[str] = mapped_column(Text, default="", nullable=False)  # base64 data-URL yoki ""


class Teacher(Base):
    """O'qituvchilar (spec 5.2). login users.login bilan birgalikda unikal —
    bu qoida CRUD qatlamida tekshiriladi (ikki jadval bo'ylab DB-darajali
    unikal cheklov qo'yib bo'lmaydi)."""

    __tablename__ = "teachers"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # "t1", "t2"...
    name: Mapped[str] = mapped_column(String, nullable=False)
    phone: Mapped[str] = mapped_column(String, default="", nullable=False)
    email: Mapped[str] = mapped_column(String, default="", nullable=False)
    login: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    photo: Mapped[str] = mapped_column(Text, default="", nullable=False)

    # classIds javob modelida shu bog'lanishdan hisoblanadi
    classes: Mapped[list["ClassGroup"]] = relationship(back_populates="teacher")


class ClassGroup(Base):
    """Sinflar (spec 5.3)."""

    __tablename__ = "classes"
    __table_args__ = (UniqueConstraint("grade", "letter", name="uq_classes_grade_letter"),)

    id: Mapped[str] = mapped_column(String, primary_key=True)  # "c-5a"
    grade: Mapped[int] = mapped_column(Integer, nullable=False)  # 1–11
    letter: Mapped[str] = mapped_column(String, nullable=False)  # "A", "B"...
    # O'qituvchi o'chirilganda sinf qoladi, teacher_id NULL bo'ladi (spec 6.5)
    teacher_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("teachers.id", ondelete="SET NULL"), nullable=True
    )

    teacher: Mapped["Teacher | None"] = relationship(back_populates="classes")
    students: Mapped[list["Student"]] = relationship(back_populates="class_group")
    # Sinf o'chirilganda jurnal ustunlari va katakchalari ham o'chadi (spec 6.4)
    journal_columns: Mapped[list["JournalColumn"]] = relationship(
        cascade="all, delete-orphan", passive_deletes=True
    )
    journal_entries: Mapped[list["JournalEntry"]] = relationship(
        cascade="all, delete-orphan", passive_deletes=True
    )


class Student(Base):
    """O'quvchilar (spec 5.4)."""

    __tablename__ = "students"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    class_id: Mapped[str] = mapped_column(
        String, ForeignKey("classes.id"), nullable=False, index=True
    )
    points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # >= 0
    badges: Mapped[list] = mapped_column(JSON, default=list, nullable=False)  # ["star", ...]

    class_group: Mapped["ClassGroup"] = relationship(back_populates="students")
    # O'quvchi o'chirilganda jurnal yozuvlari ham o'chadi (spec 6.6)
    journal_entries: Mapped[list["JournalEntry"]] = relationship(
        cascade="all, delete-orphan", passive_deletes=True
    )


class Lesson(Base):
    """Dars ishlanmalari (spec 5.5)."""

    __tablename__ = "lessons"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # "l-5-1-1"
    grade: Mapped[int] = mapped_column(Integer, nullable=False, index=True)  # 1–11
    quarter: Mapped[int] = mapped_column(Integer, nullable=False)  # 1–4
    order: Mapped[int] = mapped_column(Integer, nullable=False)  # chorak ichidagi tartib
    title: Mapped[str] = mapped_column(String, nullable=False)
    author_id: Mapped[str] = mapped_column(String, nullable=False)  # user yoki teacher id
    author_name: Mapped[str] = mapped_column(String, nullable=False)  # denormalizatsiya
    objective: Mapped[str] = mapped_column(Text, default="", nullable=False)
    theory: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    practice: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    homework: Mapped[str] = mapped_column(Text, default="", nullable=False)
    equipment: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    outcomes: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    video_url: Mapped[str] = mapped_column(String, default="", nullable=False)
    duration_min: Mapped[int] = mapped_column(Integer, default=45, nullable=False)
    status: Mapped[str] = mapped_column(String, default="draft", nullable=False)  # "ready" | "draft"


class QuarterInfo(Base):
    """Chorak ko'nikmalari (spec 5.6)."""

    __tablename__ = "quarter_infos"

    grade: Mapped[int] = mapped_column(Integer, primary_key=True)
    quarter: Mapped[int] = mapped_column(Integer, primary_key=True)
    skills: Mapped[list] = mapped_column(JSON, default=list, nullable=False)


class JournalColumn(Base):
    """O'tilgan dars — jurnal ustuni (spec 5.7)."""

    __tablename__ = "journal_columns"
    __table_args__ = (UniqueConstraint("class_id", "date", name="uq_journal_columns_class_date"),)

    id: Mapped[str] = mapped_column(String, primary_key=True)  # "jc-{classId}-{date}"
    class_id: Mapped[str] = mapped_column(
        String, ForeignKey("classes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date: Mapped[str] = mapped_column(String(10), nullable=False)  # "YYYY-MM-DD"
    # Jurnalga bog'langan darsni o'chirish taqiqlanadi (spec 6.2)
    lesson_id: Mapped[str] = mapped_column(
        String, ForeignKey("lessons.id", ondelete="RESTRICT"), nullable=False
    )


class JournalEntry(Base):
    """Baho/davomat katakchasi (spec 5.8). UNIQUE(student_id, date) — upsert."""

    __tablename__ = "journal_entries"
    __table_args__ = (UniqueConstraint("student_id", "date", name="uq_journal_entries_student_date"),)

    id: Mapped[str] = mapped_column(String, primary_key=True)  # "j-{studentId}-{date}"
    student_id: Mapped[str] = mapped_column(
        String, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    class_id: Mapped[str] = mapped_column(
        String, ForeignKey("classes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date: Mapped[str] = mapped_column(String(10), nullable=False)  # "YYYY-MM-DD"
    grade: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 2–5 yoki NULL
    attendance: Mapped[str] = mapped_column(
        String, default="keldi", nullable=False
    )  # "keldi" | "kelmadi" | "kechikdi"
