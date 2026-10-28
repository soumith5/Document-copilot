import time
import uuid

import structlog
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.auth.dependencies import get_current_user
from app.config import get_settings
from app.api.threads import router as threads_router
from app.api.chat import router as chat_router
from app.api.notes import router as notes_router

settings = get_settings()

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer(),
    ],
)

log = structlog.get_logger()

app = FastAPI()
app.include_router(threads_router)
app.include_router(chat_router)
app.include_router(notes_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        request_id=request_id,
        method=request.method,
        path=request.url.path,
    )

    start = time.perf_counter()
    log.info("request_started")

    try:
        response = await call_next(request)
    except Exception:
        log.exception("request_failed")
        raise

    duration_ms = round((time.perf_counter() - start) * 1000, 2)
    log.info(
        "request_finished",
        status_code=response.status_code,
        duration_ms=duration_ms,
    )
    response.headers["X-Request-ID"] = request_id
    return response


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/")
def read_root():
    return {"message": "Welcome to Document Copilot API"}

@app.get("/me")
def read_current_user(user=Depends(get_current_user)):
    return {"id": user.id, "email": user.email}