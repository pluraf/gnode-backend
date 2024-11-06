from fastapi import APIRouter

from app.routers import version

import os


router = APIRouter()

def get_mode():
    if os.path.exists("/.dockerenv"):
        return "virtual"
    else:
        return "physical"

@router.get("/")
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