from sqlalchemy import MetaData
from app.database_setup import default_engine, auth_engine

def cleanup_engine(engine):
    metadata = MetaData()
    metadata.reflect(bind=engine)
    metadata.drop_all(bind=engine)

def run_cleanup():
    cleanup_engine(default_engine)
    cleanup_engine(auth_engine)

if __name__ == "__main__":
    run_cleanup()
    print("All tables dropped successfully.")
