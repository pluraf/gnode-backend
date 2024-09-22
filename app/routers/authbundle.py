import uuid
import fcntl

from fastapi import APIRouter, Form, File, UploadFile, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Optional

from sqlalchemy import exc, create_engine, Column, String, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


Base = declarative_base()


class Authbundle(Base):
    __tablename__ = 'authbundles'
    authbundle_id = Column(String, primary_key=True)
    connector_type = Column(String)
    auth_type = Column(String)
    username = Column(String)
    password = Column(String)
    keyname = Column(String)
    keydata = Column(LargeBinary)
    description = Column(String)


router = APIRouter()


@router.post("/create")
async def authbundle_create(
    authbundle_id: Optional[str] = Form(None),
    connector_type: str = Form(...),
    auth_type: str = Form(...),
    username: Optional[str] = Form(None),
    password: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    keyfile: Optional[UploadFile] = File(None)
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

    lock = lock_db()
    engine = create_engine('sqlite:///db/authbundles.sqlite')
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
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
        unlock_db(lock)

    return JSONResponse(content={"authbundle_id": authbundle_id})


def lock_db():
    fd = open("db/authbundles.sqlite", "a+")
    fcntl.lockf(fd, fcntl.LOCK_EX)
    return fd


def unlock_db(fd):
    fcntl.lockf(fd, fcntl.LOCK_UN)
    fd.close()
