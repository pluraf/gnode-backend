# SPDX-License-Identifier: Apache-2.0

# Copyright (c) 2025 Pluraf Embedded AB <code@pluraf.com>

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


import uuid

from fastapi import APIRouter, Form, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import JSONResponse
from typing import Optional, List

from sqlalchemy import exc
from sqlalchemy.orm import sessionmaker

import app.settings as settings
import app.schemas.converter as converter_schema
from app.models.converter import Converter
from app.database_setup import default_engine
from app.auth import authenticate


router = APIRouter(tags=["converter"])


oauth2_scheme = OAuth2PasswordBearer(tokenUrl=settings.TOKEN_AUTH_URL)


@router.post("/", dependencies=[Depends(authenticate)])
async def converter_create(
    converter_id: Optional[str] = Form(None),
    code: str = Form(...),
    description: Optional[str] = Form(None),
):
    if not converter_id:
        converter_id = uuid.uuid4().hex

    converter = Converter(
        id=converter_id,
        code=code,
        description=description
    )

    session = sessionmaker(bind=default_engine)()
    session.add(converter)
    try:
        session.commit()
        converter_id = converter.id
    except exc.IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Converter [{}] already exist".format(converter_id),
        )
    finally:
        session.close()

    return JSONResponse(content={"converter_id": converter_id})


@router.get(
    "/",
    response_model=list[converter_schema.ConverterListResponse],
    dependencies=[Depends(authenticate)]
)
async def converter_list():
    session = sessionmaker(bind=default_engine)()
    try:
        return session.query(Converter).all()
    finally:
        session.close()


@router.delete("/{converter_id}", dependencies=[Depends(authenticate)])
async def converter_delete(converter_id: str):
    session = sessionmaker(bind=default_engine)()
    try:
        session.query(Converter).filter(Converter.id == converter_id).delete()
        session.commit()
    except exc.IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="One or more converters could not be deleted",
        )
    session.close()
    return Response(status_code=200)


@router.put("/{converter_id}", dependencies=[Depends(authenticate)])
async def converter_edit(
    converter_id: str,
    code: str = Form(...),
    description: Optional[str] = Form(None),
):
    session = sessionmaker(bind=default_engine)()

    converter = session.query(Converter).filter(Converter.id == converter_id).first()
    if not converter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Converter not found"
        )

    converter.code = code
    if description is not None:
        converter.description = description

    try:
        session.commit()
    except exc.IntegrityError:
        session.rollback()
        raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="Converter [{}] could not edited".format(converter_id),
        )
    finally:
        session.close()

    return JSONResponse(content={"converter_id": converter_id})


@router.get(
    "/{converter_id}",
    response_model=converter_schema.ConverterDetailsResponse,
    dependencies=[Depends(authenticate)]
)
async def converter_details(
    converter_id: str
):
    session = sessionmaker(bind=default_engine)()
    converter = session.query(Converter).filter(Converter.id == converter_id).first()
    if not converter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Converter not found"
        )
    session.close()
    return converter
