import pytest

from app import settings
from app.models.settings import SettingsModel
from app.components.settings import Settings
from app import utils
from app.routers import status

def test_settings_init_with_empty_db(test_client):
    settings = Settings()
    assert settings.authentication == True

    if utils.get_mode() == utils.GNodeMode.VIRTUAL:
        assert settings.gcloud == False
    else:
        is_gcloud = (status.get_systemd_service_status("gnode-cloud-client.service") == status.ServiceStatus.RUNNING)
        assert settings.gcloud == is_gcloud

@pytest.mark.parametrize("auth, gcloud", [
    (True, True),     
    (True, False),    
    (False, True),     
    (False, False)      
])
def test_settings_init_with_populated_db(test_client, default_db_session, auth, gcloud):
    settings_model = SettingsModel(id=1, authentication = auth, gcloud = gcloud)
    default_db_session.add(settings_model)
    default_db_session.commit()
    settings = Settings()
    assert settings.authentication == auth
    assert settings.gcloud == gcloud
    default_db_session.delete(settings_model)
    default_db_session.commit()


