<div align="center">

# 📚 MetodikaIT — Backend API

**Maktab informatika fani uchun o‘quv platformasi backendi**
*Backend for a school Computer Science teaching platform*

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.139-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)
[![JWT](https://img.shields.io/badge/Auth-JWT-000000?logo=jsonwebtokens&logoColor=white)](https://jwt.io/)

**🇺🇿 O‘zbekcha** &nbsp;·&nbsp; **🇬🇧 [English](#-english)**

</div>

---

## 🇺🇿 O‘zbekcha

### Loyiha haqida

**MetodikaIT** — maktab informatika o‘qituvchilari uchun to‘liq platforma backendi.
Dars ishlanmalari (1–11-sinf, 4 chorak), elektron jurnal (baho + davomat),
o‘quvchilar reytingi (ball va nishonlar), sinflar/o‘qituvchilar/o‘quvchilarni
boshqarish — barchasi bitta REST API orqali.

### Asosiy imkoniyatlar

- 🔐 **JWT autentifikatsiya** — rolga asoslangan ruxsatlar (`admin`, `teacher`, `viewer`)
- 📖 **Dars ishlanmalari** — avtomatik shablon generatsiyasi bilan CRUD
- 📊 **Elektron jurnal** — baho va davomat, `upsert` mantiqli katakchalar
- 🏆 **Reyting tizimi** — baho/davomatdan avtomatik ball hisoblanadi, nishonlar
- 👥 **Boshqaruv** — sinflar, o‘qituvchilar va o‘quvchilar CRUD
- 🌐 **Frontendga tayyor** — camelCase JSON, o‘zbekcha xato xabarlari, CORS
- 📝 **Avtomatik hujjat** — Swagger UI (`/docs`) va ReDoc (`/redoc`)

### Texnologiyalar

| Qatlam | Tanlov |
|---|---|
| Framework | FastAPI (async) |
| ORM | SQLAlchemy 2.x (async) |
| Ma’lumotlar bazasi | SQLite (dev) / PostgreSQL (prod) |
| Autentifikatsiya | JWT (PyJWT), Bearer token |
| Parol xavfsizligi | passlib + bcrypt |
| Server | Uvicorn |

### Rollar va ruxsatlar

| Amal | admin | teacher | viewer |
|---|:---:|:---:|:---:|
| Ko‘rish (darslar, jurnal, ...) | ✅ | ✅ | ✅ |
| Dars qo‘shish / tahrirlash | ✅ | ✅ | ❌ |
| Dars o‘chirish | ✅ (har qanday) | ✅ (faqat o‘ziniki) | ❌ |
| Jurnalga baho / davomat | ✅ (istalgan sinf) | ✅ (faqat o‘z sinfi) | ❌ |
| O‘quvchi CRUD + rag‘bat | ✅ | ✅ | ❌ |
| Sinflar / o‘qituvchilar CRUD | ✅ | ❌ | ❌ |
| O‘z profilini tahrirlash | ✅ | ✅ | ✅ |

### O‘rnatish va ishga tushirish

```bash
# 1. Virtual muhit (agar yo‘q bo‘lsa)
python -m venv .project

# 2. Faollashtirish
.\.project\Scripts\activate      # Windows (PowerShell)
source .project/bin/activate      # Linux / macOS

# 3. Kutubxonalarni o‘rnatish
pip install -r requirements.txt

# 4. Serverni ishga tushirish
uvicorn main:app --reload --port 8000
```

Server birinchi marta ishga tushganda **demo ma’lumotlar avtomatik** to‘ladi
(baza bo‘sh bo‘lsa). Keyin quyidagilar mavjud bo‘ladi:

- 🌐 API: `http://localhost:8000`
- 📘 Swagger UI: `http://localhost:8000/docs`
- 📗 ReDoc: `http://localhost:8000/redoc`

### Demo hisoblar

| Rol | Login | Parol |
|---|---|---|
| Admin | `admin` | `admin` |
| Viewer (rahbar) | `rahbar` | `rahbar` |
| O‘qituvchi | `karimov` | `1234` |
| O‘qituvchi | `yusupova` | `1234` |
| O‘qituvchi | `toshpulatov` | `1234` |

### Loyiha tuzilishi

```
Ilmkon_project/
├── main.py                  # FastAPI ilova, CORS, routerlar
├── schemas.py               # Pydantic modellar (camelCase JSON)
├── requirements.txt         # Bog‘liqliklar
├── .env                     # DATABASE_URL, JWT_SECRET, TOKEN_TTL
├── API_ENDPOINTS.md         # To‘liq API hujjati (frontend uchun)
├── BACKEND_SPEC.md          # Texnik topshiriq (spetsifikatsiya)
├── database/
│   ├── db.py                # Async engine, sessiya, init_db
│   ├── models.py            # SQLAlchemy jadvallari
│   └── seed.py              # Boshlang‘ich (demo) ma’lumotlar
├── routers/
│   ├── auth.py              # login, me, logout, profil
│   ├── lessons.py           # darslar + summary + choraklar
│   ├── classes.py           # sinflar CRUD
│   ├── teachers.py          # o‘qituvchilar CRUD
│   ├── students.py          # o‘quvchilar + ball + nishonlar
│   └── journal.py           # jurnal ustunlari + katakchalar
└── utils/
    ├── deps.py              # get_db, get_current_user, require_roles
    ├── security.py          # parol hash + JWT
    ├── points.py            # reyting ball formulasi
    ├── badges.py            # nishonlar lug‘ati
    └── lesson_template.py   # dars shablon generatorlari
```

### API hujjati

Barcha endpointlar (URL, body, javob, xatolar) — **[`API_ENDPOINTS.md`](./API_ENDPOINTS.md)**
faylida batafsil yozilgan. Interaktiv sinov uchun `/docs` (Swagger UI).

### Ma’lumotlar bazasini almashtirish (Prod)

`.env` faylida `DATABASE_URL` ni PostgreSQL ga o‘zgartiring:

```env
DATABASE_URL=postgresql+asyncpg://user:parol@localhost:5432/metodikait
```

---

## 🇬🇧 English

### About

**MetodikaIT** is the backend for a complete platform serving school Computer
Science teachers. It provides lesson plans (grades 1–11, 4 quarters), an electronic
gradebook (grades + attendance), a student rating system (points and badges), and
management of classes, teachers, and students — all through a single REST API.

### Key Features

- 🔐 **JWT authentication** — role-based access control (`admin`, `teacher`, `viewer`)
- 📖 **Lesson plans** — CRUD with automatic template generation
- 📊 **Electronic gradebook** — grades and attendance with upsert cell logic
- 🏆 **Rating system** — points auto-computed from grades/attendance, plus badges
- 👥 **Management** — CRUD for classes, teachers, and students
- 🌐 **Frontend-ready** — camelCase JSON, localized error messages, CORS
- 📝 **Auto docs** — Swagger UI (`/docs`) and ReDoc (`/redoc`)

### Tech Stack

| Layer | Choice |
|---|---|
| Framework | FastAPI (async) |
| ORM | SQLAlchemy 2.x (async) |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Authentication | JWT (PyJWT), Bearer token |
| Password security | passlib + bcrypt |
| Server | Uvicorn |

### Roles & Permissions

| Action | admin | teacher | viewer |
|---|:---:|:---:|:---:|
| View (lessons, gradebook, ...) | ✅ | ✅ | ✅ |
| Create / edit lessons | ✅ | ✅ | ❌ |
| Delete lessons | ✅ (any) | ✅ (own only) | ❌ |
| Gradebook grade / attendance | ✅ (any class) | ✅ (own class only) | ❌ |
| Student CRUD + rewards | ✅ | ✅ | ❌ |
| Classes / teachers CRUD | ✅ | ❌ | ❌ |
| Edit own profile | ✅ | ✅ | ✅ |

### Installation & Run

```bash
# 1. Create a virtual environment (if not present)
python -m venv .project

# 2. Activate it
.\.project\Scripts\activate      # Windows (PowerShell)
source .project/bin/activate      # Linux / macOS

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the server
uvicorn main:app --reload --port 8000
```

On first launch the **demo data is seeded automatically** (only if the database
is empty). Once running:

- 🌐 API: `http://localhost:8000`
- 📘 Swagger UI: `http://localhost:8000/docs`
- 📗 ReDoc: `http://localhost:8000/redoc`

### Demo Accounts

| Role | Login | Password |
|---|---|---|
| Admin | `admin` | `admin` |
| Viewer (principal) | `rahbar` | `rahbar` |
| Teacher | `karimov` | `1234` |
| Teacher | `yusupova` | `1234` |
| Teacher | `toshpulatov` | `1234` |

### Project Structure

```
Ilmkon_project/
├── main.py                  # FastAPI app, CORS, routers
├── schemas.py               # Pydantic models (camelCase JSON)
├── requirements.txt         # Dependencies
├── .env                     # DATABASE_URL, JWT_SECRET, TOKEN_TTL
├── API_ENDPOINTS.md         # Full API documentation (for frontend)
├── BACKEND_SPEC.md          # Technical specification
├── database/
│   ├── db.py                # Async engine, session, init_db
│   ├── models.py            # SQLAlchemy tables
│   └── seed.py              # Initial (demo) data
├── routers/
│   ├── auth.py              # login, me, logout, profile
│   ├── lessons.py           # lessons + summary + quarters
│   ├── classes.py           # classes CRUD
│   ├── teachers.py          # teachers CRUD
│   ├── students.py          # students + points + badges
│   └── journal.py           # journal columns + cells
└── utils/
    ├── deps.py              # get_db, get_current_user, require_roles
    ├── security.py          # password hashing + JWT
    ├── points.py            # rating point formula
    ├── badges.py            # badge dictionary
    └── lesson_template.py   # lesson template generators
```

### API Documentation

All endpoints (URL, body, response, errors) are documented in detail in
**[`API_ENDPOINTS.md`](./API_ENDPOINTS.md)**. For interactive testing use `/docs` (Swagger UI).

### Switching the Database (Prod)

Change `DATABASE_URL` in `.env` to PostgreSQL:

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/metodikait
```

---

<div align="center">

**MetodikaIT** — built with FastAPI ⚡

</div>
