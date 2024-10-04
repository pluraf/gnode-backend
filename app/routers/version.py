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
        socket.setsockopt(zmq.RCVTIMEO, 5000)
        version = socket.recv_string()
    except zmq.error.ZMQError as e:
        print(f"Error retrieving version from {address}: {e}")
        return "unknown"
    finally:
        socket.close()
    return version


def parse_api_versions() -> Dict[str, str]:
    api_versions = {}
    try:
        api_versions["M-BROKER-C"] = get_version_from_zmq("ipc:///tmp/mqbc-zmq.sock")
    except Exception as e:
        api_versions["M-BROKER-C"] = "unknown"
        print(f"Failed to retrieve version for M-BROKER-C: {e}")
    try:
        api_versions["M2E-BRIDGE"] = get_version_from_zmq("ipc:///tmp/m2eb-zmq.sock")
    except Exception as e:
        api_versions["M2E-BRIDGE"] = "unknown"
        print(f"Failed to retrieve version for M2E-BRIDGE: {e}")
    return api_versions


def read_version_from_file(file_path: str) -> Dict[str, str]:
    api_versions = {}

    with open(file_path, "r") as file:
        for line in file:
            api_name, version = line.split("=")
            api_versions[api_name.strip()] = version.strip()
    return api_versions


def read_serial_number_from_file(file_path: str):
    with open(file_path, "r") as file:
        serial_number = file.read()
    return serial_number


@router.get("/")
async def api_version_get():
    gnode_api_version = read_version_from_file("./api_versions.txt")
    mbc_m2eb_api_versions = parse_api_versions()
    api_versions = {**gnode_api_version, **mbc_m2eb_api_versions}

    serial_number = read_serial_number_from_file("./serial_number.txt")

    rv = {
        "API VERSIONS" : api_versions,
        "SERIAL_NUMBER" : serial_number
    }
    
    return rv