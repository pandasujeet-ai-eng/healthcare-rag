from app.observability.azure_monitor import (
    configure_monitoring,
)

configure_monitoring()


from fastapi import FastAPI
from fastapi.middleware.cors import (
    CORSMiddleware,
)

from app.api.graph_routes import (
    router as graph_router,
)
from app.api.routes import (
    router as api_router,
)
from app.api.security_routes import (
    router as security_router,
)


APP_NAME = "Healthcare Knowledge Assistant"
APP_VERSION = "0.19.0"


app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=[
        "GET",
        "POST",
    ],
    allow_headers=["*"],
)


app.include_router(
    api_router
)

app.include_router(
    graph_router
)

app.include_router(
    security_router
)


@app.get(
    "/",
    tags=["Service"],
)
def root() -> dict:

    return {
        "service": APP_NAME,
        "version": APP_VERSION,
        "status": "running",
    }