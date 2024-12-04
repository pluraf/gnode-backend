import zmq

from fastapi import APIRouter, Response, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from typing import Any

from app.routers import authentication
from app.components import gnode_time, network_connections
from app.components.settings import Settings
from app.zmq_setup import zmq_context
from app.auth import authenticate

import app.settings as app_settings


router = APIRouter(tags=["settings"])


@router.get("/", dependencies=[Depends(authenticate)])
async def settings_get():
    socket = zmq_context.socket(zmq.REQ)
    socket.setsockopt(zmq.RCVTIMEO, 500)
    socket.setsockopt(zmq.LINGER, 0)
    socket.connect(app_settings.ZMQ_MQBC_ENDPOINT)

    response = {}

    try:
        socket.send_string('')
        message = socket.recv()
    except zmq.error.ZMQError:
        message = b"\x00"
    finally:
        socket.close()
    response["allow_anonymous"] = bool(message[0])

    try:
        response["time"] = gnode_time.get_gnode_time()
    except:
        response["time"] = {}

    try:
        response["network_settings"] = network_connections.get_netwok_settings()
    except:
        response["network_settings"] = {}

    settings = Settings()
    response["authentication"] = settings.authentication
    response["gcloud"] = settings.gcloud

    return JSONResponse(content=response)


@router.put("/", dependencies=[Depends(authenticate)])
async def settings_put(settings: dict[str, Any], _: str = Depends(authentication.authenticate)):
    # TODO: Move each block to a dedicated function (class?)
    last_exc = None
    try:
        v = settings.get("allow_anonymous")
        if v is not None:
            socket = zmq_context.socket(zmq.REQ)
            socket.setsockopt(zmq.RCVTIMEO, 500)
            socket.setsockopt(zmq.LINGER, 0)
            socket.connect(app_settings.ZMQ_MQBC_ENDPOINT)
            try:
                socket.send(b'\x01' if v else b'\x00')
                socket.recv()
            except zmq.error.ZMQError:
                pass
            finally:
                socket.close()
    except Exception as e:
        last_exc = e

    try:
        v = settings.get("gnode_time")
        if v is not None:
            gnode_time.set_gnode_time(v)
    except Exception as e:
        last_exc = e

    try:
        v = settings.get("network_settings")
        if v is not None:
            network_connections.set_network_settings(v)
    except Exception as e:
        last_exc = e

    try:
        v = settings.get("authentication")
        if v is not None:
            Settings().authentication = v
    except Exception as e:
        last_exc = e

    try:
        v = settings.get("gcloud")
        if v is not None:
            Settings().gcloud = v
    except Exception as e:
        last_exc = e

    if isinstance(last_exc, HTTPException):
        raise last_exc
    elif last_exc is not None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(last_exc)
        )

    return Response(status_code=200)
