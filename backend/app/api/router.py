from fastapi import APIRouter
from app.modules.auth.router import router as auth_router
from app.modules.vpn.router import router as vpn_router
from app.modules.threats.router import router as threats_router
from app.modules.audit.router import router as audit_router
from app.modules.sessions.router import router as sessions_router
from app.modules.admin.router import router as admin_router
from app.modules.users.router import router as users_router

router = APIRouter()

router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
router.include_router(vpn_router, prefix="/vpn", tags=["VPN Control"])
router.include_router(threats_router, prefix="/threats", tags=["Threat Detection"])
router.include_router(audit_router, prefix="/audit", tags=["Audit Observability"])
router.include_router(sessions_router, prefix="/sessions", tags=["Session Monitoring"])
router.include_router(admin_router, prefix="/admin", tags=["Admin Operations"])
router.include_router(users_router, prefix="/users", tags=["User Management"])


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
