"""Boshlang'ich (seed) ma'lumotlar — MINIMAL variant (spec 8-band asosida).

Bu yerda spec 8-bandda TO'LIQ berilgan qismlar bor: hisoblar, 4 sinf,
jurnal sanalari. Dars mavzulari va o'quvchilar — namuna (har sinf uchun bir
nechta), to'liq 176 darslik o'quv dasturi keyin qo'shiladi.

Idempotent: users jadvali bo'sh bo'lmasa hech narsa qilinmaydi.
"""

import os

from sqlalchemy import func, select

from database.db import AsyncSessionLocal
from database.models import (
    ClassGroup,
    JournalColumn,
    JournalEntry,
    Lesson,
    PointsEvent,
    QuarterInfo,
    Student,
    Teacher,
    User,
)
from utils.lesson_template import (
    EQUIPMENT_BASE,
    homework_for,
    objective_for,
    outcomes_for,
    practice_for,
    theory_for,
)
from utils.points import cell_points, journal_reason
from utils.security import hash_password

# Standart admin (yaxyo) boshlang'ich paroli — production'da env'dan olinadi
# (7.2-band: repoda ochiq parol turmasligi uchun). Qo'yilmasa dev default "1710".
ADMIN_INITIAL_PASSWORD = os.getenv("ADMIN_INITIAL_PASSWORD", "1710")

# --- Hisoblar (spec 8.1) ---

USERS = [
    dict(id="u-yaxyo", name="Yaxyo", login="yaxyo", password=ADMIN_INITIAL_PASSWORD,
         role="admin", title="Administrator"),
    dict(id="u-admin", name="Aziz Rahmonov", login="admin", password="admin",
         role="admin", title="Platforma administratori"),
    dict(id="u-rahbar", name="Nodira Alimova", login="rahbar", password="rahbar",
         role="viewer", title="O'quv ishlari bo'yicha direktor o'rinbosari"),
]

TEACHERS = [
    dict(id="t1", name="Dilshod Karimov", login="karimov", password="1234",
         phone="+998 90 123 45 67", email="d.karimov@maktab.uz"),
    dict(id="t2", name="Malika Yusupova", login="yusupova", password="1234",
         phone="+998 90 234 56 78", email="m.yusupova@maktab.uz"),
    dict(id="t3", name="Jasur Toshpo'latov", login="toshpulatov", password="1234",
         phone="+998 90 345 67 89", email="j.toshpulatov@maktab.uz"),
]

# --- Sinflar (spec 8.2): 3-A→t2, 5-A→t1, 7-B→t1, 9-A→t3 ---

CLASSES = [
    dict(id="c-3a", grade=3, letter="A", teacher_id="t2"),
    dict(id="c-5a", grade=5, letter="A", teacher_id="t1"),
    dict(id="c-7b", grade=7, letter="B", teacher_id="t1"),
    dict(id="c-9a", grade=9, letter="A", teacher_id="t3"),
]

# Muallif: dars grade'iga biriktirilgan o'qituvchi (spec 8.3)
GRADE_AUTHOR = {3: "t2", 5: "t1", 7: "t1", 9: "t3"}
AUTHOR_NAME = {t["id"]: t["name"] for t in TEACHERS}

# --- Namuna dars mavzulari (har seed-sinf grade'i uchun 1-chorak, 4 tadan) ---

SAMPLE_TOPICS = {
    3: ["Kompyuter va uning qismlari", "Sichqoncha bilan ishlash",
        "Klaviaturada yozish", "Rasm chizish dasturi"],
    5: ["Informatika nima o'rganadi?", "Axborot va uning turlari",
        "Kompyuter tuzilishi", "Fayl va papkalar bilan ishlash"],
    7: ["Elektron jadvallar asoslari", "Formulalar va hisob-kitob",
        "Diagrammalar qurish", "Ma'lumotlarni saralash va filtrlash"],
    9: ["Algoritm tushunchasi", "Blok-sxemalar", "Chiziqli algoritmlar",
        "Shartli va takror algoritmlar"],
}

