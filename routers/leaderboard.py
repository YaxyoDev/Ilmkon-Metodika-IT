"""Davriy reyting — haftalik/oylik/chorak/umumiy (gamifikatsiya 5-band).

`points` — tanlangan davrdagi ball o'zgarishlari (PointsEvent.delta) yig'indisi;
`period=all` bo'lsa o'quvchining joriy umumiy bali (student.points) ishlatiladi,
chunki seed/tarixiy ballar har doim ham event ko'rinishida bo'lmasligi mumkin.

Davr oynasi bugundan orqaga siljiydi (rolling window):
  week → 7 kun, month → 30 kun, quarter → 90 kun.
"""

from datetime import date as date_cls
from datetime import timedelta

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, select

from database.models import PointsEvent, Student
from schemas import LeaderboardEntry, LeaderboardPeriod
from utils.deps import current_user_dependency, db_dependency

router = APIRouter(prefix="/api", tags=["leaderboard"])

PERIOD_DAYS = {"week": 7, "month": 30, "quarter": 90}


@router.get("/leaderboard", response_model=list[LeaderboardEntry])
async def get_leaderboard(
    db: db_dependency,
    me: current_user_dependency,
    period: LeaderboardPeriod = Query(default="all"),
    class_id: str | None = Query(default=None, alias="classId"),
):
    students_q = select(Student)
    if class_id:
        students_q = students_q.where(Student.class_id == class_id)
    students = (await db.scalars(students_q)).all()

    if period == "all":
        points_of = {s.id: s.points for s in students}
    else:
        threshold = (date_cls.today() - timedelta(days=PERIOD_DAYS[period])).isoformat()
        rows = await db.execute(
            select(PointsEvent.student_id, func.sum(PointsEvent.delta))
            .where(PointsEvent.date >= threshold)
            .group_by(PointsEvent.student_id)
        )
        sums = {sid: int(total or 0) for sid, total in rows.all()}
        points_of = {s.id: sums.get(s.id, 0) for s in students}

    # Ball bo'yicha kamayish tartibi, teng bo'lsa ism bo'yicha barqaror tartib
    ranked = sorted(students, key=lambda s: (-points_of[s.id], s.name))
    return [
        LeaderboardEntry(student_id=s.id, points=points_of[s.id], position=i)
        for i, s in enumerate(ranked, start=1)
    ]
