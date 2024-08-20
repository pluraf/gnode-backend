from sqlalchemy import create_engine, MetaData
from database_setup import  engine

metadata = MetaData()
metadata.reflect(bind=engine)
metadata.drop_all(bind=engine)

print("All tables dropped successfully.")
