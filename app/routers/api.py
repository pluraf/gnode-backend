from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from app.routers import users
from app.routers import authentication

import app.settings as settings

router = APIRouter()


@router.get("/", response_class=PlainTextResponse)
async def retrieve_home():
    return "Welcome!!!"


router.include_router(users.router, prefix="/user")
router.include_router(authentication.router, prefix=settings.TOKEN_AUTH_URL)
