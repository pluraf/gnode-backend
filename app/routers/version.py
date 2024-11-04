import zmq

from fastapi import APIRouter
from typing import Dict

from app.zmq_setup import zmq_context
import app.settings as app_settings

router = APIRouter()


def get_version_from_zmq(address: str) -> str:
    socket = zmq_context.socket(zmq.REQ)
    socket.setsockopt(zmq.RCVTIMEO, 1000)
    socket.setsockopt(zmq.LINGER, 0)
    try:
        socket.connect(address)
        socket.send_string("api_version")
        version = socket.recv_string()
    except zmq.error.ZMQError as e:
        version = "xxxx"
    finally:
        socket.close()
    return version


def get_mqbc_api_version() -> str:
    return get_version_from_zmq(app_settings.ZMQ_MQBC_ENDPOINT)


def get_m2eb_api_version() -> str:
    return get_version_from_zmq(app_settings.ZMQ_M2EB_ENDPOINT)


def get_serial_number() -> str:
    with open("/run/gnode/serial_number", "r") as api_file:
        return api_file.read()


def get_gnode_api_version():
    with open("./api_version.txt", "r") as file:
        serial_number = file.read()
    return serial_number


@router.get("")
async def api_version_get():
    api_version = "{}.{}.{}".format(
        get_gnode_api_version(),
        get_m2eb_api_version(),
        get_mqbc_api_version()
    )

    return {
        "api_version" : api_version,
        "serial_number" : get_serial_number()
    }
