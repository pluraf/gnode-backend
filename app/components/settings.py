import subprocess

from sqlalchemy import exc
from sqlalchemy.orm import sessionmaker

from app.models.settings import SettingsModel
from app.database_setup import default_engine
from app.components.status import get_service_status, ServiceStatus
import app.settings as app_settings

class Settings:
    def __init__(self):
        session = sessionmaker(bind=default_engine)()
        self._settings = session.query(SettingsModel).first()
        if self._settings is None:
            gcloud_status = \
                (get_service_status(app_settings.GCLOUD_SERVICE_NAME) == ServiceStatus.RUNNING)
            self._settings = SettingsModel(gcloud = gcloud_status)
            session.add(self._settings)
            session.commit()
            self._settings = session.query(SettingsModel).first()
        session.close()

    @property
    def authentication(self):
        return self._settings.authentication

    @authentication.setter
    def authentication(self, value):
        session = sessionmaker(bind=default_engine)()
        try:
            self._settings.authentication = value
            session.add(self._settings)
            session.commit()
        except exc.SQLAlchemyError:
            session.rollback()
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
        except exc.SQLAlchemyError:
            session.rollback()
            raise
        except subprocess.CalledProcessError:
            raise RuntimeError("Error changing g-cloud status")
        finally:
            session.close()
