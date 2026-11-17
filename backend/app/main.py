from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.requests import Request
from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError

from app.core.config import settings
from app.database.models import Base
from app.database.seed import seed_synthetic_invoices
from app.database.session import SessionLocal, engine, migrate_local_schema
from app.api.invoices import router as invoices_router
from app.api.analysis import router as analysis_router
from app.api.dashboard import router as dashboard_router
from app.api.chat import router as chat_router
from app.api.auth import router as auth_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    migrate_local_schema()
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_synthetic_invoices(db)
    yield

app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
app.include_router(invoices_router)
app.include_router(analysis_router)
app.include_router(dashboard_router)
app.include_router(chat_router)
app.include_router(auth_router)


@app.exception_handler(HTTPException)
async def http_error_handler(_: Request, exc: HTTPException):
    detail = exc.detail
    if not isinstance(detail, dict) or "code" not in detail or "message" not in detail:
        detail = {"code": "http_error", "message": str(detail)}
    return JSONResponse(status_code=exc.status_code, content={"error": detail}, headers=exc.headers)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_: Request, __: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"error": {"code": "validation_error", "message": "La solicitud no cumple el formato esperado."}},
    )


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
