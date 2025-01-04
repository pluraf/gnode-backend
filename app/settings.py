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


ALGORITHM = "ES256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440

TOKEN_AUTH_URL = "/api/auth/token"

ZMQ_MQBC_SOCKET = "ipc:///tmp/mqbc-zmq.sock"
ZMQ_M2EB_SOCKET = "ipc:///tmp/m2eb-zmq.sock"
ZMQ_GCLIENT_SOCKET = "ipc:///run/gnode/gclient.sock"

MQBC_SERVICE_NAME = "mqbc.service"
M2EB_SERVICE_NAME = "m2eb.service"
GCLOUD_SERVICE_NAME = "gnode-cloud-client.service"
