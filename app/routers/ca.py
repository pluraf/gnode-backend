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


import shutil
import os

from fastapi import APIRouter, Form, File, Depends, UploadFile, HTTPException, status, Response
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import JSONResponse
from typing import Optional, List

from sqlalchemy import exc
from sqlalchemy.orm import sessionmaker

import app.settings as settings
from app.schemas.metadata import MetaDataListResponse, MetaDataDetailsResponse
from app.models.meta_data import MetaData
from app.database_setup import default_engine
from app.auth import authenticate


router = APIRouter(tags=["ca"])


oauth2_scheme = OAuth2PasswordBearer(tokenUrl=settings.TOKEN_AUTH_URL)


@router.post("/", dependencies=[Depends(authenticate)])
async def ca_add(
    cafile: UploadFile = File(...),
    ca_id: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
):
    if not ca_id:
        ca_id = cafile.filename

    if "/" in ca_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="/ is not allowed".format(ca_id),
        )

    file_meta = MetaData(
        id=ca_id,
        description=description
    )

    session = sessionmaker(bind=default_engine)()
    session.add(file_meta)
    try:
        session.commit()
    except exc.IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="File with ID [{}] already exist".format(ca_id),
        )
    finally:
        session.close()

    with open(f"/gnode/storage/ca/{ca_id}", "wb") as buffer:
        shutil.copyfileobj(cafile.file, buffer)

    return JSONResponse(content={"id": ca_id})


@router.get(
    "/",
    response_model=list[MetaDataListResponse],
    dependencies=[Depends(authenticate)]
)
async def ca_list():
    session = sessionmaker(bind=default_engine)()
    try:
        return session.query(MetaData).all()
    finally:
        session.close()


@router.delete("/{ca_id}", dependencies=[Depends(authenticate)])
async def ca_delete(ca_id: str):
    session = sessionmaker(bind=default_engine)()
    try:
        session.query(MetaData).filter(MetaData.id == ca_id).delete()
        session.commit()
    except exc.IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="One or more authentication bundles could not be deleted",
        )
    session.close()

    os.unlink(f"/gnode/storage/ca/{ca_id}")

    return Response(status_code=200)


@router.put("/{ca_id}", dependencies=[Depends(authenticate)])
async def ca_edit(
    ca_id: str,
    description: Optional[str] = Form(""),
    cafile: Optional[UploadFile] = File(None)
):
    session = sessionmaker(bind=default_engine)()

    file_meta = session.query(MetaData).filter(MetaData.id == ca_id).first()
    if not file_meta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    file_meta.description = description
    try:
        session.commit()
    except exc.IntegrityError:
        session.rollback()
        raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="Authentication bundle [{}] could not edited".format(ca_id),
        )
    finally:
        session.close()

    if cafile:
        with open(f"/gnode/storage/ca/{ca_id}", "wb") as buffer:
            shutil.copyfileobj(cafile.file, buffer)

    return JSONResponse(content={"id": ca_id})


@router.get(
    "/{ca_id}",
    response_model=MetaDataDetailsResponse,
    dependencies=[Depends(authenticate)]
)
async def ca_details(
    ca_id: str
):
    session = sessionmaker(bind=default_engine)()
    file_meta = session.query(MetaData).filter(MetaData.id == ca_id).first()
    if not file_meta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    session.close()
    return file_meta