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
    first_username = os.getenv("GNODE_FIRST_USER_NAME")
    first_user_pswd = os.getenv("GNODE_FIRST_USER_PSWD")
    user = get_user_by_username(db_session, first_username)
    if user is None:
        user = user_schema.UserCreate(
            username=first_username, password=first_user_pswd, is_admin=True
        )
        create_user(db_session, user)
    return

def get_first_user_id(db_session: Session):
    first_username = os.getenv("GNODE_FIRST_USER_NAME")
    user = get_user_by_username(db_session, first_username)
    return user.id
