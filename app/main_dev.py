from fastapi import FastAPI
from .main import app as main_app
from .main import lifespan


# lifespan is executed only for the main application
# https://fastapi.tiangolo.com/advanced/events/?h=asynccontextmanager#sub-applications
app = FastAPI(lifespan=lifespan)
app.mount("/api", main_app)