from fastapi import HTTPException, status

import subprocess

from app.utils import get_mode

def delete_old_ntp_servers():
    try:
        ntp_sources = subprocess.run(
            ['sudo', 'chronyc', 'ntpdata'], 
            check=True, capture_output=True, text=True
        )
        ntp_servers = []
        for line in ntp_sources.stdout.splitlines():
            if line.startswith("Remote address"):
                server = line.split(":")[1].strip()
                ntp_servers.append(server)
        for server in ntp_servers:
            subprocess.run(['sudo', 'chronyc', 'delete', server], check=True)
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code = 500, detail = f"Failed to remove old servers: {e}")


def set_time_manually_physical(date_time, time_zone):
    try:
        subprocess.run(['sudo', 'timedatectl', 'set-ntp', 'false'], check=True)
        subprocess.run(['sudo', 'timedatectl', 'set-local-rtc', '0'], check=True)
        subprocess.run(['sudo', 'timedatectl', 'set-timezone', time_zone], check=True)
        subprocess.run(['sudo', 'date', '--set', date_time], check=True)
        subprocess.run(['sudo', 'timedatectl', 'set-local-rtc', '1'], check=True)
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code = 500, detail = f"Failed to set system time: {e}")


def set_time_manually(date_time, time_zone):
    mode = get_mode()
    if mode == "virtual":
        raise HTTPException(
            status_code=status.HTTP_301_MOVED_PERMANENTLY,
            detail="Time settings are not available in virtual mode."
        )
    return set_time_manually_physical(date_time, time_zone)


def set_time_automatically_physical(ntp_server, time_zone):
    try:
        subprocess.run(['sudo', 'timedatectl', 'set-local-rtc', '0'], check=True)
        subprocess.run(['sudo', 'timedatectl', 'set-timezone', time_zone], check=True)
        subprocess.run(['sudo', 'systemctl', 'restart', 'chrony'], check=True)
        delete_old_ntp_servers()
        subprocess.run(['sudo', 'chronyc', 'add', 'server', ntp_server, 'iburst'], check=True)
        subprocess.run(['sudo', 'chronyc', 'makestep'], check=True)
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code = 500, detail = f"Failed to sync system time: {e}")


def set_time_automatically(ntp_server, time_zone):
    mode = get_mode()
    if mode == "virtual":
        raise HTTPException(
            status_code=status.HTTP_301_MOVED_PERMANENTLY,
            detail="Time settings are not available in virtual mode."
        )
    return set_time_automatically_physical(ntp_server, time_zone)


def set_gnode_time(user_input):
    if not user_input.get('automatic'):
        date = user_input.get('date')
        time = user_input.get('time')
        time_zone = user_input.get('timezone')
        if not date or not time or not time_zone:
            raise HTTPException(status_code = 422, detail = "Missing required field!")
        date_time = f"{date} {time}"
        set_time_manually(date_time, time_zone)
    else:
        time_zone = user_input.get('timezone')
        ntp_server = user_input.get('ntp_server')
        if not time_zone:
            raise HTTPException(status_code = 422, detail = "Missing required field!")
        set_time_automatically(ntp_server, time_zone)


def list_timezones():
    try:
        result = subprocess.run(
            ['timedatectl', 'list-timezones'], 
            capture_output=True, text=True, check=True)
        timezone_list = result.stdout.splitlines()
        return timezone_list
    except subprocess.CalledProcessError as e:
        if e.stderr:
            raise Exception(f"Failed to list timezones: {e.stderr.strip()}")
        else:
            raise Exception("Failed to list timezones")
