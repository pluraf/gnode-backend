from fastapi import HTTPException

import subprocess
import ipaddress
import json

def run_command(command, shell=False):
    result = subprocess.run(command, check=True, text=True, capture_output=True, shell=shell)
    return result.stdout.strip()

def get_objects_from_multiline_output(command_response):
    element_list = []
    element = {}
    is_first = True
    first_attribute = ""
    for line in command_response.splitlines() :
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
        ipaddress.IPv4Address(ip)
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
        # Check if the gateway is within the network range but not the network address
        gateway_ip = ipaddress.IPv4Address(gateway)
        return gateway_ip in network and gateway_ip != network.network_address
    except (ValueError, ipaddress.AddressValueError):
        return False

def validate_ipv4_settings(ipv4_settings):
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
    command_resp = run_command(command, True)
    command_resp = get_objects_from_multiline_output(command_resp)
    return command_resp[0]['ipv4.method']

def get_ipv4_settings(device_name):
    # command: nmcli device show <device_name>
    ipv4_settings = {}
    command = ['nmcli', 'device', 'show', device_name]
    command_resp = get_objects_from_multiline_output(run_command(command))
    ipv4_settings['address'], ipv4_settings['netmask']  = \
        cidr_to_ip_and_netmask(command_resp[0]['ip4.address[1]'])
    ipv4_settings['gateway'] = command_resp[0]['ip4.gateway']
    ipv4_settings['dns'] = command_resp[0].get('ip4.dns[1]')
    return ipv4_settings

def get_available_wifi():
    # command: nmcli -m multiline -f 'SSID,SECURITY,DEVICE,SIGNAL,RATE' device wifi list
    # allowed fields: NAME,SSID,SSID-HEX,BSSID,MODE,CHAN,FREQ,RATE,BANDWIDTH,SIGNAL,
    # BARS,SECURITY,WPA-FLAGS,RSN-FLAGS,DEVICE,ACTIVE,IN-USE,DBUS-PATH
    command = ['nmcli', '-m', 'multiline', '-f', 'SSID,SECURITY,DEVICE,SIGNAL,RATE', 'device', 'wifi', 'list']
    comm_response = run_command(command)
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
    status["address"] = "-"
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
    comm_response = run_command(command)
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
    if len(types) == 0:
        relevant_types = ['ethernet', 'wifi']
    else:
        relevant_types = types
    command = ['nmcli', '-m', 'multiline', '-f', 'NAME,TYPE,DEVICE', 'connection', 'show', '--active']
    comm_response = run_command(command)
    connections = get_objects_from_multiline_output(comm_response)
    relevant_connections = [connection for connection in connections if connection['type'] in relevant_types]
    for connection in relevant_connections:
        connection['ipv4_method'] = get_ipv4_method(connection['name'])
        connection['ipv4_settings'] = get_ipv4_settings(connection['device'])
    return relevant_connections

def get_netwok_settings():
    network_settings = {}
    try:
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
    current_connection = get_current_active_connections( [connection_type] )
    connection_name = current_connection[0]['name']
    commands = []
    if ipv4_method == "auto" and current_connection[0]['ipv4_method'] == ipv4_method:
        return
    if ipv4_method == "auto" :
        commands.append (['nmcli', 'connection', 'modify', connection_name, 'ipv4.method', 'auto'])
        commands.append(['nmcli', 'connection', 'modify', connection_name, 'ipv4.gateway', ''])
        commands.append(['nmcli', 'connection', 'modify', connection_name, 'ipv4.dns', ''])
        commands.append(['nmcli', 'connection', 'modify', connection_name, 'ipv4.addresses', ''])
    if ipv4_method == "manual" :
        res, err = validate_ipv4_settings(ipv4_settings)
        if not res:
            raise HTTPException(status_code = 422, detail = "Invalid ipv4 settings." + err)
        else:
            if ipv4_settings == current_connection[0]['ipv4_settings']:
                return
            cidr_address = ipv4_settings['address'] + '/' + netmask_to_cidr(ipv4_settings['netmask'])
            commands.append(['nmcli', 'connection', 'modify', connection_name, 'ipv4.addresses', cidr_address])
            commands.append(['nmcli', 'connection', 'modify', connection_name, 'ipv4.gateway', ipv4_settings['gateway']])
            commands.append(['nmcli', 'connection', 'modify', connection_name, 'ipv4.dns', ipv4_settings['dns']])
            commands.append(['nmcli', 'connection', 'modify', connection_name, 'ipv4.method', 'manual'])
    commands.append(['nmcli', 'connection', 'down', connection_name])
    commands.append(['nmcli', 'connection', 'up', connection_name])
    try:
        for command in commands:
            run_command(command)
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code = 500, detail = "Could not set network settings!")


def set_network_settings(user_input):
    # Accepts input of format:
    # {
    #    type: wifi
    #    ssid:
    #    password:
    #    ipv4_method:
    #    ipv4_settings:
    # }
    # command: nmcli device wifi connect <ssid> password <password>
    connection_type = user_input.get("type")
    ssid = user_input.get("ssid")
    password = user_input.get("password")
    password_needed = False
    ipv4_method = user_input.get("ipv4_method")
    ipv4_settings = user_input.get("ipv4_settings")

    allowed_attr = ['type', 'ssid', 'password', 'ipv4_method', 'ipv4_settings']
    is_allowed_attr = all(key in allowed_attr for key in user_input.keys())
    if  (connection_type is None) or connection_type != 'wifi' or ssid is None or (not is_allowed_attr):
        raise HTTPException(status_code = 422, detail = "Only wifi settings are currently supported by network settings. " +
        "Input should be of format {type:wifi, ssid: , password:, ipv4_method:, ipv4_settings:  }." +
        "Password and ipv4 values are optional")

    connections = get_available_wifi()
    seĺected_connection = [connection for connection in connections if connection['ssid'] == ssid]
    if len(seĺected_connection) == 0 :
        raise HTTPException(status_code = 404, detail = "Network settings: Given ssid is invalid")

    current_wifi_connection = get_current_active_connections(['wifi'])

    #connect to the new wifi network if not conneted
    if len(current_wifi_connection) == 0 or current_wifi_connection[0]['name'] != ssid :
        password_needed = seĺected_connection[0]["security"] != ""
        if password is None:
            if password_needed:
                raise HTTPException(status_code = 422, detail = "Network settings: Given ssid requires a password")
            command = ['nmcli', 'device', 'wifi', 'connect', ssid]
        else:
            command = ['nmcli', 'device', 'wifi', 'connect', ssid, 'password', password]
        try:
            run_command(command)
        except subprocess.CalledProcessError as e:
            raise HTTPException(status_code = 500, detail = "Could not connect to given network")

    # set ipv4 settings if input is valid
    if ipv4_method == 'auto' or (ipv4_method == "manual" and (ipv4_settings is not None) and \
            isinstance(ipv4_settings, dict)):
        set_ipv4_settings(ipv4_method, ipv4_settings, connection_type)
    else:
        if ipv4_method is not None :
            raise HTTPException(status_code = 422, detail = "ipv4_method should be auto or manual." +
            "If ipv4_method is manual, ipv4_settings object should be present.")
