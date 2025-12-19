"""C4 REST API FastAPI application.

FastAPI application for managing C4 architecture model with file-backed persistence.
"""

import os

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import c4_router

app = FastAPI(
    title="C4 Architecture REST API",
    description="REST API for C4 software architecture model",
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
app.include_router(c4_router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


def main():
    """Run the C4 REST API server."""
    host = os.getenv("C4_API_HOST", "0.0.0.0")
    port = int(os.getenv("C4_API_PORT", "8002"))

    uvicorn.run(
        "julee.docs.c4_api.app:app",
        host=host,
        port=port,
        reload=True,
    )


if __name__ == "__main__":
    main()
