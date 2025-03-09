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


from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import JSONResponse, Response, PlainTextResponse
from typing import Optional

from app.routers import version
from app.utils import get_mode
from app.auth import authenticate
from app.components.channel import Channel


router = APIRouter(tags=["channel"])


@router.get("/", dependencies=[Depends(authenticate)])
async def list_channels():
    return Response(content=Channel().list(), media_type="application/json")


@router.get("/{channel_id}", dependencies=[Depends(authenticate)])
async def get_channel(channel_id: str):
    return Response(content=Channel().get(channel_id), media_type="application/json")


@router.post("/{channel_id}", dependencies=[Depends(authenticate)])
async def create_channel(channel_id: str, request: Request):
    payload = await request.body()
    response_phrase = Channel().create(channel_id, payload)
    if response_phrase:
        return PlainTextResponse(status_code=400, content=response_phrase)
    return Response()


@router.put("/{channel_id}", dependencies=[Depends(authenticate)])
async def update_channel(channel_id: str, request: Request):
    payload = await request.body()
    response_phrase = Channel().update(channel_id, payload)
    if response_phrase:
        return PlainTextResponse(status_code=400, content=response_phrase)
    return Response()


@router.delete("/{channel_id}", dependencies=[Depends(authenticate)])
async def delete_channel(channel_id: str):
    response_phrase = Channel().delete(channel_id)
    if response_phrase:
        return PlainTextResponse(status_code=400, content=response_phrase)
    return Response()