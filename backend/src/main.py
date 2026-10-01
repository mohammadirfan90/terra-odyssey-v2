"""Main FastAPI application for Earth System Trend Detective.

Enforces:
- Strict OFFLINE=1 execution
- RFC 9457 Problem Details for all scientific and data errors
- Complete OpenAPI schema generation
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api import (
    regions_router,
    parameters_router,
    coverage_router,
    trend_router,
    comparisons_router,
    results_router,
    layers_router,
    sources_router,
)
from .cache.guard import install_offline_guard, remove_offline_guard


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Enforce strict offline isolation
    if os.environ.get("OFFLINE", "1").strip().lower() in ("1", "true", "yes"):
        install_offline_guard()
    yield
    remove_offline_guard()


app = FastAPI(
    title="Earth System Trend Detective API",
    description=(
        "Scientifically rigorous, offline-first Earth system observation and climate trend "
        "investigation platform. Uses area-weighted cell aggregation, Mann-Kendall inference, "
        "Theil-Sen slope estimation, and deterministic bilingual narration."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Allow local frontend development access
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3005",
        "http://127.0.0.1:3005",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:8005",
        "http://127.0.0.1:8005",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def rfc9457_http_exception_handler(request: Request, exc: HTTPException):
    """Format HTTP exceptions conforming to RFC 9457 Problem Details."""
    detail = exc.detail
    if isinstance(detail, dict) and "code" in detail:
        content = {
            "type": detail.get("type", "about:blank"),
            "title": detail.get("title", "Error"),
            "status": exc.status_code,
            "detail": detail.get("detail", str(detail)),
            "code": detail.get("code", "ERROR"),
            "instance": str(request.url),
        }
    else:
        content = {
            "type": "about:blank",
            "title": "HTTP Error",
            "status": exc.status_code,
            "detail": str(detail),
            "code": f"HTTP_{exc.status_code}",
            "instance": str(request.url),
        }

    return JSONResponse(
        status_code=exc.status_code,
        content=content,
        media_type="application/problem+json",
    )


# Mount routers
app.include_router(regions_router)
app.include_router(parameters_router)
app.include_router(coverage_router)
app.include_router(trend_router)
app.include_router(comparisons_router)
app.include_router(results_router)
app.include_router(layers_router)
app.include_router(sources_router)


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint disclosing offline status and runtime version."""
    offline_active = os.environ.get("OFFLINE", "1").strip().lower() in ("1", "true", "yes")
    return {
        "status": "healthy",
        "offline_enforced": offline_active,
        "service": "Earth System Trend Detective Backend",
        "version": "1.0.0",
    }


def run():
    """CLI entrypoint launching the FastAPI server with uvicorn."""
    import uvicorn

    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("src.main:app", host="0.0.0.0", port=port, reload=False)


if __name__ == "__main__":
    run()

