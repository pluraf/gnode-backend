from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.routers.api import router as api_router
from app.crud.users import load_first_user
from app.components.authentication_req import initialize_authentication_setting
from app.database_setup import SessionLocal, DefaultBase, AuthBase, default_engine, auth_engine

# We load all DB models here, so Base classes can create all tables in lifespan
import app.models.authbundle
import app.models.user
import app.models.authentication

from app.zmq_setup import zmq_context


@asynccontextmanager
async def lifespan(app: FastAPI):
    db_session = SessionLocal()
    DefaultBase.metadata.create_all(bind=default_engine)
    AuthBase.metadata.create_all(bind=auth_engine)
    try:
        # As default require authentication
        # Set initial authentication required value to true
        initialize_authentication_setting(db_session)
        # Load first user to DB
        load_first_user(db_session)
        db_session.close()
        yield
    finally:
        zmq_context.term()
    # Clean up


def get_application() -> FastAPI:
    application = FastAPI(lifespan=lifespan)
    application.include_router(api_router)
    return application


app = get_application()
