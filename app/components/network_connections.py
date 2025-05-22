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


from fastapi import HTTPException

import subprocess
import ipaddress
import json

from app.utils import run_command, run_privileged_command
from app.components.status import get_service_status, ServiceStatus

def get_objects_from_multiline_output(command_response):
    element_list = []
    element = {}
    is_first = True
    first_attribute = ""
    for line in command_response.splitlines():
        try:
            [attr, val] = line.split(":", 1)
            val = val.strip()
            if val == "--":
                val = ""
            attr = attr.strip().lower()
            if is_first:
                first_attribute = attr
                is_first = False
            if attr == first_attribute and len(element) != 0:
                element_list.append(element)
                element = {}
            element[attr] = val
        except:
            continue
    if len(element) != 0:
        element_list.append(element)
    return element_list

def netmask_to_cidr( netmask):
    network = ipaddress.IPv4Network(f"0.0.0.0/{netmask}", strict=False)
    return str(network.prefixlen)

def cidr_to_ip_and_netmask(cidr):
    # Parse the CIDR notation
    ipint = ipaddress.IPv4Interface(cidr)
    # Extract the IP address and netmask
    return str(ipint.ip), str(ipint.network.netmask)

def is_valid_ipv4_address(ip):
    try:
        ip_add = ipaddress.IPv4Address(ip)
        if(
            ip_add.is_loopback
            or ip_add.is_multicast
            or ip_add.is_reserved
            or ip_add.is_unspecified
        ):
            return False
        return True
    except ipaddress.AddressValueError:
        return False

def is_valid_subnet_mask(mask):
    try:
        network = ipaddress.IPv4Network(f'0.0.0.0/{mask}', strict=False)
        return network.with_netmask.split('/')[1] == mask
    except ValueError:
        return False

def is_valid_gateway(gateway, network_ip, subnet_mask):
    try:
        # Create a network with the provided IP and subnet mask
        network = ipaddress.IPv4Network(f"{network_ip}/{subnet_mask}", strict=False)
        if not is_valid_ipv4_address(gateway):
            return False
        # Check if the gateway is within the network range but not the network address
        gateway_ip = ipaddress.IPv4Address(gateway)
        return (
            gateway_ip in network
            and gateway_ip != network.network_address
            and gateway_ip != network.broadcast_address
        )
    except (ValueError, ipaddress.AddressValueError):
        return False

def validate_ipv4_settings(ipv4_settings):
    if not isinstance(ipv4_settings, dict):
        return False ,"Invalid ipv4_settings format"
    keys = ipv4_settings.keys()
    allowed_attr = ['address', 'netmask', 'dns', 'gateway']
    is_allowed_attr = all(key in allowed_attr for key in keys)
    if len(keys) != 4 or  (not is_allowed_attr):
        return False, "ipv4_settings should contain only address, netmask, dns and gateway"
    if not is_valid_ipv4_address(ipv4_settings['address']):
        return False, "Invalid address!"
    if not is_valid_subnet_mask(ipv4_settings['netmask']):
        return False, "Invalid netmask!"
    if not is_valid_gateway(ipv4_settings['gateway'], ipv4_settings['address'], ipv4_settings['netmask']):
        return False, "Invalid gateway!"
    if not is_valid_ipv4_address(ipv4_settings['dns']):
        return False, "Invalid dns!"
    return True, ""

def get_ipv4_method(connection_name):
    # command : nmcli connection show <connection-name> | grep ipv4.method
    command = 'nmcli connection show "' + connection_name + '" | grep ipv4.method'
    command_resp = run_privileged_command(command, True)
    command_resp = get_objects_from_multiline_output(command_resp)
    return command_resp[0]['ipv4.method']

def get_ipv4_settings(device_name):
    # command: nmcli device show <device_name>
    ipv4_settings = {}
    command = ['nmcli', 'device', 'show', device_name]
    command_resp = get_objects_from_multiline_output(run_privileged_command(command))
    try:
        ipv4_settings['address'], ipv4_settings['netmask']  = \
            cidr_to_ip_and_netmask(command_resp[0]['ip4.address[1]'])
    except KeyError:
        pass  # IP address can be empty
    ipv4_settings['gateway'] = command_resp[0]['ip4.gateway']
    ipv4_settings['dns'] = command_resp[0].get('ip4.dns[1]')
    return ipv4_settings

def get_ap_state():
    if get_service_status("hostapd@SoftAp0") == ServiceStatus.RUNNING:
        return "enabled"
    return "disabled"

