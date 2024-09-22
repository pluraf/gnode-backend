import zmq

from fastapi import APIRouter, Response
from fastapi.responses import JSONResponse
from typing import Any


router = APIRouter()


context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect("ipc:///tmp/mqbc-zmq.sock")


@router.get("/")
async def settings_get():
    socket.send_string('')
    message = socket.recv()
    return JSONResponse(content={"allow_anonymous": bool(message[0])})


@router.put("/")
async def settings_put(settings: dict[str, Any]):
    a = settings["allow_anonymous"]
    socket.send(b'\x01' if a else b'\x00')
    socket.recv()
    return Response(status_code=200)