# --- Namuna o'quvchilar (har sinf uchun) ---

SAMPLE_STUDENTS = {
    "c-3a": ["Aziza Rustamova", "Sardor Aliyev", "Malika Qodirova",
             "Jasur Ergashev", "Nilufar Saidova"],
    "c-5a": ["Ozoda Karimova", "Bekzod Tursunov", "Gulnoza Yo'ldosheva",
             "Sanjar Mirzayev", "Dilnoza Abdullayeva", "Otabek Nazarov"],
    "c-7b": ["Kamola Sobirova", "Islom Rahimov", "Sevara Umarova",
             "Doston Qosimov", "Madina Xolmatova"],
    "c-9a": ["Shahzod Yusupov", "Feruza Ismoilova", "Alisher G'aniyev",
             "Nozima Tosheva", "Rustam Berdiyev"],
}

# --- Jurnal sanalari (spec 8.6) ---

JOURNAL_DATES = ["2026-05-12", "2026-05-19", "2026-05-26", "2026-06-02"]

# O'quv yili boshi — reconcile_points_baseline() shu sana bilan boshlang'ich
# ball eventini yozadi. Davriy oynalarga (hafta/oy/chorak) tushmasligi kerak.
BASELINE_DATE = "2025-09-01"


def _make_lesson(grade: int, quarter: int, order: int, title: str) -> Lesson:
    author_id = GRADE_AUTHOR[grade]
    return Lesson(
        id=f"l-{grade}-{quarter}-{order}",
        grade=grade, quarter=quarter, order=order, title=title,
        author_id=author_id, author_name=AUTHOR_NAME[author_id],
        objective=objective_for(title, grade),
        theory=theory_for(title), practice=practice_for(title),
        homework=homework_for(title), equipment=list(EQUIPMENT_BASE),
        outcomes=outcomes_for(title), video_url="",
        duration_min=45, status="ready",
    )


async def seed_if_empty() -> None:
    """Baza bo'sh bo'lsa demo ma'lumotlarni yaratadi (idempotent)."""
    async with AsyncSessionLocal() as db:
        existing = await db.scalar(select(func.count(User.id)))
        if existing:
            return  # allaqachon seed qilingan

        # 1) Hisoblar
        for u in USERS:
            db.add(User(
                id=u["id"], name=u["name"], login=u["login"],
                password_hash=hash_password(u["password"]),
                role=u["role"], title=u["title"], photo="",
            ))
        for t in TEACHERS:
            db.add(Teacher(
                id=t["id"], name=t["name"], login=t["login"],
                password_hash=hash_password(t["password"]),
                phone=t["phone"], email=t["email"], photo="",
            ))

        # 2) Sinflar
        for c in CLASSES:
            db.add(ClassGroup(id=c["id"], grade=c["grade"],
                              letter=c["letter"], teacher_id=c["teacher_id"]))

        # 3) Namuna darslar + chorak ko'nikmalari
        for grade, topics in SAMPLE_TOPICS.items():
            for i, title in enumerate(topics, start=1):
                db.add(_make_lesson(grade, quarter=1, order=i, title=title))
            db.add(QuarterInfo(
                grade=grade, quarter=1,
                skills=[f"«{t}» mavzusi bo'yicha bilim va amaliy ko'nikma" for t in topics],
            ))

        # 4) O'quvchilar (deterministik boshlang'ich ball)
        student_ids: dict[str, list[str]] = {}
        for class_id, names in SAMPLE_STUDENTS.items():
            ids = []
            for j, name in enumerate(names):
                sid = f"s-{class_id[2:]}-{j + 1}"
                points = 40 + j * 10
                badges = ["star"] if j == 0 else (["helper"] if j == 1 else [])
                db.add(Student(id=sid, name=name, class_id=class_id,
                               points=points, badges=badges))
                ids.append(sid)
            student_ids[class_id] = ids

        await db.flush()

        # 5) Jurnal: har seed-sinfga o'tilgan sanalar + katakchalar
        for class_id in SAMPLE_STUDENTS:
            grade = next(c["grade"] for c in CLASSES if c["id"] == class_id)
            lesson_ids = [f"l-{grade}-1-{k}" for k in range(1, 5)]
            for d, date in enumerate(JOURNAL_DATES):
                db.add(JournalColumn(
                    id=f"jc-{class_id}-{date}", class_id=class_id,
                    date=date, lesson_id=lesson_ids[d % len(lesson_ids)],
                ))
                for j, sid in enumerate(student_ids[class_id]):
                    grade_val = 5 - ((j + d) % 4)  # 5..2 orasida aylanadi
                    attendance = "keldi" if (j + d) % 5 else "kechikdi"
                    db.add(JournalEntry(
                        id=f"j-{sid}-{date}", student_id=sid, class_id=class_id,
                        date=date, grade=grade_val, attendance=attendance,
                    ))

        await db.commit()


