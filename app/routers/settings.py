import zmq

from fastapi import APIRouter, Response, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from typing import Any
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from app.routers import authentication
from app.components import gnode_time, network_connections
from app.components.settings import Settings
from app.zmq_setup import zmq_context
import app.settings as app_settings

router = APIRouter()


@router.get("/")
async def settings_get(_: str = Depends(authentication.authenticate)):
    socket = zmq_context.socket(zmq.REQ)
    socket.setsockopt(zmq.RCVTIMEO, 1000)
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

    current_timestamp = int(datetime.now(timezone.utc).timestamp())
    with open("/etc/timezone", "r") as tz:
        current_timezone = tz.read().strip()
    iso_8601_utc = datetime.now(ZoneInfo(current_timezone)).strftime("%Y-%m-%dT%H:%M:%SZ")
    response["time"] = {
                        "timestamp": current_timestamp,
                        "time": iso_8601_utc,
                        "timezone": current_timezone
                        }

    try:
        response["network settings"] = network_connections.get_netwok_settings()
    except:
        response["network settings"] = {}

    settings = Settings()
    response["authentication"] = settings.authentication
    response["gcloud"] = settings.gcloud

    return JSONResponse(content=response)


@router.put("/")
async def settings_put(settings: dict[str, Any], _: str = Depends(authentication.authenticate)):
    # TODO: Move each block to a dedicated function (class?)
    last_exc = None
    try:
        v = settings.get("allow_anonymous")
        if v is not None:
            socket = zmq_context.socket(zmq.REQ)
            socket.setsockopt(zmq.RCVTIMEO, 1000)
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

    if last_exc is not None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(last_exc),
        )

    return Response(status_code=200)
