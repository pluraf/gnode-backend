import pytest

def test_main_url(test_client):
    response = test_client.get("/")
    assert response.status_code == 200
    assert response.text == "Welcome to G-Node!"
