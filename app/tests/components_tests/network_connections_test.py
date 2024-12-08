import pytest
import subprocess
from unittest.mock import call
from fastapi import HTTPException

from app.components import network_connections

@pytest.mark.parametrize("cmd_response, exp_output", [
    ("", [] ),  
    ("attr1: val1 \n attr2: --\n ATTR3 : val3", [{
        "attr1" : "val1",
        "attr2" : "",
        "attr3" : "val3" 
    }] ),
    ("attr1: val1\n attr2: --\n ATTR3 : val3 \n" + \
        "attr1: val12 \n attr2: test:22 \n ATTR3 : val32 \n" + \
        "attr1: val13 \n attr2: test:23 \n ATTR3 : --", [{
        "attr1" : "val1",
        "attr2" : "",
        "attr3" : "val3" 
    }, 
    {
        "attr1" : "val12",
        "attr2" : "test:22",
        "attr3" : "val32" 
    }, 
    {
        "attr1" : "val13",
        "attr2" : "test:23",
        "attr3" : "" 
    }] ),  
])
def test_get_objects_from_multiline_output(cmd_response, exp_output):
    resp = network_connections.get_objects_from_multiline_output(cmd_response)
    assert resp == exp_output

@pytest.mark.parametrize("netmask, exp_output", [
    ("255.255.255.0", "24" ),  
    ("255.0.0.0", "8" ),  
    ("255.255.255.192", "26" )
])
def test_netmask_to_cidr(netmask, exp_output):
    resp = network_connections.netmask_to_cidr(netmask)
    assert resp == exp_output

@pytest.mark.parametrize("cidr, exp_output", [
    ("127.0.0.1/24" , ("127.0.0.1","255.255.255.0")),  
    ("192.168.0.18/8", ("192.168.0.18", "255.0.0.0")),  
    ("168.0.56.1/26", ("168.0.56.1", "255.255.255.192"))
])
def test_cidr_to_ip_and_netmask(cidr, exp_output):
    resp = network_connections.cidr_to_ip_and_netmask(cidr)
    assert resp == exp_output

@pytest.mark.parametrize("value, exp_output", [
    ("127.0.0.1" , False),  
    ("random" , False),  
    ("" , False),  
    ("127.0.0.1.56" , False),  
    ("999.78.65.3" , False),  
    ("168.0.56.1" , True)
])
def test_is_valid_ipv4_address(value, exp_output):
    resp = network_connections.is_valid_ipv4_address(value)
    assert resp == exp_output

@pytest.mark.parametrize("value, exp_output", [
    ("127.0.0.1" , False),  
    ("random" , False),  
    ("" , False),  
    ("127.0.0.1.56" , False),  
    ("999.78.65.3" , False),  
    ("255.255.128.0" , True)
])
def test_is_valid_subnet_mask(value, exp_output):
    resp = network_connections.is_valid_subnet_mask(value)
    assert resp == exp_output

@pytest.mark.parametrize("gateway, network_ip, subnet, exp_output", [
    ("127.0.0.1","127.0.0.0", "255.255.255.0" , False),  
    ("192.168.1.18","", "255.255.255.0" , False), 
    ("","192.168.1.18", "255.255.255.0" , False), 
    ("192.168.1.18","192.168.1.0", "" , False), 
    ("192.168.1.18","192.168.1.0", "255.255.255.0" , True), 
    ("192.168.1.0","192.168.1.0", "255.255.255.0" , False), 
    ("192.168.1.255","192.168.1.0", "255.255.255.0" , False)
])
def test_is_valid_gateway(gateway, network_ip, subnet, exp_output):
    resp = network_connections.is_valid_gateway(gateway, network_ip, subnet)
    assert resp == exp_output

