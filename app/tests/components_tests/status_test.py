import pytest
from unittest.mock import patch

from app.utils import run_command
from app.components import status

@pytest.mark.parametrize("load_state, active_state, sub_state, output", [
    ("loaded","active", "running", status.ServiceStatus.RUNNING ),  
    ("loaded","inactive", "dead", status.ServiceStatus.STOPPED ),  
    ("loaded","failed", "failed", status.ServiceStatus.FAILED ),  
    ("not-found","inactive", "dead", status.ServiceStatus.MALFORMED ),  
    ("masked","inactive", "dead", status.ServiceStatus.MALFORMED ),  
    ("loaded","active", "exited", status.ServiceStatus.STOPPED ),  
    ("loaded","activating", "waiting", status.ServiceStatus.STOPPED )
])
def test_get_systemd_service_status(load_state, active_state, sub_state, output):
    real_run_command = run_command
    def mock_run_command(cmd):
        if cmd[:2] == ['systemctl', 'show'] and \
            cmd[3] == '--property=ActiveState,SubState,LoadState':
            return "LoadState=" + load_state + "\n" + \
                "ActiveState=" + active_state + "\n" + \
                "SubState=" + sub_state
        # For other commands, call the real run_command
        return real_run_command(cmd)
    with patch("app.components.status.run_command", side_effect=mock_run_command):
        res = status.get_systemd_service_status("test_service")
        assert res == output

@pytest.mark.parametrize("supervisor_status, output", [
    ("test RUNNING", status.ServiceStatus.RUNNING),     
    ("test STOPPED", status.ServiceStatus.STOPPED),
    ("test FAILED", status.ServiceStatus.MALFORMED)
])
def test_get_supervisor_service_status(supervisor_status, output):
    real_run_command = run_command
    def mock_run_command(cmd):
        if cmd[:2] == ['supervisorctl', 'show'] :
            return supervisor_status
        # For other commands, call the real run_command
        return real_run_command(cmd)
    with patch("app.components.status.run_command", side_effect=mock_run_command):
        res = status.get_supervisor_service_status("test_service")
        assert res == output