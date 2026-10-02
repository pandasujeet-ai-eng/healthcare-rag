from __future__ import annotations


from app.observability.azure_monitor import (
    configure_monitoring,
)


configure_monitoring()


from fastapi import (
    FastAPI,
)

from fastapi.middleware.cors import (
    CORSMiddleware,
)

from fastapi.responses import (
    RedirectResponse,
)

from fastapi.staticfiles import (
    StaticFiles,
)


from app.api.evidence_routes import (
    router as evidence_router,
)

from app.api.graph_routes import (
    router as graph_router,
)

from app.api.localization_routes import (
    router as localization_router,
)

from app.api.review_queue_routes import (
    router as review_queue_router,
)

from app.api.risk_routes import (
    router as risk_router,
)

from app.api.routes import (
    router as api_router,
)

from app.api.security_routes import (
    router as security_router,
)

from app.web.routes import (
    router as web_router,
)


APP_NAME = (
    "CareGuard AI"
)

APP_VERSION = (
    "1.6.0-hackathon"
)


app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*",
    ],
    allow_credentials=False,
    allow_methods=[
        "GET",
        "POST",
    ],
    allow_headers=[
        "*",
    ],
)


# =============================================================
# STATIC
# =============================================================


app.mount(
    "/static",
    StaticFiles(
        directory="app/static"
    ),
    name="static",
)


# =============================================================
# EXISTING APIs
# =============================================================


app.include_router(
    api_router
)

app.include_router(
    graph_router
)

app.include_router(
    security_router
)


# =============================================================
# CAREGUARD GOVERNANCE
# =============================================================


app.include_router(
    risk_router
)

app.include_router(
    evidence_router
)

app.include_router(
    review_queue_router
)

app.include_router(
    localization_router
)


# =============================================================
# PRODUCT UI
# =============================================================


app.include_router(
    web_router
)


# =============================================================
# ROOT
# =============================================================


@app.get(
    "/",
    include_in_schema=False,
)
def root() -> RedirectResponse:

    return RedirectResponse(
        url="/app",
        status_code=302,
    )