@pytest.mark.parametrize("ipv4_settings, exp_bool, exp_string", [
    ({
        "address": "192.168.0.18",
        "netmask": "255.255.255.0",
        "gateway": "192.168.0.1",
        "dns": "83.255.255.1"

    } , True, ""),
    ({
        "address": "192.168.0.18",
        "netmask": "255.255.255.0",
        "gateway": "192.168.0.1"

    } , False, "ipv4_settings should contain only address, netmask, dns and gateway"),
    ({
        "address": "192.168.0.18",
        "netmask": "255.255.255.0",
        "gateway": "192.168.0.1",
        "dns": "83.255.255.1",
        "test" : "val"

    } , False, "ipv4_settings should contain only address, netmask, dns and gateway"),
    ({
        "address": "192.168.0.18.600",
        "netmask": "255.255.255.0",
        "gateway": "192.168.0.1",
        "dns": "83.255.255.1"

    } , False, "Invalid address!"),
    ({
        "address": "192.168.0.18",
        "netmask": "255.255.18.0",
        "gateway": "192.168.0.1",
        "dns": "83.255.255.1"

    } , False, "Invalid netmask!"),
    ({
        "address": "192.168.0.18",
        "netmask": "255.255.255.0",
        "gateway": "192.168.0.255",
        "dns": "83.255.255.1"

    } , False, "Invalid gateway!"),
    ({
        "address": "192.168.0.18",
        "netmask": "255.255.255.0",
        "gateway": "192.168.0.1",
        "dns": "83.255.255.1.9"

    } , False, "Invalid dns!"),
    (None , False, "Invalid ipv4_settings format")
])
def test_validate_ipv4_settings(ipv4_settings, exp_bool, exp_string):
    (resp, err) = network_connections.validate_ipv4_settings(ipv4_settings)
    assert resp == exp_bool
    assert err == exp_string

def test_get_ipv4_method(mocker):
    mock_fn = mocker.patch("app.components.network_connections.run_privileged_command", return_value =  \
        "connection.id: test \n ipv4.method: random")
    resp = network_connections.get_ipv4_method("test")
    assert resp == "random"
    assert mock_fn.call_count == 1

def test_get_ipv4_settings(mocker):
    mock_fn = mocker.patch("app.components.network_connections.run_privileged_command", return_value =  \
        "GENERAL.DEVICE: test \n" + \
        "GENERAL.TYPE:  wifi \n" + \
        "IP4.ADDRESS[1]: 192.168.0.18/24 \n" + \
        "IP4.GATEWAY: 192.168.0.1 \n" + \
        "IP4.DNS[1]: 83.255.255.1")
    resp = network_connections.get_ipv4_settings("test"
    )
    assert resp == {
        "address": "192.168.0.18",
        "netmask": "255.255.255.0",
        "gateway": "192.168.0.1",
        "dns": "83.255.255.1"
    }
    assert mock_fn.call_count == 1

def test_get_wifi_state(mocker):
    mock_fn = mocker.patch("app.components.network_connections.run_command", return_value = "enabled")
    resp = network_connections.get_wifi_state()
    assert resp == "enabled"
    assert mock_fn.call_count == 1

def test_get_ethernet_state(mocker):
    mock_fn = mocker.patch("app.components.network_connections.run_command", return_value = "enabled")
    resp = network_connections.get_ethernet_state()
    assert resp == "enabled"
    assert mock_fn.call_count == 1

def test_get_available_wifi(mocker):
    mock_fn = mocker.patch("app.components.network_connections.run_privileged_command", 
    return_value = \
        "SSID:      test \n" + \
        "SECURITY:  WPA2 \n" + \
        "DEVICE:    wlp0s20f3 \n" + \
        "SIGNAL:    90 \n" + \
        "RATE:      540 Mbit/s"
    )
    resp = network_connections.get_available_wifi()
    assert resp == [
        {
            "ssid": "test",
            "security": "WPA2",
            "device": "wlp0s20f3",
            "signal": "90",
            "rate": "540 Mbit/s"
    }]
    assert mock_fn.call_count == 1

@pytest.mark.parametrize("ip_route, exp_output", [
    ("[" + \
        '{"dst":"default","gateway":"192.168.0.1","dev":"wlp0s20f3","protocol":"dhcp","prefsrc":"192.168.0.18","metric":600,"flags":[]},' + \
        '{"dst":"172.17.0.0/16","dev":"docker0","protocol":"kernel","scope":"link","prefsrc":"172.17.0.1","flags":["linkdown"]},' + \
        '{"dst":"172.18.0.0/16","dev":"br-3ee261d41a38","protocol":"kernel","scope":"link","prefsrc":"172.18.0.1","flags":["linkdown"]}]' ,
         {"dst":"default","gateway":"192.168.0.1","dev":"wlp0s20f3","protocol":"dhcp","prefsrc":"192.168.0.18","metric":600,"flags":[]}
    ),  
    ("[" + \
        '{"dst":"172.17.0.0/16","dev":"docker0","protocol":"kernel","scope":"link","prefsrc":"172.17.0.1","flags":["linkdown"]},' + \
        '{"dst":"172.18.0.0/16","dev":"br-3ee261d41a38","protocol":"kernel","scope":"link","prefsrc":"172.18.0.1","flags":["linkdown"]}]', 
        []
    )
])
def test_get_default_route(mocker,ip_route, exp_output ):
    mock_fn = mocker.patch("app.components.network_connections.run_command", return_value = ip_route)
    resp = network_connections.get_default_route()
    assert resp == exp_output
    assert mock_fn.call_count == 1


