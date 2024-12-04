from fastapi import APIRouter

from app.components.gnode_time import list_timezones


router = APIRouter(tags=["info"])


@router.get("")
async def get_timezone_list():
    timezone_list = list_timezones()
    return timezone_list