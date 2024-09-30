from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.routers.api import router as api_router
from app.crud.users import load_first_user
from app.database_setup import SessionLocal, DefaultBase, AuthBase, engine

# We load all DB models here, so Base classes can create all tables in lifespan
import app.models.authbundle
import app.models.user


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
