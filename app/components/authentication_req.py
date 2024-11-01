from fastapi import HTTPException

from sqlalchemy import exc
from sqlalchemy.orm import Session, sessionmaker

from app.models.authentication import AuthenticationModel
from app.database_setup import default_engine



def initialize_authentication_setting(db_session: Session):
    authentication_required = db_session.query(AuthenticationModel).first()
    if authentication_required is None:
        authentication_required = AuthenticationModel(is_authentication_required=True)
        db_session.add(authentication_required)
        db_session.commit()
    db_session.close()


def update_authentication_required(value: bool):
    session = sessionmaker(bind=default_engine)()

    try:
        db = session.query(AuthenticationModel).first()

        db.is_authentication_required = value
        session.commit()
        return db.is_authentication_required
    except exc.SQLAlchemyError:
        session.rollback()
        raise HTTPException(status_code=500, detail="Failed to update authentication required")
    finally:
        session.close()


def get_authentication_required():
    session = sessionmaker(bind=default_engine)()

    try:
        return bool(session.query(AuthenticationModel).filter(AuthenticationModel.is_authentication_required).first())
    finally:
        session.close()