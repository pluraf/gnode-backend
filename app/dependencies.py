from sqlalchemy.orm import Session
from app.database_setup import SessionLocal, Base, engine


def get_db():
    # init DB
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
