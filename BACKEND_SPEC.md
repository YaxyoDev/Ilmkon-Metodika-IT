# MetodikaIT — Backend spetsifikatsiyasi (Python)

> Ushbu hujjat frontend loyihani 100% qamrab oladigan backend yaratish uchun to'liq
> texnik topshiriq. Frontend'dagi yagona API qatlami — `src/services/api.ts` — hozir
> localStorage bilan ishlaydi; backend tayyor bo'lgach shu fayldagi har bir funksiya
> quyidagi HTTP endpointlarga almashtiriladi. Boshqa hech qaysi faylga tegilmaydi.

---

## 1. Loyiha haqida

**MetodikaIT** — maktab informatika fani uchun platforma: dars ishlanmalari (1–11-sinf,
4 chorak), elektron jurnal (baho + davomat), o'quvchilar reytingi (ball/nishon),
sinflar/o'qituvchilar/o'quvchilar boshqaruvi, taqdimot rejimi.

**Rollar:** `admin` (hammasi), `teacher` (darslar, jurnal, o'quvchilar, reyting),
`viewer` (faqat ko'rish — maktab rahbariyati).

---

## 2. Tavsiya etiladigan stek

| Qatlam | Tanlov | Izoh |
|---|---|---|
| Framework | **FastAPI** | async, avtomatik OpenAPI docs, Pydantic validatsiya |
| ORM | SQLAlchemy 2.x + Alembic | migratsiyalar uchun |
| DB | PostgreSQL (prod) / SQLite (dev) | |
| Auth | JWT (PyJWT yoki python-jose), Bearer token | `Authorization: Bearer <token>` |
| Parol | passlib[bcrypt] | parollar hash'lanadi |
| Server | uvicorn | dev: `uvicorn app.main:app --reload --port 8000` |

---

## 3. Umumiy kelishuvlar (MUHIM — frontend moslik sharti)

1. **JSON maydon nomlari camelCase** bo'lishi shart (`authorName`, `classId`,
   `durationMin`...). Pydantic'da: `alias_generator=to_camel, populate_by_name=True`.
2. **Barcha `id`lar — string** (`"l-5-1-1"`, `"t1"`, UUID ham bo'ladi — faqat string bo'lsin).
3. **Sanalar** — ISO `YYYY-MM-DD` string (`"2026-05-12"`). Vaqt zonasi ishlatilmaydi.
4. **Xato formati** — frontend xato xabarini foydalanuvchiga TO'G'RIDAN-TO'G'RI
   ko'rsatadi, shuning uchun xabarlar **o'zbek tilida** va aynan quyida keltirilgan
   matnlarda bo'lishi kerak. Format:
   ```json
   { "detail": "Login yoki parol noto'g'ri" }
   ```
   HTTP statuslar: 400 (validatsiya/biznes qoida), 401 (token yo'q/yaroqsiz),
   403 (ruxsat yo'q), 404 (topilmadi), 409 (konflikt/dublikat).
5. **CORS**: dev'da `http://localhost:5173` (Vite) ruxsat etilsin
   (`allow_credentials`, barcha metodlar, `Authorization` header).
6. **Parollar hech qachon javobda qaytarilmaydi** (Teacher/User javob modellarida
   `password` maydoni bo'lmasin yoki bo'sh string bo'lsin).
7. `photo` maydoni — **base64 data-URL string** (`"data:image/png;base64,..."`).
   Frontend rasmni shu ko'rinishda yuboradi. Request body limitini kamida 5 MB qiling.
   (Keyinchalik fayl-storage'ga o'tkazish mumkin, lekin string qaytarish shart.)

---

## 4. Rollar va ruxsatlar matritsasi

| Amal | admin | teacher | viewer |
|---|---|---|---|
| Darslarni ko'rish | ✅ | ✅ | ✅ |
| Dars qo'shish / tahrirlash | ✅ | ✅ | ❌ |
| Dars o'chirish | ✅ (har qandayini) | ✅ (**faqat o'zi yaratganini**: `lesson.authorId == me.id`) | ❌ |
| Jurnal ko'rish | ✅ | ✅ | ✅ |
| Jurnalga baho/davomat, «dars o'tish» ustuni | ✅ (istalgan sinf) | ✅ (**faqat o'z sinfi**: `class.teacherId == me.id`) | ❌ |
| O'quvchi qo'shish/tahrirlash/o'chirish | ✅ | ✅ | ❌ |
| Ball/nishon berish (rag'bat) | ✅ | ✅ | ❌ |
| Sinflar CRUD | ✅ | ❌ | ❌ |
| O'qituvchilar CRUD | ✅ | ❌ | ❌ |
| O'z profilini tahrirlash | ✅ | ✅ | ✅ |

> Frontend UI bu qoidalarni yashiradi, lekin backend ularni **majburiy** tekshirishi kerak.

---

## 5. Ma'lumotlar bazasi modeli

### 5.1 `users` (admin va viewer hisoblar)

| Maydon | Turi | Izoh |
|---|---|---|
| id | str PK | masalan `u-admin` |
| name | str | ism-familiya |
| login | str UNIQUE | **teachers.login bilan ham umumiy unikal** |
| password_hash | str | |
| role | enum: `admin` \| `viewer` | |
| title | str | lavozim (masalan «Platforma administratori») |
| photo | text | base64 data-URL yoki `""` |

### 5.2 `teachers`

| Maydon | Turi | Izoh |
|---|---|---|
| id | str PK | `t1`, `t2`... |
| name | str | |
| phone | str | `"+998 90 123 45 67"` |
| email | str | |
| login | str UNIQUE | users.login bilan umumiy unikal |
| password_hash | str | |
| photo | text | |

> `classIds: string[]` — teacher javob modelida hisoblanadigan maydon:
> `SELECT id FROM classes WHERE teacher_id = :id`. Alohida ustun saqlash shart emas,
> lekin JSON javobda **majburiy** (`"classIds": ["c-5a", "c-7b"]`).

### 5.3 `classes`

| Maydon | Turi | Izoh |
|---|---|---|
| id | str PK | `c-5a` |
| grade | int (1–11) | |
| letter | str | `"A"`, `"B"`... |
| teacher_id | str FK→teachers | sinf rahbari (informatika o'qituvchisi) |

UNIQUE(grade, letter).

### 5.4 `students`

| Maydon | Turi | Izoh |
|---|---|---|
| id | str PK | |
| name | str | |
| class_id | str FK→classes | |
| points | int ≥ 0 | reyting bali (jurnal + rag'batlardan avtomatik yig'iladi) |
| badges | JSON array of str | nishon id'lari, masalan `["star","helper"]`, takrorsiz |

### 5.5 `lessons` — dars ishlanmasi

| Maydon | Turi | Izoh |
|---|---|---|
| id | str PK | seed: `l-{grade}-{quarter}-{order}` |
| grade | int 1–11 | |
| quarter | int 1–4 | |
| order | int | chorak ichidagi tartib raqami |
| title | str | |
| author_id | str | **yaratgan foydalanuvchi id (user yoki teacher)** |
| author_name | str | yaratgan odam ism-familiyasi (denormalizatsiya — javobda shart) |
| objective | text | dars maqsadi |
| theory | JSON array of str | nazariy qism abzatslari |
| practice | JSON array of str | amaliy topshiriqlar |
| homework | text | |
| equipment | JSON array of str | |
| outcomes | JSON array of str | |
| video_url | str | `""` bo'lishi mumkin |
| duration_min | int | default 45 |
| status | enum: `ready` \| `draft` | |

### 5.6 `quarter_infos` — chorak ko'nikmalari

| Maydon | Turi |
|---|---|
| grade | int |
| quarter | int |
| skills | JSON array of str |

PK(grade, quarter).

### 5.7 `journal_columns` — o'tilgan dars (jurnal ustuni)

| Maydon | Turi | Izoh |
|---|---|---|
| id | str PK | `jc-{classId}-{date}` |
| class_id | str FK | |
| date | date (ISO str) | |
| lesson_id | str FK→lessons | o'tilgan mavzu |

UNIQUE(class_id, date) — «Bu sana uchun dars allaqachon ochilgan».

### 5.8 `journal_entries` — baho/davomat katakchasi

| Maydon | Turi | Izoh |
|---|---|---|
| id | str PK | `j-{studentId}-{date}` |
| student_id | str FK | |
| class_id | str FK | |
| date | date (ISO str) | |
| grade | int (2–5) yoki NULL | baho qo'yilmagan = null |
| attendance | enum: `keldi` \| `kelmadi` \| `kechikdi` | default `keldi` |

UNIQUE(student_id, date) — **upsert** semantikasi (qayta yozilsa yangilanadi).

### 5.9 Nishonlar (statik lug'at — jadval shart emas, konstanta bo'lishi mumkin)

```json
[
  { "id": "star",    "name": "Yulduzcha",         "description": "Darsda 5 baho olgani uchun" },
  { "id": "streak",  "name": "Faol ishtirokchi",  "description": "5 dars ketma-ket faol qatnashgani uchun" },
  { "id": "project", "name": "Loyiha ustasi",     "description": "Yakuniy loyihani a'lo himoya qilgani uchun" },
  { "id": "helper",  "name": "Yordamchi",         "description": "Sinfdoshlariga yordam bergani uchun" },
  { "id": "speed",   "name": "Tezkor",            "description": "Amaliy topshiriqni birinchi bo'lib bajargani uchun" }
]
```

---

## 6. Biznes qoidalari (backend majburiy bajaradi)

### 6.1 Reyting ballari — yagona manba

```python
GRADE_POINTS = {5: 15, 4: 10, 3: 5, 2: 0}
ATTENDANCE_POINTS = {"keldi": 2, "kechikdi": 1, "kelmadi": 0}

def cell_points(grade: int | None, attendance: str) -> int:
    return (GRADE_POINTS.get(grade, 0) if grade else 0) + ATTENDANCE_POINTS[attendance]
```

Jurnal katakchasi saqlanganda **delta** qo'llanadi (eski katak ballari ayirilib,
yangisi qo'shiladi), student.points hech qachon 0 dan pastga tushmaydi:

```python
old_pts = cell_points(prev.grade, prev.attendance) if prev else 0
new_pts = cell_points(entry.grade, entry.attendance)
student.points = max(0, student.points + (new_pts - old_pts))
```

`attendance == "kelmadi"` bo'lsa frontend `grade: null` yuboradi (backend ham shuni
majburlasa yaxshi).

### 6.2 Dars muallifi va o'chirish

- Dars yaratilganda `author_id`/`author_name` **tokendagi foydalanuvchidan** olinadi
  (request body'da kelmaydi!).
- O'chirish: faqat `admin` yoki `author_id == me.id`. Aks holda 403:
  `"Bu darsni faqat admin yoki uni yaratgan o'qituvchi o'chira oladi"`.
- Dars biror `journal_columns.lesson_id` da ishlatilgan bo'lsa o'chirish taqiqlanadi, 400:
  `"Bu dars jurnalda o'tilgan darslarga biriktirilgan — avval jurnalni tekshiring"`.

### 6.3 Yangi dars — shablon tanasi

Frontend faqat `{grade, quarter, title, durationMin?}` yuboradi. Backend qolgan
maydonlarni shablon bo'yicha **o'zi generatsiya qiladi** (aynan shu matnlar):

```python
EQUIPMENT_BASE = ["Kompyuter sinfi", "Proyektor yoki interaktiv doska", "Tarqatma materiallar"]

def objective_for(title, grade):
    return (f"O'quvchilarga «{title}» mavzusini amaliy misollar orqali tushuntirish, "
            f"{grade}-sinf dasturiga mos nazariy bilim va amaliy ko'nikmalarni shakllantirish.")

def theory_for(title):
    return [
        f"Dars «{title}» mavzusiga bag'ishlanadi. Kirish qismida o'tgan dars takrorlanadi va yangi mavzu kundalik hayotdagi misollar bilan bog'lab boshlanadi.",
        "Asosiy tushunchalar doskada yoki taqdimotda bosqichma-bosqich ochib beriladi: ta'rif, asosiy xossalar va qo'llanish sohalari. Har bir tushuncha kamida bitta jonli misol bilan mustahkamlanadi.",
        "Namoyish qismida o'qituvchi mavzuga oid amaliy jarayonni proyektor orqali ko'rsatadi, o'quvchilar esa asosiy qadamlarni daftarga qayd etib boradi.",
        "Yakunida savol-javob o'tkaziladi: o'quvchilar mavzu bo'yicha 2–3 nazorat savoliga og'zaki javob beradi va tushunmagan joylari aniqlanadi.",
    ]

def practice_for(title):
    return [
        f"«{title}» mavzusi bo'yicha o'qituvchi ko'rsatgan amallarni kompyuterda mustaqil takrorlash.",
        "Juftlikda ishlash: tarqatma materialdagi topshiriqni bajarish va natijani sinfdoshi bilan solishtirish.",
        "Mustaqil topshiriq: mavzuga oid kichik masalani yechish va natijani o'qituvchiga ko'rsatish.",
    ]

def homework_for(title):
    return (f"«{title}» mavzusi bo'yicha daftardagi konspektni o'qib kelish va mavzuga oid "
            f"3 ta misolni mustaqil bajarish. Qo'shimcha: mavzu yuzasidan bitta savol tayyorlab kelish.")

def outcomes_for(title):
    return [
        f"«{title}» mavzusidagi asosiy tushunchalarni ta'riflay oladi",
        "Mavzuga oid amaliy topshiriqni mustaqil bajara oladi",
        "Olingan bilimni kundalik misollar bilan bog'lay oladi",
    ]
```

Qo'shimcha qoidalar:
- `order` = shu grade+quarter'dagi maksimal order + 1 (bo'sh bo'lsa 1).
- `status = "draft"`, `videoUrl = ""`, `durationMin` default 45.

### 6.4 Sinf ↔ o'qituvchi sinxronligi

- Sinf yaratish/tahrirlashda `teacherId` beriladi; o'qituvchining `classIds`
  javobi doim classes jadvalidan hisoblanadi (6.2-band 5.2 izohiga qarang).
- Sinf yaratishda UNIQUE(grade, letter) buzilsa 409: `"Bunday sinf allaqachon mavjud"`.
- Sinf o'chirishda unda o'quvchi bo'lsa 400:
  `"Bu sinfda o'quvchilar bor — avval ularni boshqa sinfga o'tkazing"`.
- Sinf o'chirilganda unga tegishli `journal_entries` va `journal_columns` ham o'chiriladi (cascade).

### 6.5 O'qituvchi CRUD

- `login` unikal (users + teachers birgalikda): 409 `"Bu login band — boshqasini tanlang"`.
- Yangi o'qituvchida parol majburiy: 400 `"Yangi o'qituvchi uchun parol kiritilishi shart"`.
- Tahrirlashda parol bo'sh kelsa — eski parol saqlanadi.
- O'qituvchi o'chirilganda sinflari `teacher_id` bilan qoladimi? Frontend hozir
  faqat teacher yozuvini o'chiradi — backend sinflarning `teacher_id` ni NULL/bo'sh
  qilib qo'yishi mumkin (frontend `teacherId` topilmasa «—» ko'rsatadi).

### 6.6 O'quvchi CRUD va rag'bat

- O'quvchi o'chirilganda uning barcha `journal_entries` yozuvlari ham o'chiriladi.
- Rag'bat (`addPoints`): `points` musbat/manfiy bo'lishi mumkin, natija `max(0, ...)`.
  `badgeId` berilsa va o'quvchida yo'q bo'lsa — `badges` ro'yxatiga qo'shiladi (takrorsiz).

### 6.7 Login

- Avval `users`, keyin `teachers` dan qidiriladi (login + parol mos kelishi).
- Topilmasa 401: `"Login yoki parol noto'g'ri"`.
- Teacher uchun sessiya foydalanuvchisi: `role="teacher"`,
  `title="Informatika o'qituvchisi"` (o'zgarmas matn).

---

## 7. API endpointlar

Barcha endpointlar `/api` prefiksi bilan. `🔒` — token talab qilinadi.
Rollar qavsda ko'rsatilgan.

### 7.1 Auth va profil

#### `POST /api/auth/login`
Request:
```json
{ "login": "admin", "password": "admin" }
```
Response 200:
```json
{
  "token": "<JWT>",
  "user": {
    "id": "u-admin", "name": "Aziz Rahmonov", "login": "admin",
    "role": "admin", "title": "Platforma administratori", "photo": ""
  }
}
```
`user` obyekti — frontend'dagi `SessionUser` tipi. 401: `"Login yoki parol noto'g'ri"`.
JWT payload'ida kamida: `sub` (id), `kind` (`user`/`teacher`), `role`.

#### `GET /api/auth/me` 🔒 (hamma rol)
Response: `SessionUser` (yuqoridagi `user` bilan bir xil shakl).
Token yaroqsiz bo'lsa 401 — frontend login sahifasiga qaytaradi.

#### `POST /api/auth/logout` 🔒
Ixtiyoriy (JWT'da shunchaki token o'chiriladi frontend'da). 204 qaytarsa yetarli.

#### `PATCH /api/profile` 🔒 (hamma rol — faqat o'zini)
Request (hamma maydon ixtiyoriy, bo'sh string e'tiborga olinmaydi):
```json
{ "name": "...", "phone": "...", "email": "...", "photo": "data:image/...;base64,...", "password": "..." }
```
`phone`/`email` faqat teacher uchun ma'noli (user'da e'tiborsiz qoldiriladi).
Response 200: yangilangan `SessionUser`. 404: `"Profil topilmadi"`.

#### `GET /api/teachers/{id}/profile` 🔒
Teacher'ning to'liq ma'lumoti (telefon/email ko'rsatish uchun):
```json
{ "id": "t1", "name": "...", "phone": "...", "email": "...", "classIds": ["c-5a"], "login": "karimov", "photo": "" }
```
Topilmasa 200 `null` yoki 404 — frontend null'ni ham ko'taradi.

### 7.2 Darslar

#### `GET /api/lessons/summary` 🔒 (hamma rol)
Sinflar kesimida statistika (`GradeSummary[]`), grade bo'yicha o'sish tartibida:
```json
[ { "grade": 1, "lessonCount": 16, "readyCount": 16 }, ... ]
```

#### `GET /api/lessons?grade=5` 🔒 (hamma rol)
`Lesson[]` — quarter, keyin order bo'yicha tartiblangan. Lesson JSON shakli:
```json
{
  "id": "l-5-1-1", "grade": 5, "quarter": 1, "order": 1,
  "title": "Informatika nima o'rganadi?",
  "authorId": "t1", "authorName": "Dilshod Karimov",
  "objective": "...",
  "theory": ["...", "..."],
  "practice": ["...", "..."],
  "homework": "...",
  "equipment": ["..."],
  "outcomes": ["..."],
  "videoUrl": "",
  "durationMin": 45,
  "status": "ready"
}
```

#### `GET /api/lessons/{id}` 🔒 (hamma rol)
Bitta `Lesson`. 404: `"Dars topilmadi"`.

#### `POST /api/lessons` 🔒 (admin, teacher)
Request:
```json
{ "grade": 5, "quarter": 2, "title": "Scratchda animatsiya", "durationMin": 45 }
```
Backend 6.3-band bo'yicha shablon tanani yaratadi, muallifni tokendan oladi.
Response 201: to'liq `Lesson`.

#### `PATCH /api/lessons/{id}` 🔒 (admin, teacher)
Request — `Lesson`ning istalgan qism-maydonlari (frontend yuboradi):
`title, objective, theory[], practice[], homework, equipment[], outcomes[],
durationMin, status, videoUrl`. `id/grade/quarter/order/authorId/authorName`
o'zgartirilmaydi (kelsa e'tiborsiz). Response 200: yangilangan `Lesson`.
404: `"Dars topilmadi"`.

#### `DELETE /api/lessons/{id}` 🔒 (admin yoki muallif)
6.2-band qoidalari. Muvaffaqiyatda 204.

#### `GET /api/quarters?grade=5` 🔒 (hamma rol)
`QuarterInfo[]` (quarter bo'yicha tartiblangan):
```json
[ { "grade": 5, "quarter": 1, "skills": ["...", "..."] }, ... ]
```

### 7.3 Sinflar

#### `GET /api/classes` 🔒 (hamma rol)
`ClassGroup[]`, grade→letter tartibida:
```json
[ { "id": "c-3a", "grade": 3, "letter": "A", "teacherId": "t2" }, ... ]
```

#### `POST /api/classes` 🔒 (admin) — yangi sinf
Request: `{ "grade": 5, "letter": "B", "teacherId": "t1" }` → 201 `ClassGroup`.
409: `"Bunday sinf allaqachon mavjud"`.

#### `PATCH /api/classes/{id}` 🔒 (admin)
Request: o'sha maydonlar → 200 `ClassGroup`. 404: `"Sinf topilmadi"`.

#### `DELETE /api/classes/{id}` 🔒 (admin)
6.4-band qoidasi (o'quvchi bo'lsa 400). Muvaffaqiyatda 204.

### 7.4 O'qituvchilar

#### `GET /api/teachers` 🔒 (hamma rol)
`Teacher[]` (password'siz, `classIds` hisoblangan):
```json
[ { "id": "t1", "name": "Dilshod Karimov", "phone": "+998 90 123 45 67",
    "email": "d.karimov@maktab.uz", "classIds": ["c-5a", "c-7b"],
    "login": "karimov", "photo": "" }, ... ]
```

#### `POST /api/teachers` 🔒 (admin)
Request:
```json
{ "name": "...", "phone": "...", "email": "...", "classIds": [], "login": "yangi", "password": "1234" }
```
6.5-band qoidalari. Response 201: `Teacher`.

#### `PATCH /api/teachers/{id}` 🔒 (admin)
O'sha maydonlar, `password` ixtiyoriy (bo'sh = o'zgarmaydi). 404: `"O'qituvchi topilmadi"`.
`classIds` kelsa — shu sinflarning `teacher_id` si yangilanadi (eski bog'lardan chiqariladi).

#### `DELETE /api/teachers/{id}` 🔒 (admin) → 204.

### 7.5 O'quvchilar va reyting

#### `GET /api/students?classId=c-5a` 🔒 (hamma rol)
`classId` bo'lmasa — hammasi. `Student[]`:
```json
[ { "id": "s1", "name": "Aziza Rustamova", "classId": "c-3a", "points": 120, "badges": ["star"] }, ... ]
```

#### `POST /api/students` 🔒 (admin, teacher)
Request: `{ "name": "...", "classId": "c-5a", "points": 0, "badges": [] }` → 201 `Student`.

#### `PATCH /api/students/{id}` 🔒 (admin, teacher)
O'sha maydonlar → 200 `Student`. 404: `"O'quvchi topilmadi"`.

#### `DELETE /api/students/{id}` 🔒 (admin, teacher) → 204 (jurnal yozuvlari ham o'chadi).

#### `POST /api/students/{id}/points` 🔒 (admin, teacher) — rag'batlantirish
Request:
```json
{ "points": 10, "badgeId": "star" }
```
`badgeId` ixtiyoriy. Response 200: yangilangan `Student`. 404: `"O'quvchi topilmadi"`.

#### `GET /api/badges` — statik nishonlar lug'ati (5.9-band). Token talab qilinmasa ham bo'ladi.

### 7.6 Jurnal

#### `GET /api/journal?classId=c-5a` 🔒 (hamma rol)
`JournalEntry[]`:
```json
[ { "id": "j-s9-2026-05-12", "studentId": "s9", "classId": "c-5a",
    "date": "2026-05-12", "grade": 4, "attendance": "keldi" }, ... ]
```

#### `GET /api/journal/columns?classId=c-5a` 🔒 (hamma rol)
`JournalColumn[]` sana bo'yicha o'sish tartibida:
```json
[ { "id": "jc-c-5a-2026-05-12", "classId": "c-5a", "date": "2026-05-12", "lessonId": "l-5-4-1" }, ... ]
```

#### `POST /api/journal/columns` 🔒 (admin; teacher — faqat o'z sinfi)
Request: `{ "classId": "c-5a", "date": "2026-06-09", "lessonId": "l-5-4-2" }`
Response 201: `JournalColumn`. Dublikat sana 409:
`"Bu sana uchun dars allaqachon ochilgan"`. Ruxsat bo'lmasa 403.

#### `PUT /api/journal/cell` 🔒 (admin; teacher — faqat o'z sinfi) — **upsert**
Request:
```json
{ "classId": "c-5a", "studentId": "s9", "date": "2026-05-12",
  "grade": 5, "attendance": "keldi" }
```
`grade`: 2–5 yoki `null`. `grade` yuborilmasa eski qiymat saqlanadi,
`attendance` yuborilmasa eskisi (yo'q bo'lsa `"keldi"`).
Ball deltasi 6.1-band bo'yicha qo'llanadi. Response 200:
```json
{ "entry": { ...JournalEntry }, "student": { ...Student } }
```
404: `"O'quvchi topilmadi"`.

---

## 8. Seed (boshlang'ich) ma'lumotlar

Backend birinchi ishga tushganda quyidagilarni yaratishi kerak (frontend'dagi
`src/data/seed.ts` va `src/data/curriculum.ts` fayllaridan birebir ko'chiring):

1. **Hisoblar:**
   - admin: login `admin` / parol `admin` — Aziz Rahmonov, «Platforma administratori»
   - viewer: `rahbar` / `rahbar` — Nodira Alimova, «O'quv ishlari bo'yicha direktor o'rinbosari»
   - teachers: `karimov`/`1234` (Dilshod Karimov), `yusupova`/`1234` (Malika Yusupova),
     `toshpulatov`/`1234` (Jasur Toshpo'latov)
2. **Sinflar:** 3-A (t2), 5-A (t1), 7-B (t1), 9-A (t3).
3. **O'quv dasturi:** `curriculum.ts` — 1–11-sinf × 4 chorak × 4 mavzu = **176 dars**.
   Har biriga 6.3-shablon qo'llanadi, `status="ready"`; uchta boyitilgan dars
   (`l-5-1-1`, `l-7-2-1`, `l-5-3-1`) uchun `seed.ts`dagi `RICH` matnlari olinadi.
   **Muallif:** shu sinf (grade) biriktirilgan o'qituvchi (3→t2, 5→t1, 7→t1, 9→t3),
   sinfi yo'q grade'lar → admin.
4. **QuarterInfos:** har grade+quarter uchun `skills = mavzular.map(t => "«{t}» mavzusi bo'yicha bilim va amaliy ko'nikma")`.
5. **O'quvchilar:** `seed.ts`dagi ism ro'yxatlari (har sinfda 8–10 nafar), boshlang'ich
   ball va nishonlar deterministik formula bilan (ixtiyoriy — istalgan boshlang'ich qiymat bo'ladi).
6. **Jurnal:** har sinfga 4 ta o'tilgan sana (`2026-05-12`, `05-19`, `05-26`, `06-02`),
   ustunlar 4-chorak darslariga bog'langan, katakchalar to'ldirilgan (ixtiyoriy).

---

## 9. `api.ts` funksiyalari ↔ endpointlar jadvali

| Frontend funksiya | Endpoint |
|---|---|
| `login(login, password)` | `POST /api/auth/login` |
| `getSessionUser()` | `GET /api/auth/me` |
| `logout()` | tokenni o'chirish (+ `POST /api/auth/logout`) |
| `updateProfile(patch)` | `PATCH /api/profile` |
| `getTeacherProfile(id)` | `GET /api/teachers/{id}/profile` |
| `getGradeSummaries()` | `GET /api/lessons/summary` |
| `getLessonsByGrade(grade)` | `GET /api/lessons?grade=` |
| `getLesson(id)` | `GET /api/lessons/{id}` |
| `addLesson(input)` | `POST /api/lessons` |
| `updateLesson(id, patch)` | `PATCH /api/lessons/{id}` |
| `deleteLesson(id)` | `DELETE /api/lessons/{id}` |
| `getQuarterInfos(grade)` | `GET /api/quarters?grade=` |
| `getClasses()` | `GET /api/classes` |
| `saveClass(data)` | `POST /api/classes` yoki `PATCH /api/classes/{id}` (`data.id` bor-yo'qligiga qarab) |
| `deleteClass(id)` | `DELETE /api/classes/{id}` |
| `getTeachers()` | `GET /api/teachers` |
| `saveTeacher(data)` | `POST /api/teachers` yoki `PATCH /api/teachers/{id}` |
| `deleteTeacher(id)` | `DELETE /api/teachers/{id}` |
| `getStudents(classId?)` | `GET /api/students?classId=` |
| `saveStudent(data)` | `POST /api/students` yoki `PATCH /api/students/{id}` |
| `deleteStudent(id)` | `DELETE /api/students/{id}` |
| `addPoints(studentId, points, badgeId?)` | `POST /api/students/{id}/points` |
| `getBadgeDefs()` | `GET /api/badges` (yoki frontendda konstanta qoladi) |
| `getJournal(classId)` | `GET /api/journal?classId=` |
| `getJournalColumns(classId)` | `GET /api/journal/columns?classId=` |
| `addJournalColumn(classId, date, lessonId)` | `POST /api/journal/columns` |
| `setJournalCell(classId, studentId, date, patch)` | `PUT /api/journal/cell` |

**Frontend migratsiyasi:** faqat `src/services/api.ts` qayta yoziladi — har funksiya
`fetch(BASE_URL + ..., { headers: { Authorization: 'Bearer ' + token } })` ga
aylanadi; token `localStorage`da saqlanadi; xatoda `throw new Error((await res.json()).detail)`.

---

## 10. Tavsiya etilgan loyiha strukturasi (FastAPI)

```
backend/
├── app/
│   ├── main.py              # FastAPI app, CORS, router'lar
│   ├── config.py            # .env: DATABASE_URL, JWT_SECRET, TOKEN_TTL
│   ├── database.py          # engine, SessionLocal, Base
│   ├── models/              # SQLAlchemy modellari (5-band jadvallari)
│   ├── schemas/             # Pydantic (camelCase alias, 7-band JSON shakllari)
│   ├── routers/
│   │   ├── auth.py          # login, me, profile
│   │   ├── lessons.py       # lessons + summary + quarters
│   │   ├── classes.py
│   │   ├── teachers.py
│   │   ├── students.py      # students + points + badges
│   │   └── journal.py       # entries + columns + cell
│   ├── services/
│   │   ├── points.py        # GRADE_POINTS, cell_points, delta (6.1)
│   │   └── lesson_template.py  # 6.3 shablon generatorlari
│   ├── deps.py              # get_db, get_current_user, require_roles(...)
│   └── seed.py              # 8-band boshlang'ich ma'lumotlar
├── alembic/
├── requirements.txt         # fastapi, uvicorn, sqlalchemy, alembic, pyjwt, passlib[bcrypt], pydantic-settings
└── .env
```

Foydali parchalar:

```python
# schemas/base.py — camelCase moslik
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)
```

```python
# deps.py — rol tekshiruvi
def require_roles(*roles):
    def dep(user = Depends(get_current_user)):
        if user.role not in roles:
            raise HTTPException(403, "Bu amal uchun ruxsat yo'q")
        return user
    return dep
```

```python
# journal cell ruxsati: admin istalgan sinf, teacher faqat o'ziniki
def assert_can_grade(user, klass):
    if user.role == "admin":
        return
    if user.role == "teacher" and klass.teacher_id == user.id:
        return
    raise HTTPException(403, "Bu sinfda baholash huquqingiz yo'q")
```

---

## 11. Qabul qilish checklisti (backend tayyor deb hisoblash sharti)

- [ ] `admin/admin`, `rahbar/rahbar`, `karimov/1234` bilan login ishlaydi; noto'g'ri parolda o'zbekcha xato
- [ ] `GET /api/lessons/summary` 11 ta grade, jami 176 dars qaytaradi
- [ ] Teacher yangi dars yaratsa — `authorId` o'ziniki; darsda «O'chirish» ishlaydi
- [ ] Teacher boshqa muallif darsini o'chira olmaydi (403), admin — hammasini o'chiradi
- [ ] Jurnalga bog'langan darsni hech kim o'chira olmaydi (400)
- [ ] Jurnal katakchasi saqlanganda o'quvchi bali to'g'ri delta bilan o'zgaradi (5→+15+2 va h.k.)
- [ ] Bir sanaga ikkinchi marta «dars o'tish» — 409
- [ ] Teacher faqat o'z sinfida baho qo'ya oladi, viewer hech qayerda yoza olmaydi
- [ ] Sinf/o'qituvchi/o'quvchi CRUD barcha o'zbekcha xato xabarlari bilan ishlaydi
- [ ] Barcha JSON javoblar camelCase, sanalar `YYYY-MM-DD`, parollar hech qayerda qaytmaydi
- [ ] CORS: `http://localhost:5173` dan so'rovlar o'tadi
- [ ] Seed: yuqoridagi barcha demo ma'lumotlar bilan birinchi ishga tushishda to'ldiriladi
