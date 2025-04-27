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


import secrets
import string
import time

from typing import Annotated, Optional
from fastapi import APIRouter, Body, Form, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker
from sqlalchemy import exc

from passlib.context import CryptContext
from pydantic import BaseModel, ValidationError
import app.settings as settings
from datetime import datetime, timedelta, timezone

import app.crud.users as user_crud
import app.schemas.user as user_schema
import app.schemas.api_token as api_token_schema

from app.dependencies import get_db
from app.auth import authenticate, create_access_token
from app.database_setup import default_engine
from app.components.settings import Settings
from app.models.api_token import ApiToken, ApitokenState



oauth2_scheme = OAuth2PasswordBearer(tokenUrl=settings.TOKEN_AUTH_URL)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class Token(BaseModel):
    access_token: str
    token_type: str


router = APIRouter(tags=["authentication"])


def authentication_status():
    if not Settings().api_authentication:
        raise HTTPException(
            status_code=status.HTTP_301_MOVED_PERMANENTLY,
            detail="Authentication is disabled; this endpoint is not available."
        )


def authenticate_user(db_session, username: str, password: str):
    try:
        user = user_crud.get_user_by_username(db_session, username)
        if not user:
            return None
        user = user_schema.UserAuth.model_validate(user)
        if not pwd_context.verify(password, user.hashed_password):
            return None
        return user
    except ValidationError:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not authenticate user",
        )
        raise credentials_exception


async def get_current_user(
    decoded_token = Depends(authenticate),
    db_session: Session = Depends(get_db),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    username = decoded_token.get("sub")
    if username is None:
        raise credentials_exception
    try:
        user = user_schema.User.model_validate(
            user_crud.get_user_by_username(db_session, username)
        )
    except ValidationError:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[user_schema.User, Depends(get_current_user)],
):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@router.api_route("/token", methods=["GET"])
async def login_for_access_token():
    if not Settings().api_authentication:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return Response(status_code=status.HTTP_405_METHOD_NOT_ALLOWED)


@router.api_route("/token", methods=["POST"])
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db_session: Session = Depends(get_db)
) -> Token:
    if not Settings().api_authentication:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    user = authenticate_user(db_session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token("ui", sub=user.username, expires_delta=access_token_expires)
    return Token(access_token=access_token, token_type="bearer")


@router.post("/apitoken", dependencies=[Depends(authenticate)])
async def create_api_token(request: api_token_schema.ApiTokenRequest):
    characters = string.ascii_letters + string.digits
    now = int(time.time())
    till = now + request.duration * 86400 if request.duration else 0
    session = sessionmaker(bind=default_engine)()
    for _ in range(2):
        token = ''.join(secrets.choice(characters) for _ in range(50))
        api_token = ApiToken(
            token=token,
            state=request.description or 1,
            created=now,
            till=till,
            description=request.description
        )
        session.add(api_token)
        try:
            session.commit()
        except exc.IntegrityError:
            session.rollback()
            continue
        api_token.id
        session.close()
        break
    else:
        raise HTTPException(status_code=500)

    return JSONResponse(content={"apitoken_id": api_token.id})


@router.get("/apitoken/", dependencies=[Depends(authenticate)])
async def list_apitoken():
    session = sessionmaker(bind=default_engine)()
    try:
        return session.query(ApiToken).all()
    finally:
        session.close()


@router.get("/apitoken/{apitoken_id}", dependencies=[Depends(authenticate)])
async def get_apitoken(
    apitoken_id: str
):
    session = sessionmaker(bind=default_engine)()
    apitoken = session.query(ApiToken).filter(ApiToken.id == apitoken_id).first()
    if not apitoken:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Apitoken not found"
        )
    session.close()
    return apitoken


@router.put("/apitoken/{apitoken_id}", dependencies=[Depends(authenticate)])
async def update_apitoken(
    apitoken_id: str,
    state: ApitokenState = Body(...),
    duration: int = Body(...),
    description: Optional[str] = Body(...),
):
    session = sessionmaker(bind=default_engine)()
    apitoken = session.query(ApiToken).filter(ApiToken.id == apitoken_id).first()
    if not apitoken:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Apitoken not found"
        )

    apitoken.state = state
    apitoken.till = apitoken.created + duration * 86400 if duration else 0
    if description:
        apitoken.description = description

    try:
        session.commit()
    except exc.IntegrityError:
        session.rollback()
        raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="Apitoken [{}] can not be updated".format(apitoken_id),
        )
    finally:
        session.close()

    return apitoken


@router.delete("/apitoken/{apitoken_id}", dependencies=[Depends(authenticate)])
async def delete_apitoken(apitoken_id: int):
    session = sessionmaker(bind=default_engine)()
    try:
        session.query(ApiToken).filter(ApiToken.id == apitoken_id).delete()
        session.commit()
    except exc.IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Apitoken could not be deleted",
        )
    finally:
        session.close()

    return Response(status_code=200)
