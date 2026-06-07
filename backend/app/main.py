from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

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

allowed_origins = [
    "http://localhost:5173",
    "http://localhost:3000",
]
env_origins = os.getenv("ALLOWED_ORIGINS")
if env_origins:
    if env_origins.strip() == "*":
        allowed_origins = ["*"]
    else:
        allowed_origins.extend([o.strip() for o in env_origins.split(",") if o.strip()])
else:
    allowed_origins.append("*")

allow_credentials = "*" not in allowed_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", tags=["System"])
async def health_check():
    """Service health check endpoint."""
    return {
        "status": "healthy",
        "service": "skill-genome-platform",
        "version": "0.1.0",
    }


# Register Routers
app.include_router(skills_router, prefix="/api/skills", tags=["Skills"])
app.include_router(recommendations_router, prefix="/api/recommendations", tags=["Recommendations"])
app.include_router(careers_router, prefix="/api/careers", tags=["Careers"])
app.include_router(simulator_router, prefix="/api/simulator", tags=["Simulator"])


@app.on_event("startup")
async def startup_event():
    """Run server startup hooks."""
    print("Skill Genome Platform starting up...")


@app.on_event("shutdown")
async def shutdown_event():
    """Run server shutdown hooks."""
    print("Skill Genome Platform shutting down...")
