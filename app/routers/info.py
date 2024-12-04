from fastapi import APIRouter, Depends

from app.routers import version
from app.utils import get_mode
from app.auth import authenticate


router = APIRouter(tags=["info"])


@router.get("", dependencies=[Depends(authenticate)])
async def get_info():
    mode = get_mode()
    api_versions = "{}.{}.{}".format(
        version.get_gnode_api_version(),
        version.get_m2eb_api_version(),
        version.get_mqbc_api_version()
    )
    gnode_serial_number = version.get_serial_number()

    return {
        "mode": mode,
        "version": api_versions,
        "serial_number": gnode_serial_number
    }