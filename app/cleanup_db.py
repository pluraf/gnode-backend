from sqlalchemy import MetaData
from database_setup import default_engine, auth_engine

metadata = MetaData()
metadata.reflect(bind=default_engine)
metadata.drop_all(bind=default_engine)

metadata = MetaData()
metadata.reflect(bind=auth_engine)
metadata.drop_all(bind=auth_engine)

print("All tables dropped successfully.")
