from app.api.skills import router as skills_router
from app.api.careers import router as careers_router
from app.api.recommendations import router as recommendations_router
from app.api.simulator import router as simulator_router

__all__ = [
    "skills_router",
    "careers_router",
    "recommendations_router",
    "simulator_router",
]