@pytest.mark.parametrize("show_connections, exp_output", [
    (   
        'NAME:             Tele2_1c65c4 \n' + \
        'TYPE:             wifi \n' + \
        'DEVICE:           wlp0s20f3 \n' + \
        'NAME:             lo \n' + \
        'TYPE:             loopback \n' + \
        'DEVICE:           lo \n' + \
        'NAME:             br-3ee261d41a38 \n' + \
        'TYPE:             bridge \n' + \
        'DEVICE:           br-3ee261d41a38',
        []
    ),  
    (   
        'NAME:             Tele2_1c65c4 \n' + \
        'TYPE:             wifi \n' + \
        'DEVICE:           wlp0s20f3 \n' + \
        'NAME:             lo \n' + \
        'TYPE:             loopback \n' + \
        'DEVICE:           lo \n' + \
        'NAME:             Ethernet 2 \n' + \
        'TYPE:             ethernet \n' + \
        'DEVICE:           enp0s8' ,
        [{
            "name" : "Ethernet 2",
            "type" : "ethernet",
            "device" : "enp0s8"
        }]
    ),  
])
def test_get_available_ethernet(mocker, show_connections, exp_output):
    mock_fn = mocker.patch("app.components.network_connections.run_privileged_command", return_value = show_connections)
    resp = network_connections.get_available_ethernet()
    assert resp == exp_output
    assert mock_fn.call_count == 1

def test_get_current_active_connections(mocker):
    connection_output = 'NAME:             Tele2_1c65c4 \n' + \
        'TYPE:             wifi \n' + \
        'DEVICE:           wlp0s20f3 \n' + \
        'NAME:             lo \n' + \
        'TYPE:             loopback \n' + \
        'DEVICE:           lo \n' + \
        'NAME:             Ethernet 2 \n' + \
        'TYPE:             ethernet \n' + \
        'DEVICE:           enp0s8' 
    mock_run_priv_command = mocker.patch("app.components.network_connections.run_privileged_command", return_value = connection_output)
    mock_get_ipv4_method = mocker.patch("app.components.network_connections.get_ipv4_method", return_value = "test_method")
    mock_get_ipv4_settings = mocker.patch("app.components.network_connections.get_ipv4_settings", return_value = {"test: val"})
    
    # test default params:
    exp_output = [
        {
            "name" : "Tele2_1c65c4",
            "type" : "wifi",
            "device" : "wlp0s20f3",
            "ipv4_method" : "test_method",
            "ipv4_settings" : {"test: val"}
        },
        {
            "name" : "Ethernet 2",
            "type" : "ethernet",
            "device" : "enp0s8",
            "ipv4_method" : "test_method",
            "ipv4_settings" : {"test: val"}
        }]
    resp = network_connections.get_current_active_connections()
    assert resp == exp_output
    
    # test custom params:
    exp_output = [
        {
            "name" : "lo",
            "type" : "loopback",
            "device" : "lo",
            "ipv4_method" : "test_method",
            "ipv4_settings" : {"test: val"}
        }]
    resp = network_connections.get_current_active_connections(["loopback"])
    assert resp == exp_output

    # when type not present in connections
    exp_output = []
    resp = network_connections.get_current_active_connections(["test"])
    assert resp == exp_output

    #when types is None
    exp_output = []
    resp = network_connections.get_current_active_connections(None)
    assert resp == exp_output


