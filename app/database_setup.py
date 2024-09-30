import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

SQLALCHEMY_DATABASE_URL = os.getenv("GNODE_DB_URL")

default_engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
auth_engine = create_engine("sqlite:///db/authbundles.sqlite", connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=default_engine)

DefaultBase = declarative_base()
AuthBase = declarative_base()
