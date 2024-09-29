from typing import Annotated, Union
from fastapi import APIRouter, Body, Form, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

import jwt
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from pydantic import BaseModel, ValidationError
import app.settings as settings
import os
from datetime import datetime, timedelta, timezone

import app.crud.users as user_crud
import app.schemas.user as user_schema
from app.dependencies import get_db

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=settings.TOKEN_AUTH_URL)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class Token(BaseModel):
    access_token: str
    token_type: str


router = APIRouter()


def load_private_key_from_file():
    private_key_path = os.getenv("GNODE_PRIVATE_KEY_PASS")
    if not private_key_path:
        raise RuntimeError()

    with open(private_key_path, "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(), password=None, backend=default_backend()
        )
    return private_key


def load_public_key_from_file():
    public_key_path = os.getenv("GNODE_PUBLIC_KEY_PASS")
    if not public_key_path:
        raise RuntimeError()

    with open(public_key_path, "rb") as key_file:
        public_key = serialization.load_pem_public_key(key_file.read(), backend=default_backend())
    return public_key


def validate_jwt(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
                                status_code = status.HTTP_401_UNAUTHORIZED,
                                detail = "Token is not valid",
                                headers = {"WWW-Authenticate": "Bearer"}
                            )
    try:
        public_key = load_public_key_from_file()
        jwt.decode(token, public_key, algorithms=settings.ALGORITHM)
    except InvalidTokenError:
        raise credentials_exception


def authenticate_user(db_session, username: str, password: str):
    try:
        user = user_schema.UserAuth.model_validate(
            user_crud.get_user_by_username(db_session, username)
        )
        if not user:
            return False
        if not pwd_context.verify(password, user.hashed_password):
            return False
        return user
    except ValidationError:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not authenticate user",
        )
        raise credentials_exception


def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})

    private_key = load_private_key_from_file()

    encoded_jwt = jwt.encode(to_encode, private_key, algorithm=settings.ALGORITHM)
    return encoded_jwt


@router.post("/")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db_session: Session = Depends(get_db),
) -> Token:
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
    token: Annotated[str, Depends(oauth2_scheme)],
    db_session: Session = Depends(get_db),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        public_key = load_public_key_from_file()
        payload = jwt.decode(token, public_key, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except InvalidTokenError:
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
