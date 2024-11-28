import zmq
import json

from fastapi import APIRouter, Response, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from typing import Any
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from app.routers import authentication
from app.components import gnode_time, network_connections
from app.components.settings import Settings
from app.zmq_setup import zmq_context
import app.settings as app_settings

router = APIRouter()




n = '{"available_wifi":[{"ssid":"Pluraf_Test","security":"WPA2","device":"wlan0","signal":"84","rate":"65 Mbit/s"},{"ssid":"Pluraf","security":"WPA2","device":"wlan0","signal":"71","rate":"65 Mbit/s"},{"ssid":"Elegant","security":"WPA2","device":"wlan0","signal":"52","rate":"65 Mbit/s"},{"ssid":"WIFIHUB_feb410","security":"WPA2","device":"wlan0","signal":"32","rate":"65 Mbit/s"},{"ssid":"Borgen 2.0","security":"WPA2","device":"wlan0","signal":"32","rate":"65 Mbit/s"},{"ssid":"#Telia-2C5578","security":"WPA2","device":"wlan0","signal":"30","rate":"65 Mbit/s"},{"ssid":"Tele2_45c015","security":"WPA2","device":"wlan0","signal":"30","rate":"65 Mbit/s"},{"ssid":"DIRECT-xyPhilips TV","security":"WPA2","device":"wlan0","signal":"29","rate":"65 Mbit/s"},{"ssid":"WORLDWIDEWEB","security":"WPA2","device":"wlan0","signal":"27","rate":"65 Mbit/s"},{"ssid":"w","security":"WPA2","device":"wlan0","signal":"27","rate":"65 Mbit/s"},{"ssid":"Bratt","security":"WPA2","device":"wlan0","signal":"25","rate":"65 Mbit/s"},{"ssid":"Telia-496575","security":"WPA2","device":"wlan0","signal":"25","rate":"65 Mbit/s"},{"ssid":"Tele2_fe123c","security":"WPA2","device":"wlan0","signal":"24","rate":"65 Mbit/s"},{"ssid":"TP-Link_B90C","security":"WPA2","device":"wlan0","signal":"22","rate":"65 Mbit/s"},{"ssid":"Tele2_CB8816","security":"WPA2","device":"wlan0","signal":"22","rate":"65 Mbit/s"},{"ssid":"WIFI","security":"WPA2","device":"wlan0","signal":"19","rate":"65 Mbit/s"},{"ssid":"EWAYS-Elbil1","security":"WPA2","device":"wlan0","signal":"17","rate":"65 Mbit/s"},{"ssid":"COMHEM_9c7b93","security":"WPA2","device":"wlan0","signal":"17","rate":"65 Mbit/s"}],"available_ethernet":[{"name":"Eth","type":"ethernet","device":"eth0"}],"active_connections":[{"name":"Eth","type":"ethernet","device":"eth0","ipv4_method":"auto","ipv4_settings":{"address":"192.168.1.174","netmask":"255.255.255.0","gateway":"192.168.1.1","dns":"192.168.1.1"}},{"name":"Pluraf","type":"wifi","device":"wlan0","ipv4_method":"auto","ipv4_settings":{"address":"192.168.1.252","netmask":"255.255.255.0","gateway":"192.168.1.1","dns":"192.168.1.1"}}],"fetching_status":"success"}'
nj = json.loads(n)


@router.get("/")
async def settings_get(_: str = Depends(authentication.authenticate)):
    socket = zmq_context.socket(zmq.REQ)
    socket.setsockopt(zmq.RCVTIMEO, 500)
    socket.setsockopt(zmq.LINGER, 0)
    socket.connect(app_settings.ZMQ_MQBC_ENDPOINT)

    response = {}

    try:
        socket.send_string('')
        message = socket.recv()
    except zmq.error.ZMQError:
        message = b"\x00"
    finally:
        socket.close()
    response["allow_anonymous"] = bool(message[0])

    current_timestamp = int(datetime.now(timezone.utc).timestamp())
    with open("/etc/timezone", "r") as tz:
        current_timezone = tz.read().strip()
    iso_8601_utc = datetime.now(ZoneInfo(current_timezone)).strftime("%Y-%m-%dT%H:%M:%S%z")
    response["time"] = {
        "timestamp": current_timestamp,
        "iso8601": iso_8601_utc,
        "timezone": current_timezone
    }

    try:
        response["network_settings"] = network_connections.get_netwok_settings()
    except:
        response["network_settings"] = {}

    settings = Settings()
    response["authentication"] = settings.authentication
    response["gcloud"] = settings.gcloud

    return JSONResponse(content=response)


@router.put("/")
async def settings_put(settings: dict[str, Any], _: str = Depends(authentication.authenticate)):
    # TODO: Move each block to a dedicated function (class?)
    last_exc = None
    try:
        v = settings.get("allow_anonymous")
        if v is not None:
            socket = zmq_context.socket(zmq.REQ)
            socket.setsockopt(zmq.RCVTIMEO, 500)
            socket.setsockopt(zmq.LINGER, 0)
            socket.connect(app_settings.ZMQ_MQBC_ENDPOINT)
            try:
                socket.send(b'\x01' if v else b'\x00')
                socket.recv()
            except zmq.error.ZMQError:
                pass
            finally:
                socket.close()
    except Exception as e:
        last_exc = e

    try:
        v = settings.get("gnode_time")
        if v is not None:
            gnode_time.set_gnode_time(v)
    except Exception as e:
        last_exc = e

    try:
        v = settings.get("network_settings")
        if v is not None:
            network_connections.set_network_settings(v)
    except Exception as e:
        last_exc = e

    try:
        v = settings.get("authentication")
        if v is not None:
            Settings().authentication = v
    except Exception as e:
        last_exc = e

    try:
        v = settings.get("gcloud")
        if v is not None:
            Settings().gcloud = v
    except Exception as e:
        last_exc = e

    if isinstance(last_exc, HTTPException):
        raise last_exc
    elif last_exc is not None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(last_exc)
        )

    return Response(status_code=200)
