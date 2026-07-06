"""MetodikaIT API — kirish nuqtasi.

Ishga tushirish (dev):
    uvicorn main:app --reload --port 8000
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database.db import close_db, init_db
from routers import auth, classes, journal, lessons, students, teachers


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await close_db()


app = FastAPI(title="MetodikaIT API", lifespan=lifespan)

# CORS — dev'da Vite frontend (spec 3.5)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(lessons.router)
app.include_router(classes.router)
app.include_router(teachers.router)
app.include_router(students.router)
app.include_router(journal.router)
