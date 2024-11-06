import zmq

from fastapi import APIRouter, Response, Depends, HTTPException
from fastapi.responses import JSONResponse
from typing import Any

from app.routers import authentication
from app.components import network_connections
from app.zmq_setup import zmq_context
import app.settings as app_settings
from app.components.utils import run_command
import subprocess

router = APIRouter()

# Function to return status as "running", "not running" or "failed"
def get_systemd_service_status(service_name):
    #command: systemctl show <service_name> --property=ActiveState,SubState
    command = ['systemctl', 'show', service_name, '--property=ActiveState,SubState,LoadState']
    service_status = {}
    try:
        resp = run_command(command)
        for line in resp.splitlines() :
            [attr, val] = line.split("=", 1)
            service_status[attr] = val
        if service_status["LoadState"] in ["not-found" , "masked"]:
            return "not running"
        if service_status["LoadState"] == "loaded" :
            if service_status["ActiveState"] == "active":
                if service_status["SubState"] == "running" :
                    return "running"
                else :
                    return "not running"
            if service_status["ActiveState"] == "failed":
                return "failed"
            else:
                return "not running"
        else:
            return "failed"
    except subprocess.CalledProcessError as e:
        return "not running"

def get_status_from_zmq(address: str) -> str:
    socket = zmq_context.socket(zmq.REQ)
    try:
        socket.connect(address)
        socket.send_string("status")
        socket.setsockopt(zmq.RCVTIMEO, 1000)
        status = socket.recv_string()
    except zmq.error.ZMQError as e:
        status = "not running"
    finally:
        socket.close()
    return status

@router.get("/")
async def status_get(_: str = Depends(authentication.validate_jwt)):
    response = {}
    response["mqbc_status"] = get_status_from_zmq(app_settings.ZMQ_MQBC_ENDPOINT)
    response["m2eb_status"] = get_status_from_zmq(app_settings.ZMQ_M2EB_ENDPOINT)
    response["network_status"] = network_connections.get_network_status()
    response["gcloud_client_status"] = get_systemd_service_status("gnode-cloud-client.service")
    return JSONResponse(content=response)

