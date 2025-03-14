import pytest

from app.utils import run_command
from app.components import status
from app.utils import get_mode, GNodeMode

@pytest.mark.parametrize("load_state, active_state, sub_state, output", [
    ("loaded","active", "running", status.ServiceStatus.RUNNING ),  
    ("loaded","inactive", "dead", status.ServiceStatus.STOPPED ),  
    ("loaded","failed", "failed", status.ServiceStatus.FAILED ),  
    ("not-found","inactive", "dead", status.ServiceStatus.MALFORMED ),  
    ("masked","inactive", "dead", status.ServiceStatus.MALFORMED ),  
    ("loaded","active", "exited", status.ServiceStatus.STOPPED ),  
    ("loaded","activating", "waiting", status.ServiceStatus.STOPPED )
])
def test_get_systemd_service_status(mocker,load_state, active_state, sub_state, output):
    real_run_command = run_command
    def mock_run_command(cmd):
        if cmd[:2] == ['systemctl', 'show'] and \
            cmd[3] == '--property=ActiveState,SubState,LoadState':
            return "LoadState=" + load_state + "\n" + \
                "ActiveState=" + active_state + "\n" + \
                "SubState=" + sub_state
        # For other commands, call the real run_command
        return real_run_command(cmd)
    mocker.patch("app.components.status.run_command", side_effect=mock_run_command)
    res = status.get_systemd_service_status("test_service")
    assert res == output

@pytest.mark.parametrize("supervisor_status, output", [
    ("test RUNNING", status.ServiceStatus.RUNNING),     
    ("test STOPPED", status.ServiceStatus.STOPPED),
    ("test FAILED", status.ServiceStatus.MALFORMED)
])
def test_get_supervisor_service_status(mocker,supervisor_status, output):
    real_run_command = run_command
    def mock_run_command(cmd):
        if cmd[:2] == ['supervisorctl', 'show'] :
            return supervisor_status
        # For other commands, call the real run_command
        return real_run_command(cmd)
    mocker.patch("app.components.status.run_command", side_effect=mock_run_command)
    res = status.get_supervisor_service_status("test_service")
    assert res == output

@pytest.mark.parametrize("mode", [
    (GNodeMode.PHYSICAL),
    (GNodeMode.VIRTUAL)
])
def test_get_service_status(mocker, mode):
    mocker.patch("app.components.status.get_mode", return_value = mode)
    supervisor_spy = mocker.spy(status, "get_supervisor_service_status")
    systemd_spy = mocker.spy(status, "get_systemd_service_status")
    status.get_service_status("test")
    if mode == GNodeMode.PHYSICAL:
        assert systemd_spy.call_count == 1
        assert supervisor_spy.call_count == 0
    else:
        assert systemd_spy.call_count == 0
        assert supervisor_spy.call_count == 1
