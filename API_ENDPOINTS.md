# MetodikaIT — API hujjati (frontend uchun)

Bu fayl backenddagi **barcha** endpointlarni tavsiflaydi: URL, nima qilishi,
so‘rov tanasi (body), javob va xatolar. Frontendni ulashda shu hujjatga tayaning.

---

## 0. Umumiy qoidalar

- **Bazaviy URL (dev):** `http://localhost:8000`
- **Barcha endpointlar prefiksi:** `/api`
- **Format:** JSON. Maydon nomlari **camelCase** (`authorName`, `classId`, `durationMin` ...).
- **Sanalar:** `"YYYY-MM-DD"` string (masalan `"2026-05-12"`).
- **id lar:** doim string.
- **Rasm (`photo`):** base64 data-URL string (`"data:image/png;base64,..."`) yoki `""`.
- **Parol** hech qachon javobda qaytmaydi.

### Autentifikatsiya

Login qilgach `token` olasiz va uni har bir 🔒 so‘rovda header sifatida yuborasiz:

```
Authorization: Bearer <token>
```

Tokenni frontendda `localStorage` da saqlang. Token yaroqsiz/muddati o‘tgan bo‘lsa
`401` qaytadi — login sahifasiga qайtaring.

### Xato formati

Har qanday xato quyidagi ko‘rinishda keladi (xabar o‘zbekcha — to‘g‘ridan-to‘g‘ri
foydalanuvchiga ko‘rsatsa bo‘ladi):

```json
{ "detail": "Login yoki parol noto'g'ri" }
```

| Status | Ma'nosi |
|---|---|
| `400` | Validatsiya / biznes qoida buzildi |
| `401` | Token yo‘q / yaroqsiz |
| `403` | Ruxsat yo‘q |
| `404` | Topilmadi |
| `409` | Konflikt / dublikat |

Frontendda: `if (!res.ok) throw new Error((await res.json()).detail)`.

### Rollar

`admin` — hammasi · `teacher` — darslar/jurnal/o‘quvchi/reyting · `viewer` — faqat ko‘rish.

### Demo hisoblar

| Rol | Login | Parol |
|---|---|---|
| admin | `admin` | `admin` |
| viewer | `rahbar` | `rahbar` |
| teacher | `karimov` | `1234` |
| teacher | `yusupova` | `1234` |
| teacher | `toshpulatov` | `1234` |

---

## 1. Auth va profil

### 🔓 POST `/api/auth/login`
Tizimga kirish. Avval adminlar/viewerlar, keyin o‘qituvchilar bo‘yicha qidiradi.

**Body:**
```json
{ "login": "admin", "password": "admin" }
```
**Javob 200:**
```json
{
  "token": "<JWT>",
  "user": {
    "id": "u-admin", "name": "Aziz Rahmonov", "login": "admin",
    "role": "admin", "title": "Platforma administratori", "photo": ""
  }
}
```
**Xato:** `401 "Login yoki parol noto'g'ri"`

> Eslatma: o‘qituvchi kirsa `role: "teacher"`, `title: "Informatika o'qituvchisi"`.

---

### 🔒 GET `/api/auth/me`
Joriy foydalanuvchini qaytaradi (token orqali). Sahifa yangilanganda sessiyani tiklash uchun.

**Body:** yo‘q
**Javob 200:** `SessionUser` (yuqoridagi `user` bilan bir xil shakl)
**Xato:** `401` — token yaroqsiz.

---

### 🔒 POST `/api/auth/logout`
Chiqish. JWT stateless bo‘lgani uchun frontend shunchaki tokenni o‘chiradi.

**Body:** yo‘q
**Javob:** `204` (tana yo‘q)

---

### 🔒 PATCH `/api/profile`  *(har qanday rol — faqat o‘zini)*
Shaxsiy profilni yangilaydi. **Hamma maydon ixtiyoriy**, bo‘sh string e’tiborga olinmaydi.

**Body:** (istalgan qism)
```json
{
  "name": "...", "phone": "...", "email": "...",
  "photo": "data:image/png;base64,...", "password": "yangiParol"
}
```
> `phone`/`email` faqat o‘qituvchi uchun ta’sir qiladi. `password` bo‘sh bo‘lsa eski parol qoladi.

**Javob 200:** yangilangan `SessionUser`
**Xato:** `404 "Profil topilmadi"`

---

## 2. Darslar

