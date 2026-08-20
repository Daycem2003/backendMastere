from fastapi import APIRouter

from src.apps.authorization.views.permission_view import router as permission_router
from src.apps.authorization.views.role_assignment_view import router as role_assignment_router
from src.apps.authorization.views.role_view import router as role_router

router = APIRouter()
router.include_router(permission_router)
router.include_router(role_router)
router.include_router(role_assignment_router)
