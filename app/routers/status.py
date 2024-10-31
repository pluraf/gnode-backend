import zmq

from fastapi import APIRouter, Response, Depends, HTTPException
from fastapi.responses import JSONResponse
from typing import Any

from app.routers import authentication
from app.components import network_connections
from app.zmq_setup import zmq_context
import app.settings as app_settings

router = APIRouter()

def get_status_from_zmq(address: str) -> str:
    socket = zmq_context.socket(zmq.REQ)
    try:
        socket.connect(address)
        socket.send_string("status")
        socket.setsockopt(zmq.RCVTIMEO, 1000)
        status = socket.recv_string()
    except zmq.error.ZMQError as e:
        status = "not running"
    finally:
        socket.close()
    return status

@router.get("/")
async def status_get(_: str = Depends(authentication.validate_jwt)):
    response = {}
    response["mqbc_status"] = get_status_from_zmq(app_settings.ZMQ_MQBC_ENDPOINT)
    response["m2eb_status"] = get_status_from_zmq(app_settings.ZMQ_M2EB_ENDPOINT)
    response["network_status"] = network_connections.get_network_status()
    return JSONResponse(content=response)

