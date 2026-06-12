import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import engine, SessionLocal
from app.models.base import Base
from app.models.user import User
from app.modules.auth.helpers import get_password_hash
from app.api.router import router as api_router

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vpn-api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Create tables in the database if they don't exist
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)

    # 2. Seed default admin user if database is empty of admins
    db = SessionLocal()
    try:
        admin_user = db.query(User).filter(User.role == "admin").first()
        if not admin_user:
            logger.warning("No admin user found. Seeding default admin account...")
            default_pwd = "AdminSecurePass123!"
            hashed_pwd = get_password_hash(default_pwd)
            new_admin = User(
                username="admin",
                hashed_password=hashed_pwd,
                role="admin",
                is_active=True
            )
            db.add(new_admin)
            db.commit()
            logger.warning("==========================================================")
            logger.warning("Seeded default Admin:")
            logger.warning("  Username: admin")
            logger.warning("  Password: AdminSecurePass123!")
            logger.warning("  PLEASE CHANGE THIS PASSWORD IMMEDIATELY ON FIRST LOGIN!")
            logger.warning("==========================================================")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to seed default database records: {e}", exc_info=True)
    finally:
        db.close()

    yield


app = FastAPI(title="VPN Management API", version="0.1.0", lifespan=lifespan)

# Setup CORS for the frontend application
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With", "X-CSRF-Token"],
)

# Mount main API router
app.include_router(api_router, prefix="/api")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
