from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter

from match.presentation.api.service import router as service_router

router = APIRouter(
    prefix="/api/v1",
    route_class=DishkaRoute,
)

router.include_router(service_router, tags=["service"])
