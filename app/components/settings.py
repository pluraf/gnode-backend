import subprocess

from sqlalchemy import exc
from sqlalchemy.orm import sessionmaker

from app.models.settings import SettingsModel
from app.database_setup import default_engine
import app.settings as app_settings
from app.utils import get_mode, GNodeMode, send_zmq_request

class Settings:
    def __init__(self):
        session = sessionmaker(bind=default_engine)()
        self._settings = session.query(SettingsModel).first()
        session.close()

    @property
    def api_authentication(self):
        return self._settings.api_authentication

    @api_authentication.setter
    def api_authentication(self, value):
        session = sessionmaker(bind=default_engine)()
        try:
            if not send_zmq_set_auth_req(self._settings.api_authentication,value):
                raise RuntimeError("Cannot set api_authentication for m-broker-c and m2e-bridge")
            self._settings.api_authentication = value
            session.add(self._settings)
            session.commit()
            self._settings = session.query(SettingsModel).first()
        except exc.SQLAlchemyError:
            session.rollback()
            raise
        except RuntimeError as e:
            raise
        finally:
            session.close()

    @property
    def gcloud(self):
        return self._settings.gcloud

    @gcloud.setter
    def gcloud(self, value):
        session = sessionmaker(bind=default_engine)()
        try:
            if value:
                subprocess.run(["sudo", "/bin/systemctl", "start", app_settings.GCLOUD_SERVICE_NAME], check=True)
            else:
                subprocess.run(["sudo", "/bin/systemctl", "stop", app_settings.GCLOUD_SERVICE_NAME], check=True)
            self._settings.gcloud = value
            session.add(self._settings)
            session.commit()
            self._settings = session.query(SettingsModel).first()
        except exc.SQLAlchemyError:
            session.rollback()
            raise
        except subprocess.CalledProcessError:
            raise RuntimeError("Error changing g-cloud status")
        finally:
            session.close()

def init_settings_table():
    session = sessionmaker(bind=default_engine)()
    settings = session.query(SettingsModel).first()
    if settings is None:
        session.add(SettingsModel())
        session.commit()
        settings = session.query(SettingsModel).first()
        session.close()
        #no need to reset api_auth value in case of failure since it is initialization
        send_zmq_set_auth_req(settings.api_authentication, settings.api_authentication)
        if get_mode() == GNodeMode.PHYSICAL :
            try:
                if (settings.gcloud):
                    subprocess.run(["sudo", "/bin/systemctl", "start", app_settings.GCLOUD_SERVICE_NAME], check=True)
                else:
                    subprocess.run(["sudo", "/bin/systemctl", "stop", app_settings.GCLOUD_SERVICE_NAME], check=True)
            except subprocess.CalledProcessError:
                # Letting execution continue in case of error
                # TODO: Change print to log later
                print("Error initializing gcloud settings!")
    else:
        # if api_authentication is set to false, ensure status is reflected in m2e bridge and m-brocker-c
        if not settings.api_authentication:
            send_zmq_set_auth_req(False, False)

def send_zmq_set_auth_req(old_api_auth, new_api_auth):
    zmq_command = "set_api_auth_on" if new_api_auth else "set_api_auth_off"
    reset_command = "set_api_auth_on" if old_api_auth else "set_api_auth_off"
    mqbc_resp = send_zmq_request(app_settings.ZMQ_MQBC_ENDPOINT, zmq_command, "fail" )
    if mqbc_resp != "ok":
        return False
    m2eb_resp = send_zmq_request(app_settings.ZMQ_M2EB_ENDPOINT, zmq_command, "fail" )
    if m2eb_resp != "ok":
        mqbc_resp = send_zmq_request(app_settings.ZMQ_MQBC_ENDPOINT, reset_command, "fail" )
        return False
    return True