def get_wifi_state():
    return run_command(["nmcli", "radio", "wifi"])

def get_ethernet_state():
    return run_command(["nmcli", "networking"])

def get_available_wifi():
    # command: nmcli -m multiline -f 'SSID,SECURITY,DEVICE,SIGNAL,RATE' device wifi list
    # allowed fields: NAME,SSID,SSID-HEX,BSSID,MODE,CHAN,FREQ,RATE,BANDWIDTH,SIGNAL,
    # BARS,SECURITY,WPA-FLAGS,RSN-FLAGS,DEVICE,ACTIVE,IN-USE,DBUS-PATH
    command = ['nmcli', '-m', 'multiline', '-f', 'SSID,SECURITY,DEVICE,SIGNAL,RATE', 'device', 'wifi', 'list']
    comm_response = run_privileged_command(command)
    return get_objects_from_multiline_output(comm_response)

def get_default_route():
    #command: ip -j route
    command = ['ip', '-j', 'route']
    comm_response = run_command(command)
    resp_json = json.loads(comm_response)
    for route in resp_json:
        if route["dst"] == "default":
            return route
    return []

def get_network_status():
    status = {}
    status["ipv4"] = "-"
    status["netmask"] = "-"
    status["gateway"] = "-"
    status["dns"] = "-"
    try:
        def_route = get_default_route()
        if def_route == []:
            return status
        curr_device = def_route["dev"]
        return get_ipv4_settings(curr_device)
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code = 500, detail = "Could not get network status!")

def get_available_ethernet():
    # command: nmcli -m multiline -f 'NAME,TYPE,DEVICE' connection show
    command = ['nmcli', '-m', 'multiline', '-f', 'NAME,TYPE,DEVICE', 'connection', 'show']
    comm_response = run_privileged_command(command)
    connections = get_objects_from_multiline_output(comm_response)
    relevant_connections = [connection for connection in connections if connection['type'] == 'ethernet']
    # To get more details about specific connection, command 'nmcli connections show <conn name>'
    # can be used
    return relevant_connections

def get_current_active_connections(types = []):
    # command: nmcli -m multiline -f 'NAME,TYPE,DEVICE' connection show --active
    # allowed fields: NAME,UUID,TYPE,TIMESTAMP,TIMESTAMP-REAL,AUTOCONNECT,AUTOCONNECT-PRIORITY,
    # READONLY,DBUS-PATH,ACTIVE,DEVICE,STATE,ACTIVE-PATH,SLAVE,FILENAME
    # nmcli connection type allowed values : adsl, bond, bond-slave, bridge, bridge-slave,
    # bluetooth, cdma, ethernet, gsm, infiniband, olpc-mesh, team, team-slave, vlan, wifi, wimax.
    relevant_types = []
    if not isinstance(types, list):
        return []
    if len(types) == 0:
        relevant_types = ['ethernet', 'wifi']
    else:
        relevant_types = types
    command = ['nmcli', '-m', 'multiline', '-f', 'NAME,TYPE,DEVICE', 'connection', 'show', '--active']
    comm_response = run_privileged_command(command)
    connections = get_objects_from_multiline_output(comm_response)
    relevant_connections = [connection for connection in connections if connection['type'] in relevant_types]
    for connection in relevant_connections:
        connection['ipv4_method'] = get_ipv4_method(connection['name'])
        connection['ipv4_settings'] = get_ipv4_settings(connection['device'])
    return relevant_connections

def get_netwok_settings():
    network_settings = {}
    try:
        network_settings["ap_state"] = get_ap_state()
        network_settings["wifi_state"] = get_wifi_state()
        network_settings["ethernet_state"] = get_ethernet_state()
        network_settings["available_wifi"] = get_available_wifi()
        network_settings["available_ethernet"] = get_available_ethernet()
        network_settings["active_connections"] = get_current_active_connections()
        network_settings["fetching_status"] = "success"
        return network_settings
    except subprocess.CalledProcessError as e:
        print(e.stderr.strip())
        network_settings["fetching_status"] = "failure"
        return network_settings

