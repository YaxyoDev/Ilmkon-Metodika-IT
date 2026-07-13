"""Server tarafida yutuqlarni hisoblash (API_REQUIREMENTS.md 6.6-band).

Frontenddagi 11 ta yutuq ID si (`src/utils/gamification.ts`) uchun shartlar bu
yerda TAXMINIY (ID nomidan kelib chiqib) belgilangan — frontendda aniq shartlar
paydo bo'lganda shu jadvalni moslashtirish kifoya. Endpoint hozir frontendda
ishlatilmaydi (spec 6.6 "kelajak uchun"), shuning uchun bu qo'shimcha xavfsiz.

Har yutuq ochilgan bo'lsa `{"id": ..., "unlockedAt": "YYYY-MM-DD"}` qaytadi;
ochilmagani ro'yxatga kirmaydi.
"""

from datetime import date as date_cls

# Ostonalar
FIVE_STARS_COUNT = 5      # five-stars — 5 ta «5»
SCHOLAR_COUNT = 15        # scholar — 15 ta «5»
STREAK5 = 5               # streak-5 — 5 dars ketma-ket "keldi"
STREAK10 = 10             # streak-10 — 10 dars ketma-ket "keldi"
ATTENDANCE_MIN_ENTRIES = 5
ATTENDANCE_RATE = 0.9     # attendance-90 — 90% davomat
POINTS_TIERS = {"points-100": 100, "points-300": 300, "points-600": 600}
COLLECTOR_BADGES = 3      # collector — 3 xil nishon
TOP_N = 3                 # top-3 — reytingda 1..3 o'rin


def _nth_date(entries, predicate, n: int) -> str | None:
    """`predicate`ni qanoatlantirgan n-chi yozuvning sanasi (sana bo'yicha o'sish)."""
    count = 0
    for e in entries:
        if predicate(e):
            count += 1
            if count == n:
                return e.date
    return None


def _streak_date(entries, need: int) -> str | None:
    """Ketma-ket `need` ta "keldi" to'planган paytdagi (need-chi) yozuv sanasi."""
    run = 0
    for e in entries:
        run = run + 1 if e.attendance == "keldi" else 0
        if run == need:
            return e.date
    return None


def compute_achievements(
    entries: list,          # JournalEntry — sana bo'yicha o'sish tartibida
    points: int,            # student.points
    badges: list[str],
    rank: int | None,       # umumiy reytingdagi o'rin (1 = birinchi), yo'q bo'lsa None
    today: str | None = None,
) -> list[dict]:
    today = today or date_cls.today().isoformat()
    out: list[dict] = []

    def add(aid: str, when: str | None):
        if when:
            out.append({"id": aid, "unlocked_at": when})

    present = [e for e in entries if e.attendance in ("keldi", "kechikdi")]

    # first-step — birinchi qatnashilgan dars
    add("first-step", present[0].date if present else None)
    # five-stars / scholar — «5» baholar soni
    add("five-stars", _nth_date(entries, lambda e: e.grade == 5, FIVE_STARS_COUNT))
    add("scholar", _nth_date(entries, lambda e: e.grade == 5, SCHOLAR_COUNT))
    # streak-5 / streak-10
    add("streak-5", _streak_date(entries, STREAK5))
    add("streak-10", _streak_date(entries, STREAK10))
    # attendance-90 — yetarli yozuv bo'lganda 90%+ davomat
    if len(entries) >= ATTENDANCE_MIN_ENTRIES and len(present) / len(entries) >= ATTENDANCE_RATE:
        add("attendance-90", entries[-1].date)
    # points-100 / 300 / 600 — joriy ballga qarab (aniq sana yo'q → bugun)
    for aid, tier in POINTS_TIERS.items():
        if points >= tier:
            add(aid, today)
    # collector — nishonlar to'plami
    if len(set(badges)) >= COLLECTOR_BADGES:
        add("collector", today)
    # top-3 — umumiy reyting
    if rank is not None and rank <= TOP_N:
        add("top-3", today)

    return out
