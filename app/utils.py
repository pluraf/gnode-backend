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
        command = "sudo -n " + command
    else:
        command = ["sudo", "-n"] + command
    result = subprocess.run(command, check=True, text=True, capture_output=True, shell=shell)
    return result.stdout.strip()


def send_zmq_request(address, command, rcvtime = 200):
    command = command if type(command) == bytes else command.encode()
    socket = get_zmq_socket(address, rcvtime)
    try:
        socket.send(command)
        return socket.recv()
    finally:
        socket.close()


def get_zmq_socket(address, rcvtime = 200):
    socket = zmq_context.socket(zmq.REQ)
    socket.setsockopt(zmq.RCVTIMEO, rcvtime)
    socket.setsockopt(zmq.LINGER, 0)
    socket.connect(address)
    return socket
