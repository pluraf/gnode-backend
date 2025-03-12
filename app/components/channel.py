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

import app.settings as app_settings
from app.utils import send_zmq_request


class Channel:
    _CACHE = {}


    def __init__(self):
        pass


    def _get_channel_type(self, channel_id):
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
        else:
            return app_settings.ZMQ_M2EB_SOCKET


    def list(self):
        request = cbor2.dumps(['GET', 'channel/'])
        m_channels = send_zmq_request(app_settings.ZMQ_MQBC_SOCKET, request)
        h_channels = send_zmq_request(app_settings.ZMQ_M2EB_SOCKET, request)

        m_channels = json.loads(m_channels)
        h_channels = json.loads(h_channels)

        for channel in m_channels:
            channel["type"] = "mqtt"
            self._CACHE[channel["id"]] = channel
        for channel in h_channels:
            channel["type"] = "http"
            self._CACHE[channel["id"]] = channel

        return json.dumps(m_channels + h_channels)


    def get(self, channel_id):
        try:
            type = self._get_channel_type(channel_id)
        except KeyError:
            return None

        request = cbor2.dumps(['GET', 'channel/' + channel_id])
        socket = app_settings.ZMQ_MQBC_SOCKET if type == "mqtt" else app_settings.ZMQ_M2EB_SOCKET
        return send_zmq_request(socket, request)


    def create(self, channel_id, payload):
        try:
            channel_type = payload["type"]
        except KeyError:
            raise ValueError("Missing channel type")

        request = cbor2.dumps(['POST', 'channel/' + channel_id, json.dumps(payload)])
        socket = self._get_socket(channel_type)
        return send_zmq_request(socket, request)


    def update(self, channel_id, payload):
        try:
            channel_type = self._get_channel_type(channel_id)
        except KeyError:
            raise KeyError("Channel not found")

        payload = payload if type(payload) in (str, bytes) else json.dumps(payload)
        request = cbor2.dumps(['PUT', 'channel/' + channel_id, payload])
        socket = self._get_socket(channel_type)
        return send_zmq_request(socket, request)


    def delete(self, channel_id):
        try:
            channel_type = self._get_channel_type(channel_id)
        except KeyError:
            raise KeyError("Channel not found")
        request = cbor2.dumps(['DELETE', 'channel/' + channel_id])
        socket = self._get_socket(channel_type)
        try:
            return send_zmq_request(socket, request)
        finally:
            self._CACHE.pop(channel_id, None)