### 🔒 GET `/api/lessons/summary`  *(hamma rol)*
Sinf (grade) kesimida statistika — 1–11 gacha hammasi qaytadi (bo‘sh grade’lar 0 bilan).

**Javob 200:**
```json
[ { "grade": 1, "lessonCount": 0, "readyCount": 0 },
  { "grade": 5, "lessonCount": 4, "readyCount": 4 } ]
```

---

### 🔒 GET `/api/lessons?grade=5`  *(hamma rol)*
Berilgan grade’ning barcha darslari (quarter, keyin order bo‘yicha tartiblangan).

**Query:** `grade` (int, majburiy)
**Javob 200:** `Lesson[]`. Bitta `Lesson` shakli:
```json
{
  "id": "l-5-1-1", "grade": 5, "quarter": 1, "order": 1,
  "title": "Informatika nima o'rganadi?",
  "authorId": "t1", "authorName": "Dilshod Karimov",
  "objective": "...",
  "theory": ["...", "..."],
  "practice": ["...", "..."],
  "homework": "...",
  "equipment": ["Kompyuter sinfi", "..."],
  "outcomes": ["...", "..."],
  "videoUrl": "",
  "durationMin": 45,
  "status": "ready"
}
```
> `status`: `"ready"` yoki `"draft"`.

---

### 🔒 GET `/api/lessons/{id}`  *(hamma rol)*
Bitta darsni qaytaradi.

**Javob 200:** `Lesson`
**Xato:** `404 "Dars topilmadi"`

---

### 🔒 POST `/api/lessons`  *(admin, teacher)*
Yangi dars yaratadi. Siz faqat asosiy maydonlarni yuborasiz — qolgan tana
(objective, theory, practice, homework, equipment, outcomes) backendda **shablon
bo‘yicha avtomatik** to‘ladi. Muallif tokendan olinadi (body’da yubormaysiz).

**Body:**
```json
{ "grade": 5, "quarter": 2, "title": "Scratchda animatsiya", "durationMin": 45 }
```
> `durationMin` ixtiyoriy (default 45). Yangi dars `status: "draft"`, `order`
> avtomatik hisoblanadi.

**Javob 201:** to‘liq `Lesson`

---

### 🔒 PATCH `/api/lessons/{id}`  *(admin, teacher)*
Darsni tahrirlaydi. Faqat yuborilgan maydonlar o‘zgaradi.
`id/grade/quarter/order/authorId/authorName` o‘zgartirilmaydi (yuborilsa e’tiborsiz).

**Body:** (istalgan qism)
```json
{
  "title": "...", "objective": "...",
  "theory": ["..."], "practice": ["..."],
  "homework": "...", "equipment": ["..."], "outcomes": ["..."],
  "durationMin": 45, "status": "ready", "videoUrl": "https://..."
}
```
**Javob 200:** yangilangan `Lesson`
**Xato:** `404 "Dars topilmadi"`

---

### 🔒 DELETE `/api/lessons/{id}`  *(admin yoki muallif)*
Darsni o‘chiradi. Faqat **admin** yoki **darsni yaratgan** o‘qituvchi o‘chira oladi.

**Javob:** `204`
**Xatolar:**
- `404 "Dars topilmadi"`
- `403 "Bu darsni faqat admin yoki uni yaratgan o'qituvchi o'chira oladi"`
- `400 "Bu dars jurnalda o'tilgan darslarga biriktirilgan — avval jurnalni tekshiring"`

---

### 🔒 GET `/api/quarters?grade=5`  *(hamma rol)*
Berilgan grade uchun chorak ko‘nikmalari (quarter bo‘yicha tartiblangan).

**Query:** `grade` (int, majburiy)
**Javob 200:**
```json
[ { "grade": 5, "quarter": 1, "skills": ["...", "..."] } ]
```

---

## 3. Sinflar

### 🔒 GET `/api/classes`  *(hamma rol)*
Barcha sinflar (grade → letter bo‘yicha tartiblangan).

**Javob 200:**
```json
[ { "id": "c-3a", "grade": 3, "letter": "A", "teacherId": "t2" } ]
```
> `teacherId` `null` bo‘lishi mumkin (rahbari o‘chirilgan sinf).

---

### 🔒 POST `/api/classes`  *(faqat admin)*
Yangi sinf. `id` avtomatik `c-{grade}{letter}` ko‘rinishida yaratiladi.

**Body:**
```json
{ "grade": 5, "letter": "B", "teacherId": "t1" }
```
> `teacherId` ixtiyoriy (`null` bo‘lishi mumkin).

