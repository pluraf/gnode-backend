import json

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.openapi.docs import (
    get_redoc_html,
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles

from app.routers.api import router as api_router
from app.crud.users import load_first_user
from app.database_setup import SessionLocal, DefaultBase, AuthBase, default_engine, auth_engine
from app.components.settings import init_settings_table
from app.zmq_setup import zmq_context

# We load all DB models here, so Base classes can create all tables in lifespan
import app.models.authbundle
import app.models.user
import app.models.settings


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
    application = FastAPI(
        title="G-Node",
        root_path="/api",
        docs_url=None,
        redoc_url=None,
        lifespan=lifespan
    )
    application.include_router(api_router)
    return application


app = get_application()


###############################################################################
# Documentation

static_prefix = ""

# Uncomment, if you want to test documentation running only gnode-backend
# app.mount("/static", StaticFiles(directory="static"), name="static")
# static_prefix = "/api"


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url = "/api/openapi.json",
        title = app.title + " - Swagger",
        oauth2_redirect_url = app.swagger_ui_oauth2_redirect_url,
        swagger_js_url = static_prefix + "/static/swagger-ui-bundle.js",
        swagger_css_url = static_prefix + "/static/swagger-ui.css",
        swagger_favicon_url = "/favicon.ico"
    )


@app.get(app.swagger_ui_oauth2_redirect_url, include_in_schema=False)
async def swagger_ui_redirect():
    return get_swagger_ui_oauth2_redirect_html()


@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    return get_redoc_html(
        openapi_url = "/api/openapi.json",
        title = app.title + " - ReDoc",
        redoc_js_url = static_prefix + "/static/redoc.standalone.js",
        with_google_fonts = False,
        redoc_favicon_url = "/favicon.ico"
    )


def merge_openapi_specs():
    openapi = get_openapi(
        title="G-Node API",
        version="0.0.0",
        routes=app.routes,
    )

    with open("app/openapi/m2eb_openapi.json", "r") as f:
        m2eb_openapi = json.load(f)
#
#    openapi["info"] = {
#        "title": "API",
#        "license": {
#            "name": "BSD 3-Clause",
#            "url": "https://spdx.org/licenses/BSD-3-Clause.html"
#        },
#        "externalDocs": {
#            "description": "Find out more about G-Node",
#            "url": "https://docs.iotplan.io/gnode/index.html"
#        }
#    }
#
    openapi.setdefault("tags", []).extend(m2eb_openapi["tags"])
    openapi["paths"].update(m2eb_openapi["paths"])
    openapi["components"]["schemas"].update(m2eb_openapi["components"]["schemas"])
    openapi["servers"] = [{"url": app.root_path}]

    return openapi


app.openapi = merge_openapi_specs
