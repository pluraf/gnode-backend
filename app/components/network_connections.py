from fastapi import HTTPException

import subprocess

def run_command(command):
    result = subprocess.run(command, check=True, text=True, capture_output=True)
    return result.stdout.strip()

def get_objects_from_multiline_output(command_response):
    element_list = []
    element = {}
    is_first = True
    first_attribute = ""
    for line in command_response.splitlines() :
        [attr, val] = line.split(":")
        val = val.strip()
        if val == "--":
            val = ""
        attr = attr.strip()
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

def get_available_wifi():
    # command: nmcli -m multiline -f 'SSID,SECURITY,S' device wifi list
    # allowed fields: NAME,SSID,SSID-HEX,BSSID,MODE,CHAN,FREQ,RATE,BANDWIDTH,SIGNAL,
    # BARS,SECURITY,WPA-FLAGS,RSN-FLAGS,DEVICE,ACTIVE,IN-USE,DBUS-PATH
    command = ['nmcli', '-m', 'multiline', '-f', 'SSID,SECURITY,SIGNAL,RATE', 'device', 'wifi', 'list']
    comm_response = run_command(command)
    return get_objects_from_multiline_output(comm_response)

def get_available_ethernet():
    # command: nmcli -m multiline -f 'NAME,TYPE,DEVICE' connection show
    command = ['nmcli', '-m', 'multiline', '-f', 'NAME,TYPE,DEVICE', 'connection', 'show']
    comm_response = run_command(command)
    connections = get_objects_from_multiline_output(comm_response)
    relevant_connections = [connection for connection in connections if connection['TYPE'] == 'ethernet']
    # To get more details about specific connection, command 'nmcli connections show <conn name>' 
    # can be used 
    return relevant_connections

def get_current_active_connections():
    # command: nmcli -m multiline -f 'NAME,TYPE,DEVICE' connection show --active
    # allowed fields: NAME,UUID,TYPE,TIMESTAMP,TIMESTAMP-REAL,AUTOCONNECT,AUTOCONNECT-PRIORITY,
    # READONLY,DBUS-PATH,ACTIVE,DEVICE,STATE,ACTIVE-PATH,SLAVE,FILENAME
    # nmcli connection type allowed values : adsl, bond, bond-slave, bridge, bridge-slave, 
    # bluetooth, cdma, ethernet, gsm, infiniband, olpc-mesh, team, team-slave, vlan, wifi, wimax.
    relevant_types = ['ethernet', 'wifi']
    command = ['nmcli', '-m', 'multiline', '-f', 'NAME,TYPE,DEVICE', 'connection', 'show', '--active']
    comm_response = run_command(command)
    connections = get_objects_from_multiline_output(comm_response)
    relevant_connections = [connection for connection in connections if connection['TYPE'] in relevant_types]
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

def set_network_settings(user_input):
    # Accepts input of format:
    # {
    #    TYPE: wifi
    #    SSID:
    #    PASSWORD:
    # }
    # command: nmcli device wifi connect <ssid> password <password>
    connection_type = user_input.get("TYPE")
    ssid = user_input.get("SSID")
    password = user_input.get("PASSWORD")
    password_needed = False
    if  (connection_type is None) or connection_type != 'wifi' or ssid is None:
        raise HTTPException(status_code = 422, detail = "Only wifi settings are currently supported by network settings. " +
        "Input should be of format {TYPE:wifi, SSID: , PASSWORD: }. Password is optional")
    connections = get_available_wifi()
    seĺected_connection = [connection for connection in connections if connection['SSID'] == ssid]
    if len(seĺected_connection) == 0 :
        raise HTTPException(status_code = 404, detail = "Network settings: Given ssid is invalid")
    password_needed = seĺected_connection[0]["SECURITY"] != ""
    if password is None:
        if password_needed:
            raise HTTPException(status_code = 422, detail = "Network settings: Given ssid requires a password")
        command = ['nmcli', 'device', 'wifi', 'connect', ssid]
    else:
        command = ['nmcli', 'device', 'wifi', 'connect', ssid, 'password', password]
    try:
        run_command(command)
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code = 500, detail = "Could not change network settings")
    

