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


import json

from fastapi import status, APIRouter, Depends, Body, Request, HTTPException
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
    channel = Channel().get(channel_id)
    if channel is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Channel not found"
        )
    return Response(content=channel, media_type="application/json")


@router.post("/", dependencies=[Depends(authenticate)])
async def create_channel(_: dict = Body(...)):
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing channel ID!")


@router.post("/{channel_id}", dependencies=[Depends(authenticate)])
async def create_channel(channel_id: str, payload: dict = Body(...)):
    try:
        response_phrase = Channel().create(channel_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    if response_phrase:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=response_phrase)
    return Response()


@router.put("/{channel_id}", dependencies=[Depends(authenticate)])
async def update_channel(channel_id: str, request: Request):
    payload = await request.body()
    try:
        response_phrase = Channel().update(channel_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    if response_phrase:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=response_phrase)
    return Response()


@router.delete("/{channel_id}", dependencies=[Depends(authenticate)])
async def delete_channel(channel_id: str):
    response_phrase = Channel().delete(channel_id)
    if response_phrase:
        return PlainTextResponse(status_code=400, content=response_phrase)
    return Response()