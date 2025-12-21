"""HCD REST API FastAPI application.

FastAPI application for managing HCD domain objects with file-backed persistence.
"""

import os

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import hcd_router, solution_router

app = FastAPI(
    title="HCD REST API",
    description="REST API for Human-Centered Design domain objects",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(hcd_router)
app.include_router(solution_router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


def main():
    """Run the HCD REST API server."""
    host = os.getenv("HCD_API_HOST", "0.0.0.0")
    port = int(os.getenv("HCD_API_PORT", "8001"))

    uvicorn.run(
        "julee.docs.hcd_api.app:app",
        host=host,
        port=port,
        reload=True,
    )


if __name__ == "__main__":
    main()
