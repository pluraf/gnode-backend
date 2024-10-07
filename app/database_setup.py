import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

GNODE_DATABASE_URL = "sqlite:///" + os.getenv("GNODE_DB_DIR") + "/gnode.sqlite"
AUTHBUNDLE_DATABASE_URL = "sqlite:///" + os.getenv("GNODE_DB_DIR") + "/authbundles.sqlite"

default_engine = create_engine(GNODE_DATABASE_URL, connect_args={"check_same_thread": False})
auth_engine = create_engine(AUTHBUNDLE_DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=default_engine)

DefaultBase = declarative_base()
AuthBase = declarative_base()
