# SPDX-License-Identifier: Apache-2.0

# Copyright (c) 2024-2026 Pluraf Embedded AB <code@pluraf.com>

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


import os
import jwt
import uuid

from datetime import datetime, timezone

from jwt.exceptions import InvalidTokenError

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidKey

from sqlalchemy.orm import sessionmaker

import app.settings as settings
from app.components.settings import Settings
from app.database_setup import default_engine
from app.models.api_token import ApiToken


oauth2_scheme = OAuth2PasswordBearer(tokenUrl=settings.TOKEN_AUTH_URL, auto_error=False)


class KeyCache:
    public_key = None
    private_key = None


def load_private_key_from_file():
    if KeyCache.private_key is not None:
        return KeyCache.private_key

    private_key_path = os.getenv("GNODE_PRIVATE_KEY_PATH")
    if not private_key_path:
        raise RuntimeError("GNODE_PRIVATE_KEY_PATH not set!")

    try:
        with open(private_key_path, "rb") as key_file:
            private_key = serialization.load_pem_private_key(
                key_file.read(), password=None, backend=default_backend()
            )
        KeyCache.private_key = private_key
        return private_key
    except (ValueError, InvalidKey) as e:
        raise RuntimeError(f"GNODE_PRIVATE_KEY: Invalid PEM file or key format. {e}")


def load_public_key_from_file():
    if KeyCache.public_key is not None:
        return KeyCache.public_key

    public_key_path = os.getenv("GNODE_PUBLIC_KEY_PATH")
    if not public_key_path:
        raise RuntimeError("GNODE_PUBLIC_KEY_PATH not set!")

    try:
        with open(public_key_path, "rb") as key_file:
            public_key = serialization.load_pem_public_key(key_file.read(), backend=default_backend())
        KeyCache.public_key = public_key
        return public_key
    except (ValueError, InvalidKey) as e:
        raise RuntimeError(f"GNODE_PUBLIC_KEY: Invalid PEM file or key format. {e}")


def verify_api_token(token):
    if not token:
        raise ValueError("token is invalid")

    session = sessionmaker(bind=default_engine)()
    api_token = session.query(ApiToken).filter(ApiToken.token == token).first()
    session.close()

    if not api_token or api_token.state != 1 or api_token.expired:
        raise InvalidTokenError("token not accepted")


async def authenticate(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
                                status_code = status.HTTP_401_UNAUTHORIZED,
                                detail = "Token is not valid",
                                headers = {"WWW-Authenticate": "Bearer"}
    )
    if Settings().api_authentication:
        if not token:
            raise credentials_exception
        try:
            jwt.get_unverified_header(token)
        except Exception:
            try:
                verify_api_token(token)
            except (InvalidTokenError, ValueError):
                raise credentials_exception
        else:
            public_key = load_public_key_from_file()
            try:
                payload = jwt.decode(
                    token,
                    public_key,
                    algorithms = settings.ALGORITHM,
                    audience = ["api", "ui"],
                    options = {"verify_aud": True, "strict_aud": False, "verify_jti": False}
                )
                if payload["aud"] == "api":
                    verify_api_token(payload.get("jti"))
            except (InvalidTokenError, ValueError) as e:
                raise credentials_exception


def create_access_token(aud, sub=None, jti=None, expires_delta=None):
    payload = dict()
    if sub:
        payload["sub"] = sub
    if expires_delta:
        payload["exp"] = datetime.now(timezone.utc) + expires_delta
    payload["jti"] = jti or uuid.uuid4().hex
    payload["aud"] = aud

    private_key = load_private_key_from_file()

    encoded_jwt = jwt.encode(payload, private_key, algorithm=settings.ALGORITHM)
    return encoded_jwt
