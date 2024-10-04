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


@router.get("/")
async def settings_get(_: str = Depends(authentication.validate_jwt)):
    socket.send_string('')
    message = socket.recv()
    return JSONResponse(content={"allow_anonymous": bool(message[0])})


@router.put("/")
async def settings_put(settings: dict[str, Any], _: str = Depends(authentication.validate_jwt)):
    a = settings["allow_anonymous"]
    socket.send(b'\x01' if a else b'\x00')

    if "gnode_time" in settings:
        gnode_time.set_gnode_time(settings["gnode_time"])

    socket.recv()
    return Response(status_code=200)
