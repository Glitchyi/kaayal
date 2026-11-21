import asyncio
import hmac
import logging
import time
import uuid

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlmodel import Session

from app.admin import router as admin_router
from app.catalog import router as catalog_router
from app.config import Settings, get_settings
from app.db import make_engine
from app.openai_adapter import OpenAIAdapterError, make_responder
from app.pii import anonymize_stale_requests
from app.portal import router as portal_router
from app.requests_api import router as requests_router
from app.schemas import VoiceReplyRequest, VoiceReplyResponse
from app.site import router as site_router

logger = logging.getLogger("kaayal")

TOOL_TOKEN_HEADER = "X-Kaayal-Tool-Token"


class RateLimiter:
    """Fixed-window, per-process limiter (Phase 1 has a single instance)."""

    def __init__(self, per_minute: int) -> None:
        self.per_minute = per_minute
        self._window_start = time.monotonic()
        self._count = 0
        self._lock = asyncio.Lock()

    async def allow(self) -> bool:
        async with self._lock:
            now = time.monotonic()
            if now - self._window_start >= 60:
                self._window_start = now
                self._count = 0
            self._count += 1
            return self._count <= self.per_minute


def _error(status: int, code: str, trace_id: str | None = None) -> JSONResponse:
    body = {"detail": code}
    if trace_id:
        body["trace_id"] = trace_id
    return JSONResponse(status_code=status, content=body)


def create_app(settings: Settings | None = None, responder=None) -> FastAPI:
    settings = settings or get_settings()
    logging.basicConfig(level=settings.log_level.upper())

    app = FastAPI(title="Kaayal Voice Tool Adapter", version="0.2.0")
    app.state.settings = settings
    app.state.responder = responder or make_responder(settings)
    app.state.rate_limiter = RateLimiter(settings.rate_limit_per_minute)
    app.state.engine = make_engine(settings.database_url)
    with Session(app.state.engine) as session:
        anonymized = anonymize_stale_requests(session)
    logger.info("startup pii_anonymization anonymized=%d", anonymized)

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError):
        # Contract uses 400 for invalid input; never echo back the utterance.
        return _error(400, "invalid_request")

    @app.middleware("http")
    async def body_size_limit(request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length and content_length.isdigit():
            if int(content_length) > settings.max_body_bytes:
                return _error(413, "request_too_large")
        return await call_next(request)

    class _ServiceMisconfigured(Exception):
        pass

    async def require_tool_auth(
        x_kaayal_tool_token: str | None = Header(default=None),
    ) -> None:
        secret = settings.sarvam_tool_shared_secret
        if not secret:
            raise _ServiceMisconfigured
        if not x_kaayal_tool_token or not hmac.compare_digest(x_kaayal_tool_token, secret):
            raise HTTPException(status_code=401, detail="unauthorized")

    @app.exception_handler(_ServiceMisconfigured)
    async def misconfigured_handler(request: Request, exc: _ServiceMisconfigured):
        return _error(503, "service_not_configured")

    app.include_router(catalog_router, dependencies=[Depends(require_tool_auth)])
    app.include_router(requests_router, dependencies=[Depends(require_tool_auth)])
    app.include_router(portal_router)
    app.include_router(admin_router)
    app.include_router(site_router)

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.post("/api/voice/reply", response_model=VoiceReplyResponse)
    async def voice_reply(
        payload: VoiceReplyRequest,
        request: Request,
        _auth: None = Depends(require_tool_auth),
    ):
        trace_id = uuid.uuid4().hex[:16]
        if not await app.state.rate_limiter.allow():
            logger.warning("voice_reply outcome=rate_limited trace_id=%s", trace_id)
            return _error(429, "rate_limited", trace_id)

        started = time.monotonic()
        try:
            reply_text = await app.state.responder(payload.utterance, payload.language)
        except OpenAIAdapterError as exc:
            logger.warning(
                "voice_reply outcome=upstream_error trace_id=%s interaction_id=%s reason=%s",
                trace_id,
                payload.interaction_id,
                exc,
            )
            return _error(502, "upstream_unavailable", trace_id)

        latency_ms = int((time.monotonic() - started) * 1000)
        # Sanitized trace only: no utterance text, no caller identity, no secrets.
        logger.info(
            "voice_reply outcome=ok trace_id=%s interaction_id=%s language=%s latency_ms=%d",
            trace_id,
            payload.interaction_id,
            payload.language,
            latency_ms,
        )
        return VoiceReplyResponse(reply_text=reply_text, trace_id=trace_id)

    return app


app = create_app()


def main() -> None:
    import uvicorn

    settings = get_settings()
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.port, log_level=settings.log_level.lower())


if __name__ == "__main__":
    main()
