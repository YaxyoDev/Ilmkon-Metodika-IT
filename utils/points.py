"""Reyting ballari — yagona manba (spec 6.1)."""

GRADE_POINTS = {5: 15, 4: 10, 3: 5, 2: 0}
ATTENDANCE_POINTS = {"keldi": 2, "kechikdi": 1, "kelmadi": 0}


def cell_points(grade: int | None, attendance: str) -> int:
    return (GRADE_POINTS.get(grade, 0) if grade else 0) + ATTENDANCE_POINTS[attendance]
