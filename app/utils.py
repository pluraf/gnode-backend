import os
import subprocess


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