**Javob 201:** `ClassGroup`
**Xato:** `409 "Bunday sinf allaqachon mavjud"` (grade+letter takrorlansa)

---

### 🔒 PATCH `/api/classes/{id}`  *(faqat admin)*
Sinfni tahrirlaydi (grade, letter, teacherId).

**Body:** (istalgan qism) `{ "grade": 5, "letter": "B", "teacherId": "t2" }`
**Javob 200:** `ClassGroup`
**Xatolar:** `404 "Sinf topilmadi"`, `409 "Bunday sinf allaqachon mavjud"`

---

### 🔒 DELETE `/api/classes/{id}`  *(faqat admin)*
Sinfni o‘chiradi. Sinfda o‘quvchi bo‘lsa o‘chirilmaydi. O‘chsa, unga tegishli
jurnal ustunlari va yozuvlari ham o‘chadi.

**Javob:** `204`
**Xatolar:**
- `404 "Sinf topilmadi"`
- `400 "Bu sinfda o'quvchilar bor — avval ularni boshqa sinfga o'tkazing"`

---

## 4. O‘qituvchilar

### 🔒 GET `/api/teachers`  *(hamma rol)*
Barcha o‘qituvchilar (ism bo‘yicha tartiblangan). `classIds` — o‘qituvchiga
biriktirilgan sinflar (avtomatik hisoblanadi). Parol qaytmaydi.

**Javob 200:**
```json
[ { "id": "t1", "name": "Dilshod Karimov", "phone": "+998 90 123 45 67",
    "email": "d.karimov@maktab.uz", "classIds": ["c-5a", "c-7b"],
    "login": "karimov", "photo": "" } ]
```

---

### 🔒 GET `/api/teachers/{id}/profile`  *(hamma rol)*
Bitta o‘qituvchining to‘liq ma’lumoti (telefon/email ko‘rsatish uchun).

**Javob 200:** `Teacher` obyekti **yoki** `null` (topilmasa).

---

### 🔒 POST `/api/teachers`  *(faqat admin)*
Yangi o‘qituvchi. Parol **majburiy**. `login` butun tizimda (admin+o‘qituvchi)
noyob bo‘lishi kerak. `classIds` berilsa — o‘sha sinflar shu o‘qituvchiga o‘tadi.

**Body:**
```json
{
  "name": "Yangi O'qituvchi", "phone": "+998 ...", "email": "...",
  "classIds": [], "login": "yangi", "password": "1234"
}
```
**Javob 201:** `Teacher`
**Xatolar:**
- `400 "Yangi o'qituvchi uchun parol kiritilishi shart"`
- `409 "Bu login band — boshqasini tanlang"`

---

### 🔒 PATCH `/api/teachers/{id}`  *(faqat admin)*
Tahrirlaydi. `password` ixtiyoriy — **bo‘sh bo‘lsa eski parol saqlanadi**.
`classIds` yuborilsa — shu ro‘yxatdagi sinflar biriktiriladi, qolganidan chiqariladi.

**Body:** (istalgan qism)
```json
{ "name": "...", "phone": "...", "email": "...",
  "login": "...", "password": "", "classIds": ["c-5a"] }
```
**Javob 200:** `Teacher`
**Xatolar:** `404 "O'qituvchi topilmadi"`, `409 "Bu login band — boshqasini tanlang"`

---

### 🔒 DELETE `/api/teachers/{id}`  *(faqat admin)*
O‘qituvchini o‘chiradi. Sinflari qoladi, ularning `teacherId` si `null` bo‘ladi.

**Javob:** `204`
**Xato:** `404 "O'qituvchi topilmadi"`

---

## 5. O‘quvchilar va reyting

### 🔒 GET `/api/students?classId=c-5a`  *(hamma rol)*
O‘quvchilar ro‘yxati. `classId` berilmasa — hammasi qaytadi.

**Query:** `classId` (ixtiyoriy)
**Javob 200:**
```json
[ { "id": "s-5a-1", "name": "Ozoda Karimova", "classId": "c-5a",
    "points": 40, "badges": ["star"] } ]
```

---

### 🔒 POST `/api/students`  *(admin, teacher)*
Yangi o‘quvchi. `points` manfiy bo‘lsa 0 ga tenglashtiriladi, `badges` takrorsizlanadi.

**Body:**
```json
{ "name": "Yangi O'quvchi", "classId": "c-5a", "points": 0, "badges": [] }
```
> `points` va `badges` ixtiyoriy (default `0` / `[]`).

