# SPDX-License-Identifier: BSD-3-Clause
#
# Copyright (c) 2024-2025 Pluraf Embedded AB <code@pluraf.com>
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its contributors
# may be used to endorse or promote products derived from this software without
# specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS “AS IS”
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
# OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
# OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
# EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


import io

from fastapi import APIRouter, Form, File, Depends, UploadFile, HTTPException, status, Response
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import JSONResponse, StreamingResponse
from typing import Optional, List

from sqlalchemy import exc
from sqlalchemy.orm import sessionmaker

import app.settings as settings
import app.schemas.device as device_schema
from app.models.device import Device, DeviceData
from app.database_setup import default_engine
from app.auth import authenticate


router = APIRouter(tags=["device"])


oauth2_scheme = OAuth2PasswordBearer(tokenUrl=settings.TOKEN_AUTH_URL)


@router.post("/{device_id}", dependencies=[Depends(authenticate)])
async def device_create(
    device_id: str,
    device: device_schema.DeviceCreateRequest
):
    device = Device(
        id=device_id,
        type=device.type,
        enabled=device.enabled,
        description=device.description,
    )

    session = sessionmaker(bind=default_engine)()
    session.add(device)
    try:
        session.commit()
    except exc.IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Device [{}] already exist".format(device_id),
        )
    finally:
        session.close()

    return Response(status_code=200)


@router.get(
    "/",
    response_model=list[device_schema.DeviceListResponse],
    dependencies=[Depends(authenticate)]
)
async def device_list():
    session = sessionmaker(bind=default_engine)()
    try:
        return session.query(Device).all()
    finally:
        session.close()


@router.get(
    "/{device_id}",
    response_model=device_schema.DeviceDetailsResponse,
    dependencies=[Depends(authenticate)]
)
async def device_details(
    device_id: str
):
    session = sessionmaker(bind=default_engine)()
    device = session.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    session.close()
    return device


@router.delete("/{device_id}", dependencies=[Depends(authenticate)])
async def device_delete(device_id: str):
    session = sessionmaker(bind=default_engine)()
    try:
        session.query(Device).filter(Device.id == device_id).delete()
        session.commit()
    except exc.IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="One or more devices could not be deleted",
        )

    session.close()
    return Response(status_code=200)


@router.put("/{device_id}", dependencies=[Depends(authenticate)])
async def device_edit(
    device_id: str,
    input: device_schema.DeviceUpdateRequest
):
    session = sessionmaker(bind=default_engine)()

    device = session.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )

    if device.type is not None:
        device.type = input.type
    if device.enabled is not None:
        device.enabled = input.enabled
    if device.description is not None:
        device.description = input.description

    try:
        session.commit()
    except exc.IntegrityError:
        session.rollback()
        raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="Device [{}] could not edited".format(device_id),
        )
    finally:
        session.close()

    return Response(status_code=200)


###
# Move to another API endpoints?
###

@router.get(
    "/{device_id}/frame",
    dependencies=[Depends(authenticate)]
)
async def device_data(
    device_id: str
):
    session = sessionmaker(bind=default_engine)()
    data = (session.query(DeviceData)
        .filter(DeviceData.device_id == device_id)
        .order_by(DeviceData.created.desc())
        .first()
    )
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device data not found"
        )
    session.close()

    buffer = io.BytesIO(data.blob)

    return StreamingResponse(buffer, media_type="image/png")
