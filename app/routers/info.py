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

from app.routers import version
from app.utils import get_mode
from app.auth import authenticate


router = APIRouter(tags=["info"])


@router.get("", dependencies=[Depends(authenticate)])
async def get_info():
    mode = get_mode()
    api_versions = "{}.{}.{}".format(
        version.get_gnode_api_version(),
        version.get_m2eb_api_version(),
        version.get_mqbc_api_version()
    )
    gnode_serial_number = version.get_serial_number()

    return {
        "mode": mode,
        "version": api_versions,
        "serial_number": gnode_serial_number
    }