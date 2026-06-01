"""
Skill Genome Platform — FastAPI Application Entry Point
=========================================================
This is where the application is assembled.

ARCHITECTURE: Layered Design
┌─────────────────────────────────┐
│         API Layer (Routers)     │  ← HTTP handling, request/response
├─────────────────────────────────┤
│       Service Layer             │  ← Business logic, ML inference
├─────────────────────────────────┤
│       Data Layer (Models/DB)    │  ← Database access, ORM
└─────────────────────────────────┘

WHY FastAPI:
- Async support for high-concurrency ML inference
- Auto-generated OpenAPI docs (Swagger UI at /docs)
- Pydantic validation on all inputs/outputs
- Dependency injection for clean architecture

INTERVIEW ANSWER:
"I chose a layered architecture where routers handle HTTP concerns,
services contain business logic and ML inference, and the data layer
manages persistence. This separation means I can test services
independently, swap databases without changing business logic, and
add new endpoints without touching ML code."
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    skills_router,
    careers_router,
    recommendations_router,
    simulator_router,
)

app = FastAPI(
    title="Skill Genome Platform",
    description=(
        "A career intelligence platform that models skill relationships, "
        "discovers career archetypes, and provides personalized skill "
        "recommendations using NLP, embeddings, and clustering."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# --- CORS Middleware ---
# Allows React frontend (localhost:5173) to call our API (localhost:8000)
# WHY: Browsers block cross-origin requests by default (security).
# Without this, React → FastAPI calls would fail with CORS errors.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite dev server
        "http://localhost:3000",   # Fallback
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Health Check ---
# This is the FIRST endpoint you build in any service.
# WHY: Docker, Kubernetes, and load balancers use health checks
# to know if your service is alive. Without it, broken services
# keep receiving traffic.
@app.get("/api/health", tags=["System"])
async def health_check():
    """Service health check endpoint."""
    return {
        "status": "healthy",
        "service": "skill-genome-platform",
        "version": "0.1.0",
    }


# --- Register Routers ---
app.include_router(skills_router, prefix="/api/skills", tags=["Skills"])
app.include_router(recommendations_router, prefix="/api/recommendations", tags=["Recommendations"])
app.include_router(careers_router, prefix="/api/careers", tags=["Careers"])
app.include_router(simulator_router, prefix="/api/simulator", tags=["Simulator"])


@app.on_event("startup")
async def startup_event():
    """
    Runs when the server starts.
    Use for: loading ML models into memory, warming caches, DB migrations.
    """
    print("🧬 Skill Genome Platform starting up...")
    # Future: Load embedding model, cluster model, etc.


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on server shutdown."""
    print("🧬 Skill Genome Platform shutting down...")
