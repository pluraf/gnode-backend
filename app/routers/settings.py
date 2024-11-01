import zmq

from fastapi import APIRouter, Response, Depends
from fastapi.responses import JSONResponse
from typing import Any
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from app.routers import authentication
from app.components import gnode_time
from app.components import authentication_req
from app.zmq_setup import zmq_context

router = APIRouter()


@router.get("/")
async def settings_get(_: str = Depends(authentication.conditionally_authenticate)):
    socket = zmq_context.socket(zmq.REQ)
    socket.connect("ipc:///tmp/mqbc-zmq.sock")
    socket.setsockopt(zmq.RCVTIMEO, 1000)

    response = {}

    try:
        socket.send_string('')
        message = socket.recv()
    except zmq.error.ZMQError:
        message = b"\x00"
    finally:
        socket.close()
    response["allow_anonymous"] = bool(message[0])

    current_timestamp = int(datetime.now(timezone.utc).timestamp())
    with open("/etc/timezone", "r") as tz:
        current_timezone = tz.read().strip()
    iso_8601_utc = datetime.now(ZoneInfo(current_timezone)).strftime("%Y-%m-%dT%H:%M:%SZ")
    response["time"] = {
                        "timestamp": current_timestamp,
                        "time": iso_8601_utc,
                        "timezone": current_timezone
                        }


    response["authentication_required"] = authentication_req.get_authentication_required()

    return JSONResponse(content=response)


@router.put("/")
async def settings_put(settings: dict[str, Any], _: str = Depends(authentication.conditionally_authenticate)):
    socket = zmq_context.socket(zmq.REQ)
    socket.connect("ipc:///tmp/mqbc-zmq.sock")
    socket.setsockopt(zmq.RCVTIMEO, 1000)

    v = settings.get("allow_anonymous")
    if v is not None:
        try:
            socket.send(b'\x01' if v else b'\x00')
            socket.recv()
        except zmq.error.ZMQError:
            pass
        finally:
            socket.close()

    v = settings.get("gnode_time")
    if v is not None:
        gnode_time.set_gnode_time(v)

    v = settings.get("authentication_required")
    if v is not None:
        authentication_req.update_authentication_required(v)


    return Response(status_code=200)
