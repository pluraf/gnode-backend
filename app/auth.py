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


import jwt
import os

from datetime import datetime, timezone, timedelta

from jwt.exceptions import InvalidTokenError

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidKey

import app.settings as settings
from app.components.settings import Settings


oauth2_scheme = OAuth2PasswordBearer(tokenUrl=settings.TOKEN_AUTH_URL, auto_error=False)


def load_private_key_from_file():
    private_key_path = os.getenv("GNODE_PRIVATE_KEY_PATH")
    if not private_key_path:
        raise RuntimeError("GNODE_PRIVATE_KEY_PATH not set!")

    try:
        with open(private_key_path, "rb") as key_file:
            private_key = serialization.load_pem_private_key(
                key_file.read(), password=None, backend=default_backend()
            )
        return private_key
    except (ValueError, InvalidKey) as e:
        raise RuntimeError(f"GNODE_PRIVATE_KEY: Invalid PEM file or key format. {e}")


def load_public_key_from_file():
    public_key_path = os.getenv("GNODE_PUBLIC_KEY_PATH")
    if not public_key_path:
        raise RuntimeError("GNODE_PUBLIC_KEY_PATH not set!")

    try:
        with open(public_key_path, "rb") as key_file:
            public_key = serialization.load_pem_public_key(key_file.read(), backend=default_backend())
        return public_key
    except (ValueError, InvalidKey) as e:
        raise RuntimeError(f"GNODE_PUBLIC_KEY: Invalid PEM file or key format. {e}")


async def authenticate(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
                                status_code = status.HTTP_401_UNAUTHORIZED,
                                detail = "Token is not valid",
                                headers = {"WWW-Authenticate": "Bearer"}
    )
    if Settings().api_authentication:
        if not token:
            raise credentials_exception
        public_key = load_public_key_from_file()
        try:
            return jwt.decode(token, public_key, algorithms=settings.ALGORITHM)
        except InvalidTokenError:
            raise credentials_exception
    return None


def create_access_token(data, expires_delta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})

    private_key = load_private_key_from_file()

    encoded_jwt = jwt.encode(to_encode, private_key, algorithm=settings.ALGORITHM)
    return encoded_jwt
