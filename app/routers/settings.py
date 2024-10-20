import zmq

from fastapi import APIRouter, Response, Depends
from fastapi.responses import JSONResponse
from typing import Any

from app.routers import authentication
from app.components import gnode_time
from app.zmq_setup import zmq_context

router = APIRouter()


@router.get("/")
async def settings_get(_: str = Depends(authentication.validate_jwt)):
    socket = zmq_context.socket(zmq.REQ)
    socket.connect("ipc:///tmp/mqbc-zmq.sock")
    socket.setsockopt(zmq.RCVTIMEO, 1000)

    try:
        socket.send_string('')
        message = socket.recv()
    except zmq.error.ZMQError:
        message = b"\x00"
    finally:
        socket.close()
    return JSONResponse(content={"allow_anonymous": bool(message[0])})


@router.put("/")
async def settings_put(settings: dict[str, Any], _: str = Depends(authentication.validate_jwt)):
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

    return Response(status_code=200)