def set_ipv4_settings(ipv4_method, ipv4_settings, connection_type):
    # current ipv4_settings and user given ipv4_settings match,
    try:
        current_connection = get_current_active_connections([connection_type])[0]
    except IndexError:
        raise HTTPException(
            status_code = 400, detail = "No active connections"
        )
    connection_name = current_connection['name']
    commands = []
    if ipv4_method == "auto" :
        commands.append(['nmcli', 'connection', 'modify', connection_name, 'ipv4.method', 'auto'])
        commands.append(['nmcli', 'connection', 'modify', connection_name, 'ipv4.gateway', ''])
        commands.append(['nmcli', 'connection', 'modify', connection_name, 'ipv4.dns', ''])
        commands.append(['nmcli', 'connection', 'modify', connection_name, 'ipv4.addresses', ''])
    elif ipv4_method == "manual" :
        res, err = validate_ipv4_settings(ipv4_settings)
        if not res:
            raise HTTPException(status_code=422, detail="Invalid ipv4 settings."+err)
#            commands.append(['ip', "addr", "flush", "dev", "wlan0"])
        cidr_address = ipv4_settings['address'] + '/' + netmask_to_cidr(ipv4_settings['netmask'])
        commands.append(['nmcli', 'connection', 'modify', connection_name, 'ipv4.addresses', cidr_address])
        commands.append(['nmcli', 'connection', 'modify', connection_name, 'ipv4.gateway', ipv4_settings['gateway']])
        commands.append(['nmcli', 'connection', 'modify', connection_name, 'ipv4.dns', ipv4_settings['dns']])
        commands.append(['nmcli', 'connection', 'modify', connection_name, 'ipv4.method', 'manual'])
    # commands.append(['nmcli', 'connection', 'down', connection_name])
    # commands.append(['nmcli', 'connection', 'up', connection_name])
    commands.append(["nmcli", "device", "reapply", current_connection['device']])
    try:
        for command in commands:
            run_privileged_command(command)
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code = 500, detail = "Could not set network settings!")

def set_ap_state(on):
    if on:
        run_privileged_command(["systemctl", "start", "hostapd@SoftAp0.service"])
        run_privileged_command(["systemctl", "enable", "hostapd@SoftAp0.service"])
    else:
        run_privileged_command(["systemctl", "disable", "hostapd@SoftAp0.service"])
        run_privileged_command(["systemctl", "stop", "hostapd@SoftAp0.service"])

def set_wifi_state(on):
    return run_privileged_command(["nmcli", "radio", "wifi", "on" if on else "off"])

def connect_wifi(ssid, password):
    connections = get_available_wifi()
    seĺected_connection = [connection for connection in connections if connection['ssid'] == ssid]
    if len(seĺected_connection) == 0 :
        raise HTTPException(status_code = 404, detail = "Network settings: Given ssid is invalid")
    current_wifi_connection = get_current_active_connections(['wifi'])
    #connect to the new wifi network if not conneted
    if len(current_wifi_connection) == 0 or current_wifi_connection[0]['name'] != ssid :
        password_needed = seĺected_connection[0]["security"] != ""
        if not password:
            if password_needed:
                raise HTTPException(status_code = 422, detail = "Network settings: Given ssid requires a password")
            command = ['nmcli', 'device', 'wifi', 'connect', ssid]
        else:
            command = ['nmcli', 'device', 'wifi', 'connect', ssid, 'password', password]
        try:
            run_privileged_command(command)
        except subprocess.CalledProcessError as e:
            if "property is invalid" in e.stderr or "Secrets were required" in e.stderr:
                raise HTTPException(status_code=400, detail="Password is invalid")
            run_privileged_command(["nmcli", "connection", "delete", "id", ssid])
            raise HTTPException(status_code = 500)

def set_network_settings(user_input):
    # Accepts input of format:
    # {
    #    wifi_state:
    #    type:
    #    ssid:
    #    password:
    #    ipv4_method:
    #    ipv4_settings:
    # }

    connection_type = user_input.get("type")
    ssid = user_input.get("ssid")
    password = user_input.get("password")
    ipv4_method = user_input.get("ipv4_method")
    ipv4_settings = user_input.get("ipv4_settings", {})

    if "ap_state" in user_input:
        set_ap_state(user_input["ap_state"] == "enabled")

    if "wifi_state" in user_input:
        set_wifi_state(user_input["wifi_state"] == "enabled")

    if "ssid" in user_input:
        connect_wifi(ssid, password)

    # set ipv4 settings if input is valid
    if ipv4_method == 'auto' or ipv4_method == "manual":
        set_ipv4_settings(ipv4_method, ipv4_settings, connection_type)
    elif ipv4_method is not None :
        raise HTTPException(status_code = 422, detail = "ipv4_method should be auto or manual")
