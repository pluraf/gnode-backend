import pytest
import subprocess

from app.components.settings import Settings
from app.models.settings import SettingsModel
from app import utils


def test_settings_getters(test_client):
    settings = Settings()
    assert settings.authentication == True
    assert settings.gcloud == True


@pytest.mark.parametrize("auth, gcloud", [
    (True, True),     
    (True, False),    
    (False, True),     
    (False, False)      
])
def test_settings_setters(auth, mocker, test_client,default_db_session, gcloud):
    real_subprocess_run = subprocess.run
    def mock_subprocess_run(cmd, *args, **kwargs):
        if cmd[:3] == ["sudo", "/bin/systemctl", "start"] or \
            cmd[:3] == ["sudo", "/bin/systemctl", "stop"]:
            return subprocess.CompletedProcess(args=cmd, returncode=0, stderr="")
        # For other commands, call the real subprocess.run
        return real_subprocess_run(cmd, *args, **kwargs)
    mock_run = mocker.patch("app.components.settings.subprocess.run", side_effect=mock_subprocess_run)
    settings = Settings()
    settings.authentication = auth
    settings.gcloud = gcloud
    assert settings.authentication == auth
    assert settings.gcloud == gcloud
    assert mock_run.call_count == 1
    settings_model = default_db_session.query(SettingsModel).first()
    assert settings_model.authentication == auth
    assert settings_model.gcloud == gcloud


