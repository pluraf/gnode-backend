# SPDX-License-Identifier: Apache-2.0

# Copyright (c) 2024 Pluraf Embedded AB <code@pluraf.com>

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


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
    socket.connect(app_settings.ZMQ_MQBC_SOCKET)

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
    response["api_authentication"] = settings.api_authentication
    response["gcloud"] = settings.gcloud

    return JSONResponse(content=response)


@router.put("/", dependencies=[Depends(authenticate)])
async def settings_put(settings: dict[str, Any]):
    # TODO: Move each block to a dedicated function (class?)
    last_exc = None
    try:
        v = settings.get("allow_anonymous")
        if v is not None:
            socket = zmq_context.socket(zmq.REQ)
            socket.setsockopt(zmq.RCVTIMEO, 500)
            socket.setsockopt(zmq.LINGER, 0)
            socket.connect(app_settings.ZMQ_MQBC_SOCKET)
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
        v = settings.get("api_authentication")
        if v is not None:
            Settings().api_authentication = v
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
