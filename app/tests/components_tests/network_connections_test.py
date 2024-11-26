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