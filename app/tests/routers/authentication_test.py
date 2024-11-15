import pytest
from sqlalchemy import exc
import os
from jsonschema import validate
from jsonschema.exceptions import ValidationError
from fastapi import HTTPException

from app import settings
from app.models.settings import SettingsModel
from app.components.settings import Settings
import app.routers.authentication as authentication
import app.schemas.user as user_schema

from app.tests.utils import is_valid_jwt_token

default_username = os.getenv("GNODE_DEFAULT_USERNAME")
default_password = os.getenv("GNODE_DEFAULT_PASSWORD")

def generate_valid_token(test_client):
    response = test_client.post(
        settings.TOKEN_AUTH_URL,
        data={"username": default_username, "password": default_password},
    )
    return response.json()["access_token"]

def test_get_token_url_success(test_client, 
    username = default_username,
    password = default_password):
    response = test_client.post(
        settings.TOKEN_AUTH_URL,
        data={"username": username, "password": password},
    )
    assert response.status_code == 200

    #validate response data
    resp_schema = {
        "type": "object",
        "properties": {
            "access_token": {"type": "string"},
            "token_type": {
                "type": "string",
                "enum" : ["bearer"]
            }
        },
        "required": ["access_token", "token_type"]
    }
    try:
        validate(instance=response.json(), schema=resp_schema)
    except ValidationError as e:
        pytest.fail(f"JSON validation error: {e}")
    token = response.json()["access_token"]
    assert is_valid_jwt_token(token)

def test_get_token_url_failure(test_client):
    response = test_client.post(
        settings.TOKEN_AUTH_URL,
        data={"username": "random", "password": "random"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"

def test_get_token_url_without_authentication(test_client, default_db_session):
    Settings().authentication = False
    response = test_client.post(
        settings.TOKEN_AUTH_URL,
        data={"username": default_username, "password": default_password},
    )
    assert response.status_code == 204

def test_validate_jwt_success(test_client):
    token = generate_valid_token(test_client)
    try:
        authentication.validate_jwt(token)
    except HTTPException as e:
        pytest.fail(f"Invalid token")

def test_validate_jwt_failure():
    #invalid format token
    token = "invalid token"
    try:
        authentication.validate_jwt(token)
        assert False
    except HTTPException as e:
        assert e.status_code == 401
        assert e.detail == "Token is not valid"
    
    #random jwt token generated from another key
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0IiwiZXhwIjo" + \
    "iMjAyNC0xMS0xNCAxNzoyNzowNi41ODgxMDErMDA6MDAifQ.ql5Xm7ZgnfkaJpaHkKFIe0MoF6L8rRLU1_2hxj7h9P0"
    try:
        authentication.validate_jwt(token)
        assert False
    except HTTPException as e:
        assert e.status_code == 401
        assert e.detail == "Token is not valid"


@pytest.mark.asyncio
async def test_get_current_active_user_success():
    test_user = user_schema.User(username= "user1", is_active=True,
        is_admin=False, id=1)
    try:
        cur_user = await authentication.get_current_active_user(test_user)
        assert cur_user.username == test_user.username
    except HTTPException as e:
        pytest.fail(f"Inactive user")

@pytest.mark.asyncio
async def test_get_current_active_user_failure():
    test_user = user_schema.User(username= "user1", is_active=False,
        is_admin=False, id=1)
    try:
        cur_user = await authentication.get_current_active_user(test_user)
        assert False
    except HTTPException as e:
        assert e.status_code == 400
        assert e.detail == "Inactive user"

@pytest.mark.asyncio
async def test_get_current_user_success(test_client, default_db_session ):
    token = generate_valid_token(test_client)
    try:
        cur_user = await authentication.get_current_user(token, default_db_session )
        assert cur_user.username == default_username
    except HTTPException as e:
        pytest.fail(f"Invalid User")

@pytest.mark.asyncio
async def test_get_current_user_failure(default_db_session ):
    #invalid format token
    token = "invalid token"
    try:
        cur_user = await authentication.get_current_user(token, default_db_session )
        assert False
    except HTTPException as e:
        assert e.status_code == 401
        assert e.detail == "Could not validate credentials"

    #random jwt token generated from another key
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0IiwiZXhwIjo" + \
    "iMjAyNC0xMS0xNCAxNzoyNzowNi41ODgxMDErMDA6MDAifQ.ql5Xm7ZgnfkaJpaHkKFIe0MoF6L8rRLU1_2hxj7h9P0"
    try:
        cur_user = await authentication.get_current_user(token, default_db_session )
        assert False
    except HTTPException as e:
        assert e.status_code == 401
        assert e.detail == "Could not validate credentials"

def test_authentication_status(test_client):
    try:
        authentication.authentication_status()
    except HTTPException as e:
        pytest.fail(f"Incorrect authentication status")
    Settings().authentication = False

    #with authentication set as false
    try:
        authentication.authentication_status()
    except HTTPException as e:
        assert e.status_code == 301
        assert e.detail == "Authentication is disabled; this endpoint is not available."


