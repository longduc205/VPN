from fastapi import APIRouter
from app.modules.auth.router import router as auth_router

router = APIRouter()

router.include_router(auth_router, prefix="/auth", tags=["Authentication"])


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
