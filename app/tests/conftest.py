import pytest
from fastapi.testclient import TestClient
import os

from app.main import app
from app.cleanup_db import run_cleanup
from app.database_setup import SessionLocalDefault

@pytest.fixture(scope="function")
def test_client(mocker):
    mock_settings_zmq_send = mocker.patch("app.components.settings.send_zmq_request", return_value = "ok")
    with TestClient(app) as test_client:
        yield test_client
    #cleanup db
    run_cleanup()


@pytest.fixture
def default_db_session():
    session = SessionLocalDefault()
    yield session
    session.close()

# Replace db environment value with test db values for entire test session
@pytest.fixture(scope="session", autouse=True)
def set_test_env_vars():
    os.environ["GNODE_DEFAULT_USERNAME"] = "test"
    os.environ["GNODE_DEFAULT_PASSWORD"] = "test"
    os.environ["GNODE_DB_DIR"] = "./app/tests/db/"
    yield
