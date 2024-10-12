from fastapi import APIRouter
import zmq
from typing import Dict

router = APIRouter()
context = zmq.Context()  # Should be terminated when application exits


def get_version_from_zmq(address: str) -> str:
    socket = context.socket(zmq.REQ)
    try:
        socket.connect(address)
        socket.send_string("api_version")
        socket.setsockopt(zmq.RCVTIMEO, 1000)
        version = socket.recv_string()
    except zmq.error.ZMQError as e:
        version = "xxxx"
    finally:
        socket.close()
    return version


def get_mqbc_api_version() -> str:
    return get_version_from_zmq("ipc:///tmp/mqbc-zmq.sock")


def get_m2eb_api_version() -> str:
    return get_version_from_zmq("ipc:///tmp/m2eb-zmq.sock")


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
