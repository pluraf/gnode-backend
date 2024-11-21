import subprocess

from sqlalchemy import exc
from sqlalchemy.orm import sessionmaker

from app.models.settings import SettingsModel
from app.database_setup import default_engine
import app.settings as app_settings
from app.utils import get_mode, GNodeMode

class Settings:
    def __init__(self):
        session = sessionmaker(bind=default_engine)()
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
            self._settings = session.query(SettingsModel).first()
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

