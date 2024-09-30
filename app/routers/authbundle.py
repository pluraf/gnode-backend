import uuid

from fastapi import APIRouter, Form, File, Depends, UploadFile, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Optional

from sqlalchemy import exc
from sqlalchemy.orm import sessionmaker

import app.schemas.autbundle as autbundle_schema
from app.routers import authentication
from app.models.authbundle import Authbundle
from app.database_setup import auth_engine


router = APIRouter()


@router.post("/")
async def authbundle_create(
    authbundle_id: Optional[str] = Form(None),
    connector_type: str = Form(...),
    auth_type: str = Form(...),
    username: Optional[str] = Form(None),
    password: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    keyfile: Optional[UploadFile] = File(None),
    _: str = Depends(authentication.validate_jwt)
):
    if not authbundle_id:
        authbundle_id = uuid.uuid4().hex

    autbundle = Authbundle(
        authbundle_id=authbundle_id,
        connector_type=connector_type,
        auth_type=auth_type,
        description=description,
        username=username,
        password=password
    )

    if (keyfile):
        content = await keyfile.read()
        autbundle.keyname=keyfile.filename
        autbundle.keydata=content

    session = sessionmaker(bind=auth_engine)()
    session.add(autbundle)
    try:
        session.commit()
        authbundle_id = autbundle.authbundle_id
    except exc.IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Authentication bundle [{}] already exist".format(authbundle_id),
        )
    finally:
        session.close()

    return JSONResponse(content={"authbundle_id": authbundle_id})


@router.get("/", response_model=list[autbundle_schema.AuthbundleListResponse])
async def authbundle_list(_: str = Depends(authentication.validate_jwt)):
    session = sessionmaker(bind=auth_engine)()
    try:
        return session.query(Authbundle).all()
    finally:
        session.close()
