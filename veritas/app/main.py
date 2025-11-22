"""
Veritas - AI Senate Truth Auditor

Main FastAPI application entry point for the Veritas truth auditing system.
Veritas is responsible for:
- Truth auditing and fact verification
- Logic checking and fallacy detection
- Bias detection and analysis
- Chain-of-thought validation
- Source verification

Phase 1: Scaffolding with stub implementations.
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.config import config
from app.routes.veritas import router as veritas_router


app = FastAPI(
    title=config.app_name,
    version=config.version,
    description="Veritas: AI Senate Truth Auditor - Responsible for truth auditing, "
                "logic checking, bias detection, and chain-of-thought validation.",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Register the Veritas router
app.include_router(veritas_router)


@app.get("/", response_class=JSONResponse)
async def root():
    """
    Root endpoint providing basic information about the Veritas service.
    """
    return {
        "service": config.app_name,
        "version": config.version,
        "description": "AI Senate Truth Auditor",
        "status": "operational",
    }


@app.get("/health", response_class=JSONResponse)
async def health_check():
    """
    Health check endpoint for monitoring and load balancer probes.

    Returns:
        JSON object with health status and service information.
    """
    return {
        "status": "healthy",
        "service": config.app_name,
        "version": config.version,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
