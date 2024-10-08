import zmq

from fastapi import APIRouter, Response, Depends
from fastapi.responses import JSONResponse
from typing import Any

from app.routers import authentication
from app.components import gnode_time

router = APIRouter()


context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect("ipc:///tmp/mqbc-zmq.sock")
socket.setsockopt(zmq.RCVTIMEO, 2000)


@router.get("/")
async def settings_get(_: str = Depends(authentication.validate_jwt)):
    try:
        socket.send_string('')
        message = socket.recv()
    except zmq.error.ZMQError:
        message = b"\x00"
    return JSONResponse(content={"allow_anonymous": bool(message[0])})


@router.put("/")
async def settings_put(settings: dict[str, Any], _: str = Depends(authentication.validate_jwt)):
    v = settings.get("allow_anonymous")
    if v is not None:
        try:
            socket.send(b'\x01' if v else b'\x00')
            socket.recv()
        except zmq.error.ZMQError:
            pass

    v = settings.get("gnode_time")
    if v is not None:
        gnode_time.set_gnode_time(v)

    return Response(status_code=200)
