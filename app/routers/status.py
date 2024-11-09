from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.routers import authentication
from app.components import network_connections
from app.utils import run_command, get_mode, GNodeMode
import subprocess


router = APIRouter()


class ServiceStatus:
    MALFORMED = "malformed"
    STOPPED = "stopped"
    RUNNING = "running"
    FAILED = "failed"


# Function to return status as "running", "not running" or "failed"
def get_systemd_service_status(service_name):
    #command: systemctl show <service_name> --property=ActiveState,SubState
    command = ['systemctl', 'show', service_name, '--property=ActiveState,SubState,LoadState']
    service_status = {}
    try:
        resp = run_command(command)
        for line in resp.splitlines():
            [attr, val] = line.split("=", 1)
            service_status[attr] = val
        if service_status["LoadState"] in ["not-found", "masked"]:
            return ServiceStatus.MALFORMED
        if service_status["LoadState"] == "loaded":
            if service_status["ActiveState"] == "active":
                if service_status["SubState"] == "running":
                    return ServiceStatus.RUNNING
                else:
                    return ServiceStatus.STOPPED
            if service_status["ActiveState"] == "failed":
                return ServiceStatus.FAILED
            else:
                return ServiceStatus.STOPPED
        else:
            return ServiceStatus.FAILED
    except subprocess.CalledProcessError:
        return ServiceStatus.MALFORMED


def get_supervisor_service_status(service_name):
    try:
        resp = run_command(['supervisorctl', 'show', service_name])
        status = resp.split()[1]
        if status == "RUNNING":
            return ServiceStatus.RUNNING
        if status == "STOPPED":
            return ServiceStatus.STOPPED
        return ServiceStatus.MALFORMED
    except subprocess.CalledProcessError:
        return ServiceStatus.MALFORMED


def get_service_status(service_name):
    if get_mode() == GNodeMode.PHYSICAL:
        return get_systemd_service_status(service_name)
    else:
        return get_supervisor_service_status(service_name)


@router.get("")
async def status_get(_: str = Depends(authentication.authenticate)):
    response = {}
    response["service"] = {
        "mqbc": get_service_status("mqbc.service"),
        "m2eb": get_service_status("m2eb.service"),
        "gcloud_client": get_service_status("gnode-cloud-client.service")
    }
    response["network"] = network_connections.get_network_status()
    return JSONResponse(content=response)
