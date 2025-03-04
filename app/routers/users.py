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


from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Annotated, List

import app.crud.users as user_crud
import app.schemas.user as user_schema
from app.dependencies import get_db

from app.routers import authentication


router = APIRouter(
    tags=["user"],
    dependencies=[Depends(authentication.authentication_status)]
)


@router.post("/", response_model=user_schema.User)
def create_user(
    current_user: Annotated[user_schema.User, Depends(authentication.get_current_active_user)],
    user: user_schema.UserCreate,
    db_session: Session = Depends(get_db),
):
    # Only admin users can create new users
    if current_user is None or (not current_user.is_admin):
        raise HTTPException(
            status_code=400, detail="Only admin users are authorized to create new users"
        )

    try:
        return user_crud.create_user(db_session=db_session, user=user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500)


@router.get("/", response_model=list[user_schema.User])
def read_all_users(
    current_user: Annotated[user_schema.User, Depends(authentication.get_current_active_user)],
    skip: int = 0,
    limit: int = 100,
    db_session: Session = Depends(get_db),
):
    if current_user is None:
        raise HTTPException(status_code=400, detail="Only active users are authorized")
    users = user_crud.get_users(db_session, skip=skip, limit=limit)
    return users


@router.get("/{user_id}", response_model=user_schema.User)
def read_user(
    user_id: int,
    current_user: Annotated[user_schema.User, Depends(authentication.get_current_active_user)],
    db_session: Session = Depends(get_db),
):
    if current_user is None:
        raise HTTPException(status_code=400, detail="Only active users are authorized")
    db_user = user_crud.get_user(db_session, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@router.delete("/{user_id}", response_model=user_schema.User)
def delete_user(
    user_id: int,
    current_user: Annotated[user_schema.User, Depends(authentication.get_current_active_user)],
    db_session: Session = Depends(get_db),
):
    if current_user.id != user_id and (not current_user.is_admin):
        raise HTTPException(status_code=400, detail="Unauthorized action")
    if user_id == user_crud.get_first_user_id(db_session):
        raise HTTPException(status_code=400, detail="Cannot delete first user")
    db_user = user_crud.delete_user(db_session, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user
