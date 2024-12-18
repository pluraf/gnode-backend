import subprocess
import zmq
import json

import app.settings as app_settings

from sqlalchemy import exc
from sqlalchemy.orm import sessionmaker

from app.models.settings import SettingsModel
from app.database_setup import default_engine
from app.zmq_setup import zmq_context
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
        socket = zmq_context.socket(zmq.REQ)
        socket.setsockopt(zmq.RCVTIMEO, 1000)
        socket.setsockopt(zmq.LINGER, 0)
        socket.connect(app_settings.ZMQ_GCLIENT_SOCKET)
        socket.send_string("info")
        info = json.loads(socket.recv_string())
        socket.close()
        rep = {
            "https": None,
            "ssh": None
        }
        for mapping in info:
            if mapping[0] == 443:
                rep["https"] = mapping[0]
            elif mapping[2] == 22:
                rep["ssh"] = mapping[0]
        return rep

    @gcloud.setter
    def gcloud(self, value):
        socket = zmq_context.socket(zmq.REQ)
        socket.setsockopt(zmq.RCVTIMEO, 4000)
        socket.setsockopt(zmq.LINGER, 0)
        socket.connect(app_settings.ZMQ_GCLIENT_SOCKET)

        commands = []

        https = value.get("https")
        if https is not None:
            commands.append("https_on" if https else "https_off")

        ssh = value.get("ssh")
        if ssh is not None:
            commands.append("ssh_on" if ssh else "ssh_off")

        for command in commands:
            socket.send_string(command)
            if socket.recv_string() != "OK":
                raise RuntimeError("Can not execute command %s" % command)

def init_settings_table():
    session = sessionmaker(bind=default_engine)()
    settings = session.query(SettingsModel).first()
    if settings is None:
        session.add(SettingsModel())
        session.commit()
        settings = session.query(SettingsModel).first()
        session.close()
