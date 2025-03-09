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
    def __init__(self):
        pass

    def list(self):
        request = cbor2.dumps(['GET', 'channel/'])
        m_channels = send_zmq_request(app_settings.ZMQ_MQBC_SOCKET, request)
        h_channels = send_zmq_request(app_settings.ZMQ_M2EB_SOCKET, request)

        m_channels = json.loads(m_channels)
        h_channels = json.loads(h_channels)

        for channel in m_channels:
            channel["type"] = "mqtt"
        for channel in h_channels:
            channel["type"] = "http"

        return json.dumps(m_channels + h_channels)


    def get(self, channel_id):
        request = cbor2.dumps(['GET', 'channel/' + channel_id])
        channel = send_zmq_request(app_settings.ZMQ_MQBC_SOCKET, request)
        

    def create(self, channel_id, payload):
        request = cbor2.dumps(['POST', 'channel/' + channel_id, payload])
        return send_zmq_request(app_settings.ZMQ_MQBC_SOCKET, request)

    def update(self, channel_id, payload):
        request = cbor2.dumps(['PUT', 'channel/' + channel_id, payload])
        r = send_zmq_request(app_settings.ZMQ_MQBC_SOCKET, request)
        print(r, type(r))
        return r

    def delete(self, channel_id):
        request = cbor2.dumps(['DELETE', 'channel/' + channel_id])
        return send_zmq_request(app_settings.ZMQ_MQBC_SOCKET, request)
