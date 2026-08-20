from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from src.apps.authorization.services.permission_service import PermissionService
from src.apps.authorization.services.role_service import RoleService
from src.apps.authorization.fastapi_router import router as authorization_router
from src.config.settings.development import CORS_ALLOWED_ORIGINS
@asynccontextmanager
async def lifespan(app: FastAPI):
    await PermissionService.seed_default_permissions()
    await RoleService.seed_default_roles()
    yield


app = FastAPI(title="Mastere Backend API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(authorization_router, prefix="/api/v1/authorization", tags=["Authorization"])


@app.get("/health")
async def health_check():
    return {"status": "ok"}