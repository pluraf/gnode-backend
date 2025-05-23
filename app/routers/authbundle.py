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


import uuid

from fastapi import APIRouter, Form, File, Depends, UploadFile, HTTPException, status, Response
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import JSONResponse
from typing import Optional, List

from sqlalchemy import exc
from sqlalchemy.orm import sessionmaker

import app.settings as settings
import app.schemas.autbundle as autbundle_schema
from app.models.authbundle import Authbundle
from app.database_setup import auth_engine
from app.auth import authenticate


router = APIRouter(tags=["authbundle"])


oauth2_scheme = OAuth2PasswordBearer(tokenUrl=settings.TOKEN_AUTH_URL)


@router.post("/", dependencies=[Depends(authenticate)])
async def authbundle_create(
    authbundle_id: Optional[str] = Form(None),
    service_type: str = Form(...),
    auth_type: str = Form(...),
    username: Optional[str] = Form(None),
    password: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    keyfile: Optional[UploadFile] = File(None)
):
    if not authbundle_id:
        authbundle_id = uuid.uuid4().hex

    authbundle = Authbundle(
        authbundle_id=authbundle_id,
        service_type=service_type,
        auth_type=auth_type,
        description=description,
        username=username,
        password=password
    )

    if (keyfile):
        content = await keyfile.read()
        authbundle.keyname=keyfile.filename
        authbundle.keydata=content

    session = sessionmaker(bind=auth_engine)()
    session.add(authbundle)
    try:
        session.commit()
        authbundle_id = authbundle.authbundle_id
    except exc.IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Authentication bundle [{}] already exist".format(authbundle_id),
        )
    finally:
        session.close()

    return JSONResponse(content={"authbundle_id": authbundle_id})


@router.get(
    "/",
    response_model=list[autbundle_schema.AuthbundleListResponse],
    dependencies=[Depends(authenticate)]
)
async def authbundle_list():
    session = sessionmaker(bind=auth_engine)()
    try:
        return session.query(Authbundle).all()
    finally:
        session.close()


@router.delete("/{authbundle_id}", dependencies=[Depends(authenticate)])
async def authbundle_delete(authbundle_id: str):
    session = sessionmaker(bind=auth_engine)()
    try:
        session.query(Authbundle).filter(Authbundle.authbundle_id == authbundle_id).delete()
        session.commit()
    except exc.IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="One or more authentication bundles could not be deleted",
        )

    session.close()
    return Response(status_code=200)


@router.put("/{authbundle_id}", dependencies=[Depends(authenticate)])
async def authbundle_edit(
    authbundle_id: str,
    service_type: str = Form(...),
    auth_type: str = Form(...),
    username: Optional[str] = Form(None),
    password: Optional[str] = Form(None),
    description: Optional[str] = Form(""),
    keyfile: Optional[UploadFile] = File(None)
):
    session = sessionmaker(bind=auth_engine)()

    authbundle = session.query(Authbundle).filter(Authbundle.authbundle_id == authbundle_id).first()
    if not authbundle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Authentication bundle not found"
        )

    if username:
        authbundle.username = username
    if password:
        authbundle.password = password
    authbundle.description = description
    if keyfile:
        content = await keyfile.read()
        authbundle.keyname = keyfile.filename
        authbundle.keydata = content
    if service_type:
        authbundle.service_type = service_type
    if auth_type:
        authbundle.auth_type = auth_type

    try:
        session.commit()
    except exc.IntegrityError:
        session.rollback()
        raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="Authentication bundle [{}] could not edited".format(authbundle_id),
        )
    finally:
        session.close()

    return JSONResponse(content={"authbundle_id": authbundle_id})


@router.get(
    "/{authbundle_id}",
    response_model=autbundle_schema.AuthbundleDetailsResponse,
    dependencies=[Depends(authenticate)]
)
async def authbundle_details(
    authbundle_id: str
):
    session = sessionmaker(bind=auth_engine)()
    authbundle = session.query(Authbundle).filter(Authbundle.authbundle_id == authbundle_id).first()
    if not authbundle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Authentication bundle not found"
        )
    session.close()
    return authbundle