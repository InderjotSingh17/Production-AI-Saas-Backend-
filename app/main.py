
from fastapi import FastAPI, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app import models
from app.config import settings
from app.routers.auth import router as auth_router
from app.routers.conversations import router as conversations_router
from app.routers import jobs
from app.middleware import ObservabilityMiddleware
from app.services.observability import configure_logging

app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG)

configure_logging()
app.add_middleware(ObservabilityMiddleware)

app.include_router(auth_router)
app.include_router(conversations_router)
app.include_router(jobs.router)


@app.on_event("startup")
def create_database_tables():
    Base.metadata.create_all(bind=engine)


@app.get("/")
async def root():
    return {
        "message": "Production AI SaaS Backend is running",
        "environment": settings.APP_ENV,
    }


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/health/database")
def database_health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}
