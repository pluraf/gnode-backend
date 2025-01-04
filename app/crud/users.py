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


import os

from sqlalchemy.orm import Session
from passlib.hash import bcrypt

from app.models.user import UserModel
import app.schemas.user as user_schema


def get_user(db_session: Session, user_id: int):
    return db_session.query(UserModel).filter(UserModel.id == user_id).first()


def get_user_by_username(db_session: Session, username: str):
    return db_session.query(UserModel).filter(UserModel.username == username).first()


def get_users(db_session: Session, skip: int = 0, limit: int = 100):
    return db_session.query(UserModel).offset(skip).limit(limit).all()


def create_user(db_session: Session, user: user_schema.UserCreate):
    # Check is user exists
    existing_user = get_user_by_username(db_session, user.username)
    if existing_user:
        raise ValueError("Username already exist")

    hashed_password = bcrypt.hash(user.password)
    db_user = UserModel(
        username=user.username, hashed_password=hashed_password, is_admin=user.is_admin
    )
    db_session.add(db_user)
    db_session.commit()
    db_session.refresh(db_user)
    return db_user


def delete_user(db_session: Session, user_id: int):
    user = get_user(db_session, user_id)
    if user is None:
        return user
    db_session.delete(user)
    db_session.commit()
    return user


def load_first_user(db_session: Session):
    first_username = os.getenv("GNODE_DEFAULT_USERNAME")
    first_user_pswd = os.getenv("GNODE_DEFAULT_PASSWORD")
    user = get_user_by_username(db_session, first_username)
    if user is None:
        user = user_schema.UserCreate(
            username=first_username, password=first_user_pswd, is_admin=True
        )
        create_user(db_session, user)
    return

def get_first_user_id(db_session: Session):
    first_username = os.getenv("GNODE_DEFAULT_USERNAME")
    user = get_user_by_username(db_session, first_username)
    return user.id
