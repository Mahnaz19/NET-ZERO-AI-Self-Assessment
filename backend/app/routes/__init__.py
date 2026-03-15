from fastapi import APIRouter

from .health import router as health_router
from .recommendations import router as recommendations_router
from .submissions import router as submissions_router


api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(submissions_router)
api_router.include_router(recommendations_router)

