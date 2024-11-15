import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.cleanup_db import run_cleanup
from app.database_setup import SessionLocal

@pytest.fixture(scope="function")
def test_client():
    with TestClient(app) as test_client:
        yield test_client
    #cleanup db
    run_cleanup()


@pytest.fixture
def default_db_session():
    session = SessionLocal()
    yield session
    session.close()  