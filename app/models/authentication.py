from sqlalchemy import Boolean, Column

from app.database_setup import DefaultBase


class AuthenticationModel(DefaultBase):
    __tablename__ = "authentication"

    is_authentication_required = Column(Boolean, primary_key=True, default=True)