**Javob 201:** `Student`

---

### 🔒 PATCH `/api/students/{id}`  *(admin, teacher)*
Tahrirlaydi (ism, sinf, ball, nishonlar).

**Body:** (istalgan qism) `{ "name": "...", "classId": "c-7b", "points": 100, "badges": ["star"] }`
**Javob 200:** `Student`
**Xato:** `404 "O'quvchi topilmadi"`

---

### 🔒 DELETE `/api/students/{id}`  *(admin, teacher)*
O‘quvchini o‘chiradi. Uning barcha jurnal yozuvlari ham o‘chadi.

**Javob:** `204`
**Xato:** `404 "O'quvchi topilmadi"`

---

### 🔒 POST `/api/students/{id}/points`  *(admin, teacher)* — rag‘batlantirish
Ball qo‘shadi/ayiradi va ixtiyoriy nishon beradi.

**Body:**
```json
{ "points": 10, "badgeId": "star" }
```
> `points` musbat yoki manfiy bo‘lishi mumkin; natija `0` dan pastga tushmaydi.
> `badgeId` ixtiyoriy — o‘quvchida bo‘lmasa qo‘shiladi (takrorsiz).

**Javob 200:** yangilangan `Student`
**Xato:** `404 "O'quvchi topilmadi"`

---

### 🔓 GET `/api/badges`
Nishonlar lug‘ati (statik). Token talab qilinmaydi.

**Javob 200:**
```json
[
  { "id": "star",    "name": "Yulduzcha",        "description": "Darsda 5 baho olgani uchun" },
  { "id": "streak",  "name": "Faol ishtirokchi", "description": "5 dars ketma-ket faol qatnashgani uchun" },
  { "id": "project", "name": "Loyiha ustasi",    "description": "Yakuniy loyihani a'lo himoya qilgani uchun" },
  { "id": "helper",  "name": "Yordamchi",        "description": "Sinfdoshlariga yordam bergani uchun" },
  { "id": "speed",   "name": "Tezkor",           "description": "Amaliy topshiriqni birinchi bo'lib bajargani uchun" }
]
```

---

## 6. Jurnal (baho + davomat)

### 🔒 GET `/api/journal?classId=c-5a`  *(hamma rol)*
Sinfning barcha baho/davomat katakchalari.

**Query:** `classId` (majburiy)
**Javob 200:**
```json
[ { "id": "j-s-5a-1-2026-05-12", "studentId": "s-5a-1", "classId": "c-5a",
    "date": "2026-05-12", "grade": 4, "attendance": "keldi" } ]
```
> `grade`: `2–5` yoki `null`. `attendance`: `"keldi"` | `"kelmadi"` | `"kechikdi"`.

---

### 🔒 GET `/api/journal/columns?classId=c-5a`  *(hamma rol)*
O‘tilgan darslar ustunlari (sana bo‘yicha o‘sish tartibida).

**Query:** `classId` (majburiy)
**Javob 200:**
```json
[ { "id": "jc-c-5a-2026-05-12", "classId": "c-5a",
    "date": "2026-05-12", "lessonId": "l-5-1-1" } ]
```

---

### 🔒 POST `/api/journal/columns`  *(admin; teacher — faqat o‘z sinfi)* — «dars o‘tish»
Berilgan sanaga yangi ustun (o‘tilgan dars) ochadi.

**Body:**
```json
{ "classId": "c-5a", "date": "2026-06-09", "lessonId": "l-5-1-2" }
```
**Javob 201:** `JournalColumn`
**Xatolar:**
- `404 "Sinf topilmadi"`
- `403 "Bu sinfda baholash huquqingiz yo'q"` (begona sinf)
- `409 "Bu sana uchun dars allaqachon ochilgan"`

---

### 🔒 PUT `/api/journal/cell`  *(admin; teacher — faqat o‘z sinfi)* — **upsert**
Bitta katakchani (baho + davomat) yozadi yoki yangilaydi. O‘quvchining reyting
bali avtomatik qayta hisoblanadi.

**Body:**
```json
{ "classId": "c-5a", "studentId": "s-5a-1", "date": "2026-05-12",
  "grade": 5, "attendance": "keldi" }
```
Qoidalar:
- `grade`: `2–5` yoki `null`. **Yuborilmasa** eski qiymat saqlanadi; `null`
  yuborilsa baho o‘chadi.
