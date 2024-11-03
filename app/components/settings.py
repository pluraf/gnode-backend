import subprocess

from sqlalchemy import exc
from sqlalchemy.orm import sessionmaker

from app.models.settings import SettingsModel
from app.database_setup import default_engine


class Settings:
    def __init__(self):
        session = sessionmaker(bind=default_engine)()
        self._settings = session.query(SettingsModel).first()
        if self._settings is None:
            self._settings = SettingsModel()
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
            self._settings.gcloud = value
            session.add(self._settings)
            session.commit()
        except exc.SQLAlchemyError:
            session.rollback()
            raise
        finally:
            session.close()

        if value:
            subprocess.run(["sudo", "/bin/systemctl", "start", "gnode-cloud-client.service"], check=True)
        else:
            subprocess.run(["sudo", "/bin/systemctl", "stop", "gnode-cloud-client.service"], check=True)