def test_get_netwok_settings(mocker):
    exp_output = {
        "wifi_state": "enabled",
        "ethernet_state": "enabled",
        "available_wifi": [
            {
                "ssid": "Tele2_1c65c4",
                "security": "WPA2",
                "device": "wlp0s20f3",
                "signal": "87",
                "rate": "540 Mbit/s"
            },
            {
                "ssid": "Tele2_1c65c4",
                "security": "WPA2",
                "device": "wlp0s20f3",
                "signal": "80",
                "rate": "540 Mbit/s"
            }
        ],
        "available_ethernet": [],
        "active_connections": [
            {
                "name": "Tele2_1c65c4",
                "type": "wifi",
                "device": "wlp0s20f3",
                "ipv4_method": "auto",
                "ipv4_settings": {
                    "address": "192.168.0.18",
                    "netmask": "255.255.255.0",
                    "gateway": "192.168.0.1",
                    "dns": "83.255.255.1"
                }
            }
        ],
        "fetching_status": "success"
    }
    mocker.patch("app.components.network_connections.get_wifi_state", return_value = exp_output["wifi_state"])
    mocker.patch("app.components.network_connections.get_ethernet_state", return_value = exp_output["ethernet_state"])
    mocker.patch("app.components.network_connections.get_available_wifi", return_value = exp_output["available_wifi"])
    mocker.patch("app.components.network_connections.get_available_ethernet", return_value = exp_output["available_ethernet"])
    mocker.patch("app.components.network_connections.get_current_active_connections", return_value = exp_output["active_connections"])
    
    resp = network_connections.get_netwok_settings()
    assert resp == exp_output

    # test failure
    def raise_err():
        raise subprocess.CalledProcessError(returncode=1, cmd="", stderr= "invalid!")
    mocker.patch("app.components.network_connections.get_current_active_connections", side_effect=raise_err)
    del exp_output["active_connections"]
    exp_output["fetching_status"] = "failure"

    resp = network_connections.get_netwok_settings()
    assert resp == exp_output

def test_set_ipv4_settings_auto(mocker):
    mock_cur_connection =  [
        {
            "name": "test"
        }
    ]
    mocker.patch("app.components.network_connections.get_current_active_connections", return_value = mock_cur_connection)
    mock_run_command = mocker.patch("app.components.network_connections.run_privileged_command", return_value = "")
    network_connections.set_ipv4_settings("auto", {},"conn_type")
    expected_calls = [
        call(['nmcli', 'connection', 'modify', 'test', 'ipv4.method', 'auto']),
        call(['nmcli', 'connection', 'modify', 'test', 'ipv4.gateway', '']),
        call(['nmcli', 'connection', 'modify', 'test', 'ipv4.dns', '']),
        call(['nmcli', 'connection', 'modify', 'test', 'ipv4.addresses', '']),
        call(['nmcli', 'connection', 'down', 'test']),
        call(['nmcli', 'connection', 'up', 'test']),
    ]
    assert mock_run_command.call_args_list == expected_calls

def test_set_ipv4_settings_no_active_connection(mocker):
    mock_cur_connection =  []
    mocker.patch("app.components.network_connections.get_current_active_connections", return_value = mock_cur_connection)
    mock_run_command = mocker.patch("app.components.network_connections.run_privileged_command", return_value = "")
    try:
        network_connections.set_ipv4_settings("auto", {},"conn_type")
        assert False
    except HTTPException as e:
        assert e.status_code == 400
        assert e.detail == "No active connections"

def test_set_ipv4_settings_manual(mocker):
    mock_cur_connection =  [
        {
            "name": "test"
        }
    ]
    mocker.patch("app.components.network_connections.get_current_active_connections", return_value = mock_cur_connection)
    mock_run_command = mocker.patch("app.components.network_connections.run_privileged_command", return_value = "")
    network_connections.set_ipv4_settings("manual", 
    {
        "address": "192.168.0.18",
        "netmask": "255.255.255.0",
        "gateway": "192.168.0.1",
        "dns": "83.255.255.1"
    },"conn_type")
    expected_calls = [
        call(['nmcli', 'connection', 'modify', 'test', 'ipv4.addresses', '192.168.0.18/24']),
        call(['nmcli', 'connection', 'modify', 'test', 'ipv4.gateway', '192.168.0.1']),
        call(['nmcli', 'connection', 'modify', 'test', 'ipv4.dns', '83.255.255.1']),
        call(['nmcli', 'connection', 'modify', 'test', 'ipv4.method', 'manual']),
        call(['nmcli', 'connection', 'down', 'test']),
        call(['nmcli', 'connection', 'up', 'test']),
    ]
    assert mock_run_command.call_args_list == expected_calls

def test_set_ipv4_settings_manual_invalid(mocker):
    mock_cur_connection =  [
        {
            "name": "test"
        }
    ]
    mocker.patch("app.components.network_connections.get_current_active_connections", return_value = mock_cur_connection)
    mock_run_command = mocker.patch("app.components.network_connections.run_privileged_command", return_value = "")
    try:
        network_connections.set_ipv4_settings("manual", 
        {
            "address": "192.168.0.18",
            "netmask": "255.255.255.0"
        },"conn_type")
        assert False
    except HTTPException as e:
        assert e.status_code == 422
        assert  "Invalid ipv4 settings." in e.detail


