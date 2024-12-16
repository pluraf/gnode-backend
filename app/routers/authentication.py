from typing import Annotated, Union
from fastapi import APIRouter, Body, Form, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from passlib.context import CryptContext
from pydantic import BaseModel, ValidationError
import app.settings as settings
import os
from datetime import datetime, timedelta, timezone

import app.crud.users as user_crud
import app.schemas.user as user_schema
from app.dependencies import get_db
from app.auth import authenticate, create_access_token

from app.components.settings import Settings


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


@router.api_route("/", methods=["GET"])
async def login_for_access_token():
    if not Settings().api_authentication:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return Response(status_code=status.HTTP_405_METHOD_NOT_ALLOWED)


@router.api_route("/", methods=["POST"])
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
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


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