- `attendance` yuborilmasa eskisi (yoki `"keldi"`) qoladi.
- `attendance: "kelmadi"` bo‘lsa `grade` avtomatik `null` bo‘ladi.

**Ball formulasi (avtomatik):**
`baho: 5→+15, 4→+10, 3→+5, 2→0` · `davomat: keldi→+2, kechikdi→+1, kelmadi→0`.
Katak qayta yozilsa eski ball ayirilib, yangisi qo‘shiladi (ball `0` dan pastga tushmaydi).

**Javob 200:**
```json
{
  "entry":   { "id": "...", "studentId": "s-5a-1", "classId": "c-5a",
               "date": "2026-05-12", "grade": 5, "attendance": "keldi" },
  "student": { "id": "s-5a-1", "name": "...", "classId": "c-5a",
               "points": 57, "badges": ["star"] }
}
```
**Xatolar:** `404 "Sinf topilmadi"`, `404 "O'quvchi topilmadi"`, `403 "Bu sinfda baholash huquqingiz yo'q"`

---

## 7. Tez ma’lumotnoma (jadval)

| Metod | URL | Rol | Nima qiladi |
|---|---|---|---|
| POST | `/api/auth/login` | 🔓 | Kirish, token beradi |
| GET | `/api/auth/me` | 🔒 | Joriy foydalanuvchi |
| POST | `/api/auth/logout` | 🔒 | Chiqish (204) |
| PATCH | `/api/profile` | 🔒 | O‘z profilini tahrirlash |
| GET | `/api/lessons/summary` | 🔒 | Grade kesimida statistika |
| GET | `/api/lessons?grade=` | 🔒 | Grade darslari |
| GET | `/api/lessons/{id}` | 🔒 | Bitta dars |
| POST | `/api/lessons` | admin, teacher | Yangi dars |
| PATCH | `/api/lessons/{id}` | admin, teacher | Darsni tahrirlash |
| DELETE | `/api/lessons/{id}` | admin/muallif | Darsni o‘chirish |
| GET | `/api/quarters?grade=` | 🔒 | Chorak ko‘nikmalari |
| GET | `/api/classes` | 🔒 | Sinflar |
| POST | `/api/classes` | admin | Yangi sinf |
| PATCH | `/api/classes/{id}` | admin | Sinfni tahrirlash |
| DELETE | `/api/classes/{id}` | admin | Sinfni o‘chirish |
| GET | `/api/teachers` | 🔒 | O‘qituvchilar |
| GET | `/api/teachers/{id}/profile` | 🔒 | O‘qituvchi profili |
| POST | `/api/teachers` | admin | Yangi o‘qituvchi |
| PATCH | `/api/teachers/{id}` | admin | O‘qituvchini tahrirlash |
| DELETE | `/api/teachers/{id}` | admin | O‘qituvchini o‘chirish |
| GET | `/api/students?classId=` | 🔒 | O‘quvchilar |
| POST | `/api/students` | admin, teacher | Yangi o‘quvchi |
| PATCH | `/api/students/{id}` | admin, teacher | O‘quvchini tahrirlash |
| DELETE | `/api/students/{id}` | admin, teacher | O‘quvchini o‘chirish |
| POST | `/api/students/{id}/points` | admin, teacher | Ball/nishon berish |
| GET | `/api/badges` | 🔓 | Nishonlar lug‘ati |
| GET | `/api/journal?classId=` | 🔒 | Jurnal katakchalari |
| GET | `/api/journal/columns?classId=` | 🔒 | Jurnal ustunlari |
| POST | `/api/journal/columns` | admin/o‘z sinfi | «Dars o‘tish» ustuni |
| PUT | `/api/journal/cell` | admin/o‘z sinfi | Baho/davomat (upsert) |

---

## 8. Frontendda ulash namunasi

```ts
const BASE = "http://localhost:8000";

async function api(path: string, options: RequestInit = {}) {
  const token = localStorage.getItem("token");
  const res = await fetch(BASE + path, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });
  if (res.status === 204) return null;
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Xatolik yuz berdi");
  return data;
}

// Misollar:
const { token, user } = await api("/api/auth/login", {
  method: "POST",
  body: JSON.stringify({ login: "admin", password: "admin" }),
});
localStorage.setItem("token", token);

const lessons = await api("/api/lessons?grade=5");
```

> **Interaktiv hujjat:** server ishga tushgach `http://localhost:8000/docs`
> (Swagger UI) da barcha endpointlarni jonli sinab ko‘rish mumkin.
