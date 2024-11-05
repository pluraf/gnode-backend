from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from app.routers import users
from app.routers import authentication
from app.routers import authbundle
from app.routers import settings
from app.routers import version
from app.routers import info

import app.settings as app_settings

router = APIRouter()


@router.get("/", response_class=PlainTextResponse)
async def retrieve_home():
    return "Welcome to G-Node!"


router.include_router(users.router, prefix="/user")
router.include_router(authentication.router, prefix=app_settings.TOKEN_AUTH_URL)
router.include_router(authbundle.router, prefix="/authbundle")
router.include_router(settings.router, prefix="/settings")
router.include_router(version.router, prefix="/version")
router.include_router(info.router, prefix="/info")