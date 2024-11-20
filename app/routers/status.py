from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.routers import authentication
from app.components import network_connections
from app.components.status import get_service_status
import app.settings as app_settings

router = APIRouter()

@router.get("")
async def status_get(_: str = Depends(authentication.authenticate)):
    response = {}
    response["service"] = {
        "mqbc": get_service_status(app_settings.MQBC_SERVICE_NAME),
        "m2eb": get_service_status(app_settings.M2EB_SERVICE_NAME),
        "gcloud_client": get_service_status(app_settings.GCLOUD_SERVICE_NAME)
    }
    response["network"] = network_connections.get_network_status()
    return JSONResponse(content=response)
