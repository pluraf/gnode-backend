from app.database_setup import AuthBase
from sqlalchemy import Column, String, LargeBinary


class Authbundle(AuthBase):
    __tablename__ = 'authbundles'
    authbundle_id = Column(String, primary_key=True)
    service_type = Column(String)
    auth_type = Column(String)
    username = Column(String)
    password = Column(String)
    keyname = Column(String)
    keydata = Column(LargeBinary)
    description = Column(String)
