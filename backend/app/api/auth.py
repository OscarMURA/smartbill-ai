"""Cookie based account authentication and CSRF protection."""
from datetime import UTC, datetime, timedelta
from hashlib import sha256
import secrets
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, EmailStr, Field
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.models import SessionRecord, UserRecord
from app.database.seed import SYNTHETIC_COLLECTION_ID
from app.database.session import get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])
password_hasher = PasswordHash.recommended()
SESSION_COOKIE = "smartbill_session"
SESSION_TTL = timedelta(days=14)


def _utc_now_naive() -> datetime:
    # SQLite's DateTime column is timezone-naive; retain UTC semantics without
    # mixing aware and naive values during expiry comparisons.
    return datetime.now(UTC).replace(tzinfo=None)


def _secure_cookie() -> bool:
    return settings.session_cookie_secure or settings.environment.lower() in {"prod", "production"}


class Credentials(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=256)


def _error(status: int, code: str, message: str) -> HTTPException:
    return HTTPException(status_code=status, detail={"code": code, "message": message})


def _check_origin(request: Request) -> None:
    origin = request.headers.get("origin", "").rstrip("/")
    expected = settings.frontend_origin.rstrip("/")
    if not origin or origin != expected:
        raise _error(403, "origin_rejected", "El origen de la solicitud no está permitido.")


def _user_out(user: UserRecord, csrf: str) -> dict:
    return {"id": user.id, "email": user.email, "csrf_token": csrf}


def _create_session(response: Response, user: UserRecord, db: Session) -> str:
    opaque = secrets.token_urlsafe(32)
    csrf = secrets.token_urlsafe(32)
    db.add(SessionRecord(id=sha256(opaque.encode()).hexdigest(), user_id=user.id,
                         csrf_token=csrf, expires_at=_utc_now_naive() + SESSION_TTL))
    db.commit()
    response.set_cookie(SESSION_COOKIE, opaque, httponly=True, samesite="lax",
                        secure=_secure_cookie(), max_age=int(SESSION_TTL.total_seconds()),
                        path="/",)
    return csrf


def get_current_session(request: Request, db: Session = Depends(get_db)) -> tuple[UserRecord, SessionRecord]:
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        raise _error(401, "authentication_required", "Inicia sesión para continuar.")
    session = db.get(SessionRecord, sha256(token.encode()).hexdigest())
    if session is None or session.expires_at <= _utc_now_naive():
        if session is not None:
            db.delete(session)
            db.commit()
        raise _error(401, "authentication_required", "La sesión no es válida o venció.")
    user = db.get(UserRecord, session.user_id)
    if user is None:
        raise _error(401, "authentication_required", "La sesión no es válida.")
    return user, session


def get_optional_user(request: Request, db: Session = Depends(get_db)) -> UserRecord | None:
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return None
    session = db.get(SessionRecord, sha256(token.encode()).hexdigest())
    if session is None or session.expires_at <= _utc_now_naive():
        return None
    return db.get(UserRecord, session.user_id)


def require_invoice_access(record: object, user: UserRecord | None) -> None:
    is_public_synthetic = (getattr(record, "collection_id") == str(SYNTHETIC_COLLECTION_ID)
                           and getattr(record, "source") == "synthetic")
    if settings.public_demo and not is_public_synthetic:
        raise _error(404, "invoice_not_found", "No se encontró la factura.")
    if not is_public_synthetic:
        if user is None or getattr(record, "user_id") != user.id:
            raise _error(404, "invoice_not_found", "No se encontró la factura.")


def require_csrf(request: Request, auth=Depends(get_current_session)):
    _check_origin(request)
    _, session = auth
    if not secrets.compare_digest(request.headers.get("x-csrf-token", ""), session.csrf_token):
        raise _error(403, "csrf_invalid", "El token de seguridad no es válido.")
    return auth


def verify_authenticated_mutation(request: Request, db: Session):
    """Apply origin and CSRF checks to private mutations while preserving public demo reads."""
    _check_origin(request)
    auth = get_current_session(request, db)
    if not secrets.compare_digest(request.headers.get("x-csrf-token", ""), auth[1].csrf_token):
        raise _error(403, "csrf_invalid", "El token de seguridad no es válido.")
    return auth


@router.post("/register", status_code=201)
def register(payload: Credentials, request: Request, response: Response, db: Session = Depends(get_db)):
    _check_origin(request)
    email = str(payload.email).strip().lower()
    if db.scalar(select(UserRecord).where(UserRecord.email == email)):
        raise _error(409, "email_exists", "Ya existe una cuenta con ese correo.")
    user = UserRecord(id=str(uuid4()), email=email, password_hash=password_hasher.hash(payload.password))
    db.add(user)
    db.flush()
    csrf = _create_session(response, user, db)
    return _user_out(user, csrf)


@router.post("/login")
def login(payload: Credentials, request: Request, response: Response, db: Session = Depends(get_db)):
    _check_origin(request)
    email = str(payload.email).strip().lower()
    user = db.scalar(select(UserRecord).where(UserRecord.email == email))
    if user is None or not password_hasher.verify(payload.password, user.password_hash):
        raise _error(401, "invalid_credentials", "Correo o contraseña incorrectos.")
    csrf = _create_session(response, user, db)
    return _user_out(user, csrf)


@router.get("/me")
def me(auth=Depends(get_current_session)):
    user, session = auth
    return _user_out(user, session.csrf_token)


@router.post("/logout")
def logout(request: Request, response: Response, auth=Depends(require_csrf), db: Session = Depends(get_db)):
    _check_origin(request)
    _, session = auth
    db.delete(session)
    db.commit()
    response.delete_cookie(SESSION_COOKIE, path="/", httponly=True, samesite="lax",
                           secure=_secure_cookie())
    return {"ok": True}
