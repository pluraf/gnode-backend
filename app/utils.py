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


import os
import zmq
import subprocess

from app.zmq_setup import zmq_context


class GNodeMode:
    PHYSICAL = "physical"
    VIRTUAL = "virtual"


def get_mode():
    if os.path.exists("/.dockerenv"):
        return GNodeMode.VIRTUAL
    return GNodeMode.PHYSICAL


def run_command(command, shell=False):
    result = subprocess.run(command, check=True, text=True, capture_output=True, shell=shell)
    return result.stdout.strip()


def run_privileged_command(command, shell=False):
    if shell:
        command = "sudo " + command
    else:
        command = ["sudo"] + command
    result = subprocess.run(command, check=True, text=True, capture_output=True, shell=shell)
    return result.stdout.strip()

def send_zmq_request(address,command,fail_resp,is_resp_str = True, rcvtime = 500):
    socket = get_zmq_socket(address, rcvtime)
    resp = fail_resp
    if socket is None:
        return resp
    try:
        socket.send_string(command)
        if is_resp_str:
            resp = socket.recv_string()
        else:
            resp = socket.recv()
    except zmq.error.ZMQError as e:
        resp = fail_resp
    finally:
        socket.close()
    return resp

def get_zmq_socket(address,rcvtime = 500):
    socket = zmq_context.socket(zmq.REQ)
    socket.setsockopt(zmq.RCVTIMEO, rcvtime)
    socket.setsockopt(zmq.LINGER, 0)
    try:
        socket.connect(address)
    except zmq.error.ZMQError as e:
        return None
    return socket