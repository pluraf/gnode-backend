import subprocess
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status

from app.utils import get_mode, run_privileged_command, run_command


def delete_old_ntp_servers():
    try:
        ntp_sources = run_privileged_command(['chronyc', 'ntpdata'])
        ntp_servers = []
        for line in ntp_sources.splitlines():
            if line.startswith("Remote address"):
                server = line.split(":")[1].strip()
                ntp_servers.append(server)
        for server in ntp_servers:
            run_privileged_command(['chronyc', 'delete', server])
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code = 500, detail = f"Failed to remove old servers!")


def set_time_manual(date_time, time_zone):
    try:
        run_privileged_command(['timedatectl', 'set-ntp', 'false'])
        run_privileged_command(['timedatectl', 'set-local-rtc', '0'])
        run_privileged_command(['timedatectl', 'set-timezone', time_zone])
        run_privileged_command(
            '/usr/bin/env DEBIAN_FRONTEND=noninteractive /usr/sbin/dpkg-reconfigure tzdata',
            shell=True
        )
        run_privileged_command(['date', '--set', date_time])
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code = 500, detail = f"Failed to set system time!")


def set_time_auto(ntp_server, time_zone):
    try:
        run_privileged_command(['timedatectl', 'set-local-rtc', '0'])
        run_privileged_command(['timedatectl', 'set-timezone', time_zone])
        run_privileged_command(
            '/usr/bin/env DEBIAN_FRONTEND=noninteractive /usr/sbin/dpkg-reconfigure tzdata',
            shell=True
        )
        run_privileged_command(['systemctl', 'restart', 'chrony.service'])
        delete_old_ntp_servers()
        run_privileged_command(['chronyc', 'add', 'server', ntp_server, 'iburst'])
        run_privileged_command(['chronyc', 'makestep'])
    except subprocess.CalledProcessError as e:
        detail = "Failed to sync system time"
        if "Invalid host/IP address" in e.stderr:
            detail = "Invalid NTP server address"
        raise HTTPException(status_code = 500, detail = detail)


def set_gnode_time(user_input):
    if get_mode() == "virtual":
        raise HTTPException(
            status_code=status.HTTP_301_MOVED_PERMANENTLY,
            detail="Time settings are not available in virtual mode."
        )

    if not user_input.get('automatic'):
        date = user_input.get('date')
        time = user_input.get('time')
        time_zone = user_input.get('timezone')
        if not date or not time or not time_zone:
            raise HTTPException(status_code = 422, detail = "Missing required field!")
        date_time = f"{date} {time}"
        set_time_manual(date_time, time_zone)
    else:
        time_zone = user_input.get('timezone')
        ntp_server = user_input.get('ntp_server')
        if not time_zone:
            raise HTTPException(status_code = 422, detail = "Missing required field!")
        set_time_auto(ntp_server, time_zone)

    run_privileged_command(["hwclock", "--systohc", "--utc"])


def get_gnode_time():
    time_conf = run_command(["timedatectl", "show"])
    for line in time_conf.splitlines():
        try:
            key, value = map(str.strip, line.split("="))
        except IndexError:
            continue
        if key == "NTP":  # Detect current mode
            auto = value == "yes"
        elif key == "Timezone":  # Detect current timezone
            current_timezone = value
    now = datetime.now(ZoneInfo(current_timezone))
    # Return summary
    return {
        "timestamp": now.timestamp(),
        "iso8601": now.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "timezone": current_timezone,
        "auto": auto
    }

def list_timezones():
    try:
        result = run_command(['timedatectl', 'list-timezones'])
        timezone_list = result.splitlines()
        return timezone_list
    except subprocess.CalledProcessError as e:
        return []