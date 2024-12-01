from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.routers.api import router as api_router
from app.crud.users import load_first_user
from app.database_setup import SessionLocal, DefaultBase, AuthBase, default_engine, auth_engine
from app.components.settings import init_settings_table

# We load all DB models here, so Base classes can create all tables in lifespan
import app.models.authbundle
import app.models.user
import app.models.settings

from app.zmq_setup import zmq_context


@asynccontextmanager
async def lifespan(app: FastAPI):
    db_session = SessionLocal()
    DefaultBase.metadata.create_all(bind=default_engine)
    AuthBase.metadata.create_all(bind=auth_engine)
    try:
        # Load first user to DB
        load_first_user(db_session)
        db_session.close()
        # Initialize settings table
        init_settings_table()
        yield
    finally:
        # Clean up
        zmq_context.term()



def get_application() -> FastAPI:
    application = FastAPI(lifespan=lifespan, root_path="/api")
    application.include_router(api_router)
    return application


app = get_application()
