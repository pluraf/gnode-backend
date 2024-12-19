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