def test_set_ipv4_settings_run_error(mocker):
    mock_cur_connection =  [
        {
            "name": "test"
        }
    ]
    mocker.patch("app.components.network_connections.get_current_active_connections", return_value = mock_cur_connection)
    def raise_err(cmd):
        raise subprocess.CalledProcessError(returncode=1, cmd="", stderr= "invalid!")
    mocker.patch("app.components.network_connections.run_privileged_command", side_effect=raise_err)
    try:
        network_connections.set_ipv4_settings("manual", 
        {
            "address": "192.168.0.18",
            "netmask": "255.255.255.0",
            "gateway": "192.168.0.1",
            "dns": "83.255.255.1"
        },"conn_type")
        assert False
    except HTTPException as e:
        assert e.status_code == 500
        assert e.detail == "Could not set network settings!"

def test_set_wifi_state(mocker):
    mock_fn = mocker.patch("app.components.network_connections.run_privileged_command", return_value = "")
    network_connections.set_wifi_state(True)
    assert mock_fn.call_count == 1
    assert mock_fn.call_args.args == (['nmcli', 'radio', 'wifi', 'on'],)

    network_connections.set_wifi_state(False)
    assert mock_fn.call_count == 2
    assert mock_fn.call_args.args == (['nmcli', 'radio', 'wifi', 'off'],)

def test_connect_wifi_ssid_not_found(mocker):
    mock_available_wifi =  []
    mocker.patch("app.components.network_connections.get_available_wifi", return_value = mock_available_wifi)
    try:
        network_connections.connect_wifi("test","test")
        assert False
    except HTTPException as e:
        assert e.status_code == 404
        assert e.detail == "Network settings: Given ssid is invalid"

def test_connect_wifi_already_connected(mocker):
    mock_available_wifi = [{
        "ssid" : "test"
    }]
    mocker.patch("app.components.network_connections.get_available_wifi", return_value = mock_available_wifi)
    mock_cur_active_connections = [
        {
            "name" : "test",
            "type" : "wifi"
        },
        {
            "name" : "Ethernet 2",
            "type" : "ethernet"
        }]
    mocker.patch("app.components.network_connections.get_current_active_connections", return_value = mock_cur_active_connections)
    mock_fn = mocker.patch("app.components.network_connections.run_privileged_command", return_value = "")
    network_connections.connect_wifi("test","test")
    network_connections.connect_wifi("test",None)
    assert mock_fn.call_count == 0
      
def test_connect_wifi_run_error(mocker):
    mock_available_wifi = [{
        "ssid" : "test",
        "security" : "WPA2"
    }]
    mocker.patch("app.components.network_connections.get_available_wifi", return_value = mock_available_wifi)
    mock_cur_active_connections = [
        {
            "name" : "Ethernet 2",
            "type" : "ethernet"
        }]
    mocker.patch("app.components.network_connections.get_current_active_connections", return_value = mock_cur_active_connections)
    def raise_err(cmd):
        raise subprocess.CalledProcessError(returncode=1, cmd="", stderr= "")
    def raise_password_err(cmd):
        raise subprocess.CalledProcessError(returncode=1, cmd="", stderr= "Secrets were required")
    mocker.patch("app.components.network_connections.run_privileged_command", side_effect=raise_err)

    try:
        network_connections.connect_wifi("test","test")
        assert False
    except HTTPException as e:
        assert e.status_code == 500

    mocker.patch("app.components.network_connections.run_privileged_command", side_effect=raise_password_err)
    try:
        network_connections.connect_wifi("test","test")
        assert False
    except HTTPException as e:
        assert e.status_code == 400
        assert e.detail == "Password is invalid"

