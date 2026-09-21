from app.observability.azure_monitor import (
    configure_monitoring,
)


# Configure OpenTelemetry before creating
# the FastAPI application.
configure_monitoring()


from fastapi import FastAPI
from fastapi.middleware.cors import (
    CORSMiddleware,
)

from app.api.routes import router


APP_NAME = (
    "Healthcare Knowledge Assistant"
)

APP_VERSION = "0.7.0"


app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description=(
        "Production-style healthcare RAG API "
        "using LangChain, Azure OpenAI, "
        "Azure AI Search, LangSmith and "
        "Azure Application Insights."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)


# DEV configuration.
#
# We will restrict origins before production
# deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*"
    ],
    allow_credentials=False,
    allow_methods=[
        "GET",
        "POST",
    ],
    allow_headers=[
        "*"
    ],
)


app.include_router(
    router
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
        "documentation": "/docs",
    }