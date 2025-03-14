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


from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.auth import authenticate
from app.components import network_connections
from app.components.status import get_service_status
from app.utils import get_mode, GNodeMode

import app.settings as app_settings



router = APIRouter(tags=["status"])


@router.get("", dependencies=[Depends(authenticate)])
async def status_get():
    response = {}
    response["service"] = {
        "mqbc": get_service_status(app_settings.MQBC_SERVICE_NAME),
        "m2eb": get_service_status(app_settings.M2EB_SERVICE_NAME),
        "gcloud_client": get_service_status(app_settings.GCLOUD_SERVICE_NAME)
    }
    if get_mode() == GNodeMode.PHYSICAL:
        response["network"] = network_connections.get_network_status()
    return JSONResponse(content=response)
