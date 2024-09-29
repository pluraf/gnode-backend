from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session

from app.routers.api import router as api_router
from app.crud.users import load_first_user
from app.dependencies import get_db
from app.database_setup import SessionLocal, DefaultBase, AuthBase, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    db_session = SessionLocal()
    DefaultBase.metadata.create_all(bind=engine)
    AuthBase.metadata.create_all(bind=engine)
    try:
        # Load first user to DB
        load_first_user(db_session)
        yield
    finally:
        db_session.close()
    # Clean up


def get_application() -> FastAPI:
    application = FastAPI(lifespan=lifespan)
    application.include_router(api_router)
    return application


app = get_application()