@pytest.mark.parametrize("ssid, password, sel_conn, active_conn, exp_cmd, is_error, err_code", [
    ("test","test", [{
            "ssid" : "test",
            "security" : "WPA2"
        }], 
        [
        {
            "name" : "Ethernet 2",
            "type" : "ethernet"
        }],
        ['nmcli', 'device', 'wifi', 'connect', 'test', 'password', 'test'],
        False, 0), 
    ("test",None, [{
            "ssid" : "test",
            "security" : ""
        }], 
        [
        {
            "name" : "wifi1",
            "type" : "wifi"
        }],
        ['nmcli', 'device', 'wifi', 'connect', 'test'],
        False, 0), 
    ("test",None, [{
            "ssid" : "test",
            "security" : "WPA2"
        }], 
        [
        {
            "name" : "Ethernet 2",
            "type" : "ethernet"
        }],
        ['nmcli', 'device', 'wifi', 'connect', 'test'],
        True, 422), 
])
def test_connect_wifi_multiple_cases(mocker,ssid, password, sel_conn, active_conn, exp_cmd,is_error, err_code):
    mocker.patch("app.components.network_connections.get_available_wifi", return_value = sel_conn)
    mocker.patch("app.components.network_connections.get_current_active_connections", return_value = active_conn)
    mock_run_cmd = mocker.patch("app.components.network_connections.run_privileged_command", return_value = active_conn)
    try:
        network_connections.connect_wifi(ssid,password)
        assert not is_error
        assert mock_run_cmd.call_count == 1
        assert mock_run_cmd.call_args.args == (exp_cmd,)
    except HTTPException as e:
        assert is_error
        assert e.status_code == err_code


    
@pytest.mark.parametrize("nw_settings,set_wifi_call_count, set_wifi_args", [
({
    "type" : "wifi",
    "test" : "val",
    "wifi_state" : "enabled"
}, 1, call(True)),
({
    "wifi_state" : "disabled"
}, 1, call(False)),
({
    "type" : "wifi",
    "test" : "val"
}, 0, None),
])
def test_set_network_settings_wifi_state(mocker, nw_settings, set_wifi_call_count, set_wifi_args):
    mock_set_wifi = mocker.patch("app.components.network_connections.set_wifi_state", return_value = "")
    mocker.patch("app.components.network_connections.connect_wifi", return_value = "")
    mocker.patch("app.components.network_connections.set_ipv4_settings", return_value = "")
    network_connections.set_network_settings(nw_settings)
    assert mock_set_wifi.call_count == set_wifi_call_count
    assert mock_set_wifi.call_args == set_wifi_args

@pytest.mark.parametrize("nw_settings, connect_wifi_call_count, connect_wifi_args ", [
({
    "type" : "wifi",
    "test" : "val",
    "wifi_state" : "enabled",
    "ssid" : "test"
}, 1, call("test",None)),
({
    "wifi_state" : "disabled",
    "ssid" : "test",
    "password" : "pass"
}, 1, call("test","pass")),
({
    "type" : "wifi",
    "test" : "val"
}, 0, None),
])
def test_set_network_settings_wifi_state(mocker, nw_settings, connect_wifi_call_count, connect_wifi_args):
    mocker.patch("app.components.network_connections.set_wifi_state", return_value = "")
    mock_connect_wifi =mocker.patch("app.components.network_connections.connect_wifi", return_value = "")
    mocker.patch("app.components.network_connections.set_ipv4_settings", return_value = "")
    network_connections.set_network_settings(nw_settings)
    assert mock_connect_wifi.call_count == connect_wifi_call_count
    assert mock_connect_wifi.call_args == connect_wifi_args

@pytest.mark.parametrize("nw_settings, is_err, err_code,  set_ipv4_call_count, set_ipv4_args ", [
({
    "type" : "wifi",
    "ipv4_method" : "auto"
    
}, False, 0, 1, call("auto",{}, "wifi")),
({
    "ipv4_method" : "auto"
    
}, False, 0, 1, call("auto",{}, None)),
({
    "type" : "ethernet",
    "ipv4_method" : "manual",
    "ipv4_settings" : {"test":"val"}
    
}, False, 0, 1, call("manual",{"test":"val"}, "ethernet")),
({
    "type" : "wifi",
    "ipv4_method" : "random"
    
}, True, 422, 0, None),
])
def test_set_network_settings_ipv4_settings(mocker, nw_settings, is_err, err_code,  set_ipv4_call_count, set_ipv4_args):
    mocker.patch("app.components.network_connections.set_wifi_state", return_value = "")
    mocker.patch("app.components.network_connections.connect_wifi", return_value = "")
    mock_set_ipv4 =mocker.patch("app.components.network_connections.set_ipv4_settings", return_value = "")
    try:
        network_connections.set_network_settings(nw_settings)
        assert not is_err
        assert mock_set_ipv4.call_count == set_ipv4_call_count
        assert mock_set_ipv4.call_args == set_ipv4_args
    except HTTPException as e:
        assert is_err
        assert e.status_code == err_code