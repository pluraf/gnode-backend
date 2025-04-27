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


from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from app.routers import users
from app.routers import authentication
from app.routers import authbundle
from app.routers import ca
from app.routers import settings, status
from app.routers import version
from app.routers import info
from app.routers import timezones
from app.routers import channel
from app.routers import converter

import app.settings as app_settings

router = APIRouter()


@router.get("/", response_class=PlainTextResponse, include_in_schema=False)
async def retrieve_home():
    return "Welcome to G-Node!"


router.include_router(users.router, prefix="/user")
router.include_router(authentication.router, prefix="/auth")
router.include_router(authbundle.router, prefix="/authbundle")
router.include_router(ca.router, prefix="/ca")
router.include_router(settings.router, prefix="/settings")
router.include_router(version.router, prefix="/version")
router.include_router(status.router, prefix="/status")
router.include_router(info.router, prefix="/info")
router.include_router(timezones.router, prefix="/timezones")
router.include_router(channel.router, prefix="/channel")
router.include_router(converter.router, prefix="/converter")
