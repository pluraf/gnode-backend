import pytest
from unittest.mock import patch
import subprocess

from app import settings
from app.models.settings import SettingsModel
from app.components.settings import Settings
from app import utils
from app.components.status import ServiceStatus

@pytest.mark.parametrize("gcloud_status", [
    (ServiceStatus.RUNNING),   
    (ServiceStatus.STOPPED),
    (ServiceStatus.MALFORMED),
    (ServiceStatus.FAILED)
])
def test_settings_getters_with_empty_db(test_client, gcloud_status):
    with patch("app.components.settings.get_service_status", return_value=gcloud_status):
        settings = Settings()
        assert settings.authentication == True

        if gcloud_status == ServiceStatus.RUNNING:
            assert settings.gcloud == True
        else:
            assert settings.gcloud == False

@pytest.mark.parametrize("auth, gcloud", [
    (True, True),     
    (True, False),    
    (False, True),     
    (False, False)      
])
def test_settings_getters_with_populated_db(test_client, default_db_session, auth, gcloud):
    settings_model = SettingsModel(id=1, authentication = auth, gcloud = gcloud)
    default_db_session.add(settings_model)
    default_db_session.commit()
    settings = Settings()
    assert settings.authentication == auth
    assert settings.gcloud == gcloud
    default_db_session.delete(settings_model)
    default_db_session.commit()

@pytest.mark.parametrize("auth, gcloud", [
    (True, True),     
    (True, False),    
    (False, True),     
    (False, False)      
])
def test_settings_setters(test_client,default_db_session, auth, gcloud):
    real_subprocess_run = subprocess.run
    def mock_subprocess_run(cmd, *args, **kwargs):
        if cmd[:3] == ["sudo", "/bin/systemctl", "start"] or \
            cmd[:3] == ["sudo", "/bin/systemctl", "stop"]:
            return subprocess.CompletedProcess(args=cmd, returncode=0, stderr="")
        # For other commands, call the real subprocess.run
        return real_subprocess_run(cmd, *args, **kwargs)
    with patch("app.components.settings.subprocess.run", side_effect=mock_subprocess_run):
        settings = Settings()
        settings.authentication = auth
        settings.gcloud = gcloud
        assert settings.authentication == auth
        assert settings.gcloud == gcloud
        settings_model = default_db_session.query(SettingsModel).first()
        assert settings_model.authentication == auth
        assert settings_model.gcloud == gcloud


