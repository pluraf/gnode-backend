# SPDX-License-Identifier: Apache-2.0

# Copyright (c) 2024 Pluraf Embedded AB <code@pluraf.com>

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import json
import cbor2

from zmq.error import ZMQError;
from json.decoder import JSONDecodeError

import app.settings as app_settings
from app.utils import send_zmq_request, run_privileged_command
from app.components import status


class Channel:
    _CACHE = {}


    def __init__(self):
        pass


    def _get_channel_type(self, channel_id):
        # Special case
        if channel_id in ("lora_basic_station_ws", "lora_basic_station_wss"):
            return "lora"

        channel = None
        try:
            channel = self._CACHE[channel_id]
        except KeyError:
            self.list()
            channel = self._CACHE.get(channel_id)
        try:
            return channel["type"]
        except (TypeError, KeyError):
            raise KeyError(channel_id)

    def _get_socket(self, channel_type):
        if channel_type == "mqtt":
            return app_settings.ZMQ_MQBC_SOCKET
        elif channel_type == "http":
            return app_settings.ZMQ_M2EB_SOCKET
        raise KeyError("Unknown channel type!")


    def list(self):
        request = cbor2.dumps(['GET', 'channel/'])
        try:
            m_channels = send_zmq_request(app_settings.ZMQ_MQBC_SOCKET, request)
            m_channels = json.loads(m_channels)
        except (ZMQError, JSONDecodeError):
            m_channels = []
        try:
            h_channels = send_zmq_request(app_settings.ZMQ_M2EB_SOCKET, request)
            h_channels = json.loads(h_channels)
        except (ZMQError, JSONDecodeError):
            h_channels = []

        for channel in m_channels:
            channel["type"] = "mqtt"
            self._CACHE[channel["id"]] = channel
        for channel in h_channels:
            channel["type"] = "http"
            self._CACHE[channel["id"]] = channel

        # Special case for LoRaWAN (temp)
        l_channels = [
            {
                "id": "lora_basic_station_ws",
                "type": "lora",
                "state": "CONFIGURED",
                "enabled": status.get_service_status("chirpstack-gateway-bridge-ws") == status.ServiceStatus.RUNNING
            },
            {
                "id": "lora_basic_station_wss",
                "type": "lora",
                "state": "CONFIGURED",
                "enabled": status.get_service_status("chirpstack-gateway-bridge-wss") == status.ServiceStatus.RUNNING
            }
        ]

        return json.dumps(m_channels + h_channels + l_channels)


    def get(self, channel_id):
        try:
            channel_type = self._get_channel_type(channel_id)
        except KeyError:
            return None

        # Special case for LoRaWAN (temp)
        if channel_type == "lora":
            if channel_id == "lora_basic_station_ws":
                return json.dumps({
                    "id": "lora_basic_station_ws",
                    "type": "lora",
                    "authtype": "none",
                    "state": "CONFIGURED",
                    "enabled": status.get_service_status("chirpstack-gateway-bridge-ws") == status.ServiceStatus.RUNNING,
                    "ports": (
                        {"port": 3001, "descr": "TCP"},
                    )
                })
            elif channel_id == "lora_basic_station_wss":
                return json.dumps({
                    "id": "lora_basic_station_wss",
                    "type": "lora",
                    "authtype": "none",
                    "state": "CONFIGURED",
                    "enabled": status.get_service_status("chirpstack-gateway-bridge-wss") == status.ServiceStatus.RUNNING,
                    "ports": (
                        {"port": 8887, "descr": "TLS"},
                    )
                })

        request = cbor2.dumps(['GET', 'channel/' + channel_id])
        socket = self._get_socket(channel_type)
        response = send_zmq_request(socket, request)
        if type(response) == bytes:
            response = response.decode()
        return response


    def create(self, channel_id, payload):
        try:
            channel_type = payload["type"]
        except KeyError:
            raise ValueError("Missing channel type")

        request = cbor2.dumps(['POST', 'channel/' + channel_id, json.dumps(payload)])
        socket = self._get_socket(channel_type)
        response = send_zmq_request(socket, request)
        if type(response) == bytes:
            response = response.decode()
        return response


    def update(self, channel_id, payload):
        try:
            channel_type = self._get_channel_type(channel_id)
        except KeyError:
            raise KeyError("Channel not found")

        # Special case for LoRaWAN (temp)
        if channel_type == "lora":
            if channel_id == "lora_basic_station_ws":
                if json.loads(payload)["enabled"]:
                    run_privileged_command(['systemctl', 'enable', 'chirpstack-gateway-bridge-ws'])
                    run_privileged_command(['systemctl', 'start', 'chirpstack-gateway-bridge-ws'])
                else:
                    run_privileged_command(['systemctl', 'stop', 'chirpstack-gateway-bridge-ws'])
                    run_privileged_command(['systemctl', 'disable', 'chirpstack-gateway-bridge-ws'])
            elif channel_id == "lora_basic_station_wss":
                if json.loads(payload)["enabled"]:
                    run_privileged_command(['systemctl', 'enable', 'chirpstack-gateway-bridge-wss'])
                    run_privileged_command(['systemctl', 'start', 'chirpstack-gateway-bridge-wss'])
                else:
                    run_privileged_command(['systemctl', 'stop', 'chirpstack-gateway-bridge-wss'])
                    run_privileged_command(['systemctl', 'disable', 'chirpstack-gateway-bridge-wss'])
            return ""

        payload = payload if type(payload) in (str, bytes) else json.dumps(payload)
        request = cbor2.dumps(['PUT', 'channel/' + channel_id, payload])
        socket = self._get_socket(channel_type)
        response = send_zmq_request(socket, request)
        if type(response) == bytes:
            return response.decode()
        return response


    def delete(self, channel_id):
        try:
            channel_type = self._get_channel_type(channel_id)
        except KeyError:
            raise KeyError("Channel not found")
        request = cbor2.dumps(['DELETE', 'channel/' + channel_id])
        socket = self._get_socket(channel_type)
        try:
            response = send_zmq_request(socket, request)
            if type(response) == bytes:
                return response.decode()
            return response
        finally:
            self._CACHE.pop(channel_id, None)
