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

from fastapi import APIRouter, Depends

import app.settings as app_settings

from app.zmq_setup import zmq_context
from app.auth import authenticate


router = APIRouter(tags=["info"])


def get_version_from_zmq(address: str) -> str:
    socket = zmq_context.socket(zmq.REQ)
    socket.setsockopt(zmq.RCVTIMEO, 500)
    socket.setsockopt(zmq.LINGER, 0)
    try:
        socket.connect(address)
        socket.send_string("api_version")
        version = socket.recv_string()
    except zmq.error.ZMQError as e:
        version = "xxxx"
    finally:
        socket.close()
    return version


def get_mqbc_api_version() -> str:
    return get_version_from_zmq(app_settings.ZMQ_MQBC_SOCKET)


def get_m2eb_api_version() -> str:
    return get_version_from_zmq(app_settings.ZMQ_M2EB_SOCKET)


def get_serial_number() -> str:
    with open("/run/gnode/serial_number", "r") as api_file:
        return api_file.read()


def get_gnode_api_version():
    with open("./api_version.txt", "r") as file:
        serial_number = file.read()
    return serial_number


@router.get("", dependencies=[Depends(authenticate)])
async def api_version_get():
    api_version = "{}.{}.{}".format(
        get_gnode_api_version(),
        get_m2eb_api_version(),
        get_mqbc_api_version()
    )

    return {
        "api_version" : api_version,
        "serial_number" : get_serial_number()
    }
