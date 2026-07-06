"""Pydantic modellari ("form"lar) — BACKEND_SPEC.md 7-band JSON shakllari.

Barcha javob/so'rov maydonlari camelCase (spec 3.1): CamelModel buni
avtomatik bajaradi — Python'da snake_case yozamiz, JSON'da camelCase chiqadi.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

Attendance = Literal["keldi", "kelmadi", "kechikdi"]
LessonStatus = Literal["ready", "draft"]


class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


# --- Auth va profil (spec 7.1) ---

class LoginRequest(CamelModel):
    login: str
    password: str


class SessionUser(CamelModel):
    id: str
    name: str
    login: str
    role: Literal["admin", "teacher", "viewer"]
    title: str = ""
    photo: str = ""


class LoginResponse(CamelModel):
    token: str
    user: SessionUser


class ProfileUpdate(CamelModel):
    """Hamma maydon ixtiyoriy; bo'sh string e'tiborga olinmaydi (spec 7.1)."""

    name: str = ""
    phone: str = ""
    email: str = ""
    photo: str = ""
    password: str = ""


# --- O'qituvchilar (spec 7.4) ---

class TeacherOut(CamelModel):
    id: str
    name: str
    phone: str = ""
    email: str = ""
    class_ids: list[str] = []  # classes jadvalidan hisoblanadi
    login: str
    photo: str = ""


class TeacherCreate(CamelModel):
    name: str
    phone: str = ""
    email: str = ""
    class_ids: list[str] = []
    login: str
    password: str = ""  # yangi o'qituvchida majburiy (spec 6.5) — routerda tekshiriladi


class TeacherUpdate(CamelModel):
    name: str | None = None
    phone: str | None = None
    email: str | None = None
    class_ids: list[str] | None = None
    login: str | None = None
    password: str = ""  # bo'sh = eski parol saqlanadi
    photo: str | None = None


# --- Darslar (spec 7.2) ---

class GradeSummary(CamelModel):
    grade: int
    lesson_count: int
    ready_count: int


class LessonOut(CamelModel):
    id: str
    grade: int
    quarter: int
    order: int
    title: str
    author_id: str
    author_name: str
    objective: str = ""
    theory: list[str] = []
    practice: list[str] = []
    homework: str = ""
    equipment: list[str] = []
    outcomes: list[str] = []
    video_url: str = ""
    duration_min: int = 45
    status: LessonStatus = "draft"


class LessonCreate(CamelModel):
    """Frontend faqat shu maydonlarni yuboradi — qolgani shablon (spec 6.3)."""

    grade: int = Field(ge=1, le=11)
    quarter: int = Field(ge=1, le=4)
    title: str
    duration_min: int = 45


class LessonUpdate(CamelModel):
    """id/grade/quarter/order/author* o'zgartirilmaydi (kelsa e'tiborsiz)."""

    title: str | None = None
    objective: str | None = None
    theory: list[str] | None = None
    practice: list[str] | None = None
    homework: str | None = None
    equipment: list[str] | None = None
    outcomes: list[str] | None = None
    video_url: str | None = None
    duration_min: int | None = None
    status: LessonStatus | None = None


class QuarterInfoOut(CamelModel):
    grade: int
    quarter: int
    skills: list[str] = []


# --- Sinflar (spec 7.3) ---

class ClassGroupOut(CamelModel):
    id: str
    grade: int
    letter: str
    teacher_id: str | None = None


class ClassCreate(CamelModel):
    grade: int = Field(ge=1, le=11)
    letter: str
    teacher_id: str | None = None


class ClassUpdate(CamelModel):
    grade: int | None = Field(default=None, ge=1, le=11)
    letter: str | None = None
    teacher_id: str | None = None


# --- O'quvchilar va reyting (spec 7.5) ---

class StudentOut(CamelModel):
    id: str
    name: str
    class_id: str
    points: int = 0
    badges: list[str] = []


class StudentCreate(CamelModel):
    name: str
    class_id: str
    points: int = 0
    badges: list[str] = []


class StudentUpdate(CamelModel):
    name: str | None = None
    class_id: str | None = None
    points: int | None = None
    badges: list[str] | None = None


class PointsRequest(CamelModel):
    """Rag'batlantirish: points musbat/manfiy, natija max(0, ...) (spec 6.6)."""

    points: int
    badge_id: str | None = None


class BadgeDef(CamelModel):
    id: str
    name: str
    description: str


# --- Jurnal (spec 7.6) ---

class JournalEntryOut(CamelModel):
    id: str
    student_id: str
    class_id: str
    date: str  # "YYYY-MM-DD"
    grade: int | None = None
    attendance: Attendance = "keldi"


class JournalColumnOut(CamelModel):
    id: str
    class_id: str
    date: str
    lesson_id: str


class JournalColumnCreate(CamelModel):
    class_id: str
    date: str
    lesson_id: str


class JournalCellRequest(CamelModel):
    """Upsert (spec 7.6). Diqqat: grade "yuborilmagan" (eski qiymat qoladi) va
    "null yuborilgan" (baho o'chiriladi) holatlarini ajratish uchun routerda
    `"grade" in payload.model_fields_set` tekshiriladi. attendance ham shunday.
    """

    class_id: str
    student_id: str
    date: str
    grade: int | None = Field(default=None, ge=2, le=5)
    attendance: Attendance | None = None


class JournalCellResponse(CamelModel):
    entry: JournalEntryOut
    student: StudentOut
