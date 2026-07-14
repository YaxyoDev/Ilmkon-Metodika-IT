# cPanel'ga deploy qilish (Passenger / "Setup Python App")

Bu backend — **FastAPI (ASGI)**. cPanel esa **WSGI** kutadi, shuning uchun
`passenger_wsgi.py` fayli orqali ulaymiz (repoda mavjud). Quyidagi tartibda
qiling — natijada 500 xato bo'lmaydi va baza avtomatik yaratilib to'ladi.

## 1. Kodni serverga olib chiqish

- cPanel → **Git Version Control** orqali reponi klon qiling
  (`https://github.com/YaxyoDev/Ilmkon-Metodika-IT.git`), yoki
- Fayllarni qo'lda `~/ilmkon` kabi katalogga yuklang.

## 2. Python App yaratish

cPanel → **Setup Python App** → **Create Application**:

| Maydon | Qiymat |
|---|---|
| Python version | 3.10+ (3.11/3.12 tavsiya) |
| Application root | repo joylashgan katalog (masalan `ilmkon`) |
| Application URL | domen/subdomen (masalan `api.ilmkon-metodika.uz`) |
| Application startup file | `passenger_wsgi.py` |
| Application Entry point | `application` |

> ⚠️ **Muhim:** startup file `main.py` EMAS, `passenger_wsgi.py` bo'lishi shart.
> Entry point `app` EMAS, `application` bo'lishi shart. Aks holda ASGI ilova
> WSGI deb yuklanadi va har so'rovda **500** chiqadi.

## 3. Kutubxonalarni o'rnatish

Setup Python App sahifasida **"Run Pip Install"** tugmasi bilan yoki terminalda
(virtualenv faollashtirilgan holda):

```bash
pip install -r requirements.txt
```

`a2wsgi` (ASGI→WSGI ko'prigi) `requirements.txt` da bor — albatta o'rnatilsin.

## 4. (ixtiyoriy) Sozlamalar — `.env`

`.env` git'ga kirmaydi. Standart qiymatlar bilan ilova ishlayveradi, lekin
production uchun tavsiya:

```bash
cp .env.example .env
# .env ichida JWT_SECRET ni o'zingizning tasodifiy qiymatingizga almashtiring
```

Baza standart holatda loyiha ildizidagi **SQLite** fayl (`metodika.db`) —
qo'shimcha MySQL/PostgreSQL server sozlash SHART EMAS. Ilova birinchi ishga
tushganda faylni avtomatik yaratadi, demo ma'lumot va admin hisobini to'ldiradi.

## 5. Restart

Setup Python App → **Restart**. (Passenger `passenger_wsgi.py` ni qayta
yuklaydi; import paytida `init_db()` ishlab, jadvallar va seed tayyorlanadi.)

## 6. Tekshirish

```bash
BASE=https://<sizning-domeningiz>

# Login — 200 va token qaytishi kerak
curl -s -X POST $BASE/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"login":"yaxyo","password":"1710"}'
```

`{"token":"...","user":{...}}` qaytsa — backend to'liq ishlayapti.

## Standart hisoblar

| Rol | Login | Parol |
|---|---|---|
| **Admin (asosiy)** | `yaxyo` | `1710` |
| Admin | `admin` | `admin` |
| Viewer (rahbar) | `rahbar` | `rahbar` |
| O'qituvchi | `karimov` / `yusupova` / `toshpulatov` | `1234` |

> Xavfsizlik uchun ishga tushgandan so'ng parollarni almashtiring
> (`PATCH /api/profile`).

## Nega ilgari ishlamayotgan edi?

1. **`passenger_wsgi.py` yo'q edi** → ASGI ilova WSGI deb yuklanib, har so'rovda 500.
2. a2wsgi lifespan yubormaydi → `init_db()` ishlamas, jadvallar yaratilmas,
   baza bo'sh qolar edi. Endi `passenger_wsgi.py` `init_db()` ni majburan
   (a2wsgi loop'ida) ishga tushiradi.
3. Nisbiy SQLite yo'li (`./metodika.db`) → Passenger boshqa CWD'dan yuklaganda
   noto'g'ri joyda bo'sh baza. Endi mutlaq yo'l ishlatiladi.
