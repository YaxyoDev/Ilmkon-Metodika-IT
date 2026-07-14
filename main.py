"""MetodikaIT API — kirish nuqtasi.

Ishga tushirish (dev):
    uvicorn main:app --reload --port 8000
"""

"""
Kod yangilandi
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from database.db import close_db, init_db
from routers import auth, classes, journal, leaderboard, lessons, students, teachers


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await close_db()


app = FastAPI(title="MetodikaIT API", lifespan=lifespan)

# CORS — dev'da Vite frontend (spec 3.5)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", 
                   "https://metodika-it-frontend.vercel.app", 
                   "https://ilmkon-metodika.uz", 
                   "https://www.ilmkon-metodika.uz"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Validatsiya (422) xatolarini frontend kutgan yagona shaklga keltiradi (spec 0-band):
    body har doim {"detail": "<o'zbekcha matn>"} — FastAPI standarti bergan massiv emas."""
    errors = exc.errors()
    field = errors[0]["loc"][-1] if errors and errors[0].get("loc") else "ma'lumot"
    return JSONResponse(
        status_code=422,
        content={"detail": f"Yuborilgan ma'lumot noto'g'ri: «{field}» maydonini tekshiring"},
    )


app.include_router(auth.router)
app.include_router(lessons.router)
app.include_router(classes.router)
app.include_router(teachers.router)
app.include_router(students.router)
app.include_router(journal.router)
app.include_router(leaderboard.router)
