"""Parol hash'lash (bcrypt) va JWT token yaratish/tekshirish.

Sozlamalar .env dan olinadi: JWT_SECRET, JWT_ALGORITHM, TOKEN_TTL_HOURS.
"""

import os
from datetime import datetime, timedelta, timezone

import jwt
from dotenv import load_dotenv
from passlib.context import CryptContext

load_dotenv()

# Production'da JWT_SECRET majburiy — aks holda repodagi default kalit bilan
# istalgan odam o'ziga admin token yasay oladi (7.1-band). Dev'da default qoladi.
JWT_SECRET = os.getenv("JWT_SECRET") or ""
if not JWT_SECRET:
    if os.getenv("ENV", "dev") == "prod":
        raise RuntimeError("JWT_SECRET o'rnatilmagan — production'da majburiy")
    JWT_SECRET = "dev-maxfiy-kalit"

JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
TOKEN_TTL_HOURS = int(os.getenv("TOKEN_TTL_HOURS", "24"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# --- Parol ---

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# --- JWT ---

def create_access_token(sub: str, kind: str, role: str) -> str:
    """Token yaratadi. Payload (spec 7.1): sub (id), kind (user/teacher), role."""
    payload = {
        "sub": sub,
        "kind": kind,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=TOKEN_TTL_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Tokenni tekshiradi va payload qaytaradi.

    Yaroqsiz/muddati o'tgan bo'lsa jwt.InvalidTokenError ko'tariladi
    (jwt.ExpiredSignatureError ham uning avlodi) — deps.get_current_user
    uni 401 ga aylantiradi.
    """
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
