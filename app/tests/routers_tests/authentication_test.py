import pytest
from sqlalchemy import exc
import os
from jsonschema import validate
from jsonschema.exceptions import ValidationError
from fastapi import HTTPException
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
import jwt

from app import settings
from app.models.settings import SettingsModel
from app.components.settings import Settings
import app.routers.authentication as authentication
import app.schemas.user as user_schema

from app.tests.utils import is_valid_jwt_token

# def generate_valid_token(test_client):
#     default_username = os.getenv("GNODE_DEFAULT_USERNAME")
#     default_password = os.getenv("GNODE_DEFAULT_PASSWORD")
#     response = test_client.post(
#         settings.TOKEN_AUTH_URL,
#         data={"username": default_username, "password": default_password},
#     )
#     return response.json()["access_token"]

def test_get_token_url_success(test_client):
    default_username = os.getenv("GNODE_DEFAULT_USERNAME")
    default_password = os.getenv("GNODE_DEFAULT_PASSWORD")
    response = test_client.post(
        settings.TOKEN_AUTH_URL,
        data={"username": default_username, "password": default_password},
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
    default_username = os.getenv("GNODE_DEFAULT_USERNAME")
    default_password = os.getenv("GNODE_DEFAULT_PASSWORD")
    Settings().api_authentication = False
    response = test_client.post(
        settings.TOKEN_AUTH_URL,
        data={"username": default_username, "password": default_password},
    )
    assert response.status_code == 204


# Currently testing functions that use Depends tag by directly providing
# the parameters instead of using the Dependentant function. 
# The actual testing of Depends functionality will happen when
# we test the actual API route that calls this function

# def test_validate_jwt_success(test_client):
#     token = generate_valid_token(test_client)
#     try:
#         authentication.validate_jwt(token)
#     except HTTPException as e:
#         pytest.fail(f"Invalid token")

# def test_validate_jwt_failure():
#     #invalid format token
#     token = "invalid token"
#     try:
#         authentication.validate_jwt(token)
#         assert False
#     except HTTPException as e:
#         assert e.status_code == 401
#         assert e.detail == "Token is not valid"
    
#     #random jwt token generated from another key
#     token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0IiwiZXhwIjo" + \
#     "iMjAyNC0xMS0xNCAxNzoyNzowNi41ODgxMDErMDA6MDAifQ.ql5Xm7ZgnfkaJpaHkKFIe0MoF6L8rRLU1_2hxj7h9P0"
#     try:
#         authentication.validate_jwt(token)
#         assert False
#     except HTTPException as e:
#         assert e.status_code == 401
#         assert e.detail == "Token is not valid"


def test_authentication_status(test_client):
    try:
        authentication.authentication_status()
    except HTTPException as e:
        pytest.fail(f"Incorrect authentication status")
    Settings().api_authentication = False

    #with authentication set as false
    try:
        authentication.authentication_status()
    except HTTPException as e:
        assert e.status_code == 301
        assert e.detail == "Authentication is disabled; this endpoint is not available."


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
    default_username = os.getenv("GNODE_DEFAULT_USERNAME")
    decoded_token = {"sub" : default_username}
    try:
        cur_user = await authentication.get_current_user(decoded_token, default_db_session )
        assert cur_user.username == os.getenv("GNODE_DEFAULT_USERNAME")
    except HTTPException as e:
        pytest.fail(f"Invalid User")

@pytest.mark.asyncio
async def test_get_current_user_failure(test_client, default_db_session ):
    # user not present
    decoded_token = {"sub" : "random_user"}
    try:
        cur_user = await authentication.get_current_user(decoded_token, default_db_session )
        assert False
    except HTTPException as e:
        assert e.status_code == 401
        assert e.detail == "Could not validate credentials"


# def test_load_private_key_from_file_failure():
#     old_private_key_path = os.getenv("GNODE_PRIVATE_KEY_PATH")

#     # unset environment variable
#     os.environ.pop("GNODE_PRIVATE_KEY_PATH", None)
#     try:
#         authentication.load_private_key_from_file()
#         assert False
#     except RuntimeError as e:
#         assert str(e) == "GNODE_PRIVATE_KEY_PATH not set!"

#     # set a non exixting file path
#     os.environ['GNODE_PRIVATE_KEY_PATH'] = './randompath/random_file.txt'
#     try:
#         authentication.load_private_key_from_file()
#         assert False
#     except FileNotFoundError:
#         assert True

#     test_file_path = "./app/tests/resources/test.pem"
    
#     # test invalid key file
#     with open(test_file_path, "w") as file:
#         file.write("Test file.\n")
#     os.environ['GNODE_PRIVATE_KEY_PATH'] = test_file_path
#     try:
#         authentication.load_private_key_from_file()
#         assert False
#     except RuntimeError as e:
#         assert "GNODE_PRIVATE_KEY: Invalid PEM file or key format." in str(e)
#     os.remove(test_file_path)

#     os.environ['GNODE_PRIVATE_KEY_PATH'] = old_private_key_path

    
# def test_load_private_key_from_file_success():
#     old_private_key_path = os.getenv("GNODE_PRIVATE_KEY_PATH")

#     test_file_path = "./app/tests/resources/test_private_key.pem"
    
#     private_key = ec.generate_private_key(ec.SECP256R1())
#     private_key_pem = private_key.private_bytes(
#         encoding=serialization.Encoding.PEM,
#         format=serialization.PrivateFormat.PKCS8,
#         encryption_algorithm=serialization.NoEncryption()  # No password encryption
#     )

#     with open(test_file_path, "wb") as pem_file:
#         pem_file.write(private_key_pem)
   
#     os.environ['GNODE_PRIVATE_KEY_PATH'] = test_file_path
#     read_key = authentication.load_private_key_from_file()
#     read_key_pem = read_key.private_bytes(
#         encoding=serialization.Encoding.PEM,
#         format=serialization.PrivateFormat.PKCS8,
#         encryption_algorithm=serialization.NoEncryption()
#     )
#     assert private_key_pem == read_key_pem
#     os.remove(test_file_path)
#     os.environ['GNODE_PRIVATE_KEY_PATH'] = old_private_key_path

    
# def test_load_public_key_from_file_failure():
#     old_public_key_path = os.getenv("GNODE_PUBLIC_KEY_PATH")

#     # unset environment variable
#     os.environ.pop("GNODE_PUBLIC_KEY_PATH", None)
#     try:
#         authentication.load_public_key_from_file()
#         assert False
#     except RuntimeError as e:
#         assert str(e) == "GNODE_PUBLIC_KEY_PATH not set!"

#     # set a non exixting file path
#     os.environ['GNODE_PUBLIC_KEY_PATH'] = './randompath/random_file.txt'
#     try:
#         authentication.load_public_key_from_file()
#         assert False
#     except FileNotFoundError:
#         assert True

#     test_file_path = "./app/tests/resources/test.pem"
    
#     # test invalid key file
#     with open(test_file_path, "w") as file:
#         file.write("Test file.\n")
#     os.environ['GNODE_PUBLIC_KEY_PATH'] = test_file_path
#     try:
#         authentication.load_public_key_from_file()
#         assert False
#     except RuntimeError as e:
#         assert "GNODE_PUBLIC_KEY: Invalid PEM file or key format." in str(e)
#     os.remove(test_file_path)

#     os.environ['GNODE_PUBLIC_KEY_PATH'] = old_public_key_path

    
# def test_load_public_key_from_file_success():
#     old_public_key_path = os.getenv("GNODE_PUBLIC_KEY_PATH")

#     test_file_path = "./app/tests/resources/test_public_key.pem"
    
#     private_key = ec.generate_private_key(ec.SECP256R1())
#     public_key = private_key.public_key()
#     public_key_pem = public_key.public_bytes(
#         encoding=serialization.Encoding.PEM,
#         format=serialization.PublicFormat.SubjectPublicKeyInfo
#     )

#     with open(test_file_path, "wb") as pem_file:
#         pem_file.write(public_key_pem)
   
#     os.environ['GNODE_PUBLIC_KEY_PATH'] = test_file_path
#     read_key = authentication.load_public_key_from_file()
#     read_key_pem = read_key.public_bytes(
#         encoding=serialization.Encoding.PEM,
#         format=serialization.PublicFormat.SubjectPublicKeyInfo
#     )
#     assert public_key_pem == read_key_pem
#     os.remove(test_file_path)
#     os.environ['GNODE_PUBLIC_KEY_PATH'] = old_public_key_path

def test_authenticate_user(test_client, default_db_session):
    default_username = os.getenv("GNODE_DEFAULT_USERNAME")
    default_password = os.getenv("GNODE_DEFAULT_PASSWORD")
    
    # Correct data
    result = authentication.authenticate_user(
        default_db_session,
        default_username,
        default_password
    )
    assert result.username == default_username

    # Invalid user
    result = authentication.authenticate_user(
        default_db_session,
        "random_user",
        "random_pass"
    )
    assert not result

    # wrong password
    result = authentication.authenticate_user(
        default_db_session,
        default_username,
        "random_pass"
    )
    assert not result

# def test_create_access_token():
#     payload = {
#         "sub" : "test",
#         "attr" : "val"
#     }
#     token = authentication.create_access_token(payload)
#     decoded_payload = jwt.decode(token, options={"verify_signature": False})
#     assert all(key in decoded_payload and decoded_payload[key] == value for key, value in payload.items())