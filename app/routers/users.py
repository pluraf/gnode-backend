from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Annotated, List

import app.crud.users as user_crud
import app.schemas.user as user_schema
from app.dependencies import get_db

from app.routers import authentication


router = APIRouter()


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

    return user_crud.create_user(db_session=db_session, user=user)


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


@router.delete("/", response_model=dict)
def delete_user(
    userids: List[int],
    current_user: Annotated[user_schema.User, Depends(authentication.get_current_active_user)],
    db_session: Session = Depends(get_db),
):
    if not current_user.is_admin:
        raise HTTPException(status_code=400, detail="Unauthorized action")

    deleted = []

    for userid in userids:
        if current_user.id == userid and (not current_user.is_admin):
            continue
        if userid == user_crud.get_first_user_id(db_session):
            continue
        db_user = user_crud.delete_user(db_session, user_id=userid)
        if db_user:
            deleted.append(db_user.id)

    return {"deleted": deleted}
