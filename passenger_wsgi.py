"""cPanel (Phusion Passenger) uchun kirish nuqtasi.

Nega bu fayl kerak?
    FastAPI — ASGI ilova. cPanel'ning "Setup Python App" (Passenger) esa WSGI
    `application` chaqiriladigan obyektni kutadi. To'g'ridan-to'g'ri `main:app`
    ni ko'rsatsak, Passenger uni WSGI deb yuklaydi va HAR so'rovda 500 beradi.

    a2wsgi.ASGIMiddleware ASGI ilovani WSGI'ga o'raydi. U barcha so'rovlarni
    fon thread'idagi BITTA doimiy event loop orqali bajaradi (async SQLAlchemy
    engine uchun xavfsiz), LEKIN ASGI lifespan hodisalarini yubormaydi.
    Shu sababli FastAPI'ning `lifespan`'idagi `init_db()` (jadval yaratish +
    seed) o'z-o'zidan ISHLAMAYDI — natijada baza bo'sh qoladi va 500 chiqadi.

    Yechim: quyida init_db() ni aynan a2wsgi ishlatadigan loop'da majburan
    ishga tushiramiz. Shunda jadvallar yaratiladi, demo ma'lumot va standart
    admin (yaxyo) seed qilinadi — hammasi so'rovlar bilan bir xil loop'da.
"""

import os
import sys

# Loyiha ildizini import yo'liga qo'shamiz (Passenger CWD boshqacha bo'lishi mumkin).
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import asyncio  # noqa: E402

from a2wsgi import ASGIMiddleware  # noqa: E402

from database.db import init_db  # noqa: E402
from main import app  # noqa: E402

# ASGI -> WSGI ko'prigi. `_bridge.loop` — barcha so'rovlar bajariladigan
# doimiy event loop.
_bridge = ASGIMiddleware(app)

# Bazani AYNAN o'sha loop'da tayyorlaymiz (lifespan bu yerda ishlamaydi).
# Import bloklanadi to init tugaguncha — birinchi so'rov kelguncha baza tayyor.
_init_future = asyncio.run_coroutine_threadsafe(init_db(), _bridge.loop)
_init_future.result()

# Passenger aynan shu nomdagi obyektni qidiradi.
application = _bridge
