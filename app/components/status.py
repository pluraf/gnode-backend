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


from app.utils import run_command, get_mode, GNodeMode
import subprocess

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
        resp = run_command(['supervisorctl', 'status', service_name])
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