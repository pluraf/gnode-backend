from sqlalchemy import Boolean, Column, Integer, String

from app.database_setup import Base


class UserModel(Base):
    __tablename__ = "gnode_users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