async def ensure_default_admin() -> None:
    """Standart admin hisobini (login: yaxyo) kafolatlaydi.

    `seed_if_empty` faqat bo'sh bazada ishlaydi; production bazasi allaqachon
    eski seed bilan to'lgan bo'lsa ham bu funksiya `yaxyo` hisobini qo'shadi
    (agar hali yo'q bo'lsa). To'liq idempotent — mavjud bo'lsa hech narsa
    qilmaydi, parolni qayta yozmaydi."""
    async with AsyncSessionLocal() as db:
        exists = await db.scalar(select(User).where(User.login == "yaxyo"))
        if exists:
            return
        db.add(User(
            id="u-yaxyo", name="Yaxyo", login="yaxyo",
            password_hash=hash_password(ADMIN_INITIAL_PASSWORD),
            role="admin", title="Administrator", photo="",
        ))
        await db.commit()


async def backfill_points_events_if_empty() -> None:
    """Mavjud jurnal yozuvlaridan ball tarixini to'ldiradi (gamifikatsiya 1-band).

    Idempotent: points_events jadvali bo'sh bo'lsagina ishlaydi. Bu eski bazalarda
    (seed allaqachon bajarilgan) ham timeline/davriy reyting uchun tarixiy
    "journal" event'larni yaratadi. Yangi ball o'zgarishlari keyin avtomatik
    log qilinadi."""
    async with AsyncSessionLocal() as db:
        if await db.scalar(select(func.count(PointsEvent.seq))):
            return  # allaqachon tarix bor

        entries = (
            await db.scalars(select(JournalEntry).order_by(JournalEntry.date))
        ).all()
        for e in entries:
            pts = cell_points(e.grade, e.attendance)
            if pts > 0:
                db.add(PointsEvent(
                    student_id=e.student_id, date=e.date, delta=pts,
                    source="journal", reason=journal_reason(e.grade, e.attendance),
                ))
        await db.commit()


async def reconcile_points_baseline() -> None:
    """student.points va sum(PointsEvent.delta) orasidagi farqni bir martalik
    "boshlang'ich ball" eventi bilan yopadi (gamifikatsiya 2–3-band).

    Seed o'quvchilari event'siz boshlang'ich ball oladi; backfill esa faqat
    jurnal katakchalaridan event tiklaydi — natijada davriy reyting va ball
    tarixi student.points bilan mos kelmaydi. Bu funksiya farqni eski sana
    (BASELINE_DATE) bilan "reward" event qilib yozadi.

    Idempotent: birinchi ishga tushirishdan keyin farq 0 bo'ladi va boshqa
    hech narsa yozilmaydi."""
    async with AsyncSessionLocal() as db:
        students = (await db.scalars(select(Student))).all()
        rows = await db.execute(
            select(PointsEvent.student_id, func.sum(PointsEvent.delta))
            .group_by(PointsEvent.student_id)
        )
        sums = {sid: int(total or 0) for sid, total in rows.all()}
        for s in students:
            diff = s.points - sums.get(s.id, 0)
            if diff:
                db.add(PointsEvent(
                    student_id=s.id, date=BASELINE_DATE, delta=diff,
                    source="reward", reason="Boshlang'ich ball",
                ))
        await db.commit()
