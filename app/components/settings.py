import subprocess
import zmq
import json

import app.settings as app_settings

from sqlalchemy import exc
from sqlalchemy.orm import sessionmaker

from app.models.settings import SettingsModel
from app.database_setup import default_engine
from app.utils import get_mode, GNodeMode, send_zmq_request, get_zmq_socket

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
        finally:
            session.close()

    @property
    def gcloud(self):
        info_str = send_zmq_request(app_settings.ZMQ_GCLIENT_SOCKET, "info", "{}", rcvtime = 4000 )
        info = json.loads(info_str)
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
        try:
            socket = get_zmq_socket(app_settings.ZMQ_GCLIENT_SOCKET, 4000)
            if socket is None:
                raise RuntimeError("Can not connect to gclient socket")
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
        finally:
            if socket is not None:
                socket.close()

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
    else:
        # if api_authentication is set to false, ensure status is reflected in m2e bridge and m-brocker-c
        if not settings.api_authentication:
            send_zmq_set_auth_req(False, False)

def send_zmq_set_auth_req(old_api_auth, new_api_auth):
    zmq_command = "set_api_auth_on" if new_api_auth else "set_api_auth_off"
    reset_command = "set_api_auth_on" if old_api_auth else "set_api_auth_off"
    mqbc_resp = send_zmq_request(app_settings.ZMQ_MQBC_SOCKET, zmq_command, "fail" )
    if mqbc_resp != "ok":
        return False
    m2eb_resp = send_zmq_request(app_settings.ZMQ_M2EB_SOCKET, zmq_command, "fail" )
    if m2eb_resp != "ok":
        mqbc_resp = send_zmq_request(app_settings.ZMQ_MQBC_SOCKET, reset_command, "fail" )
        return False
    return True

