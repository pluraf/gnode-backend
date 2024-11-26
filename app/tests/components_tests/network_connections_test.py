import pytest

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

    } , False, "Invalid dns!")
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

