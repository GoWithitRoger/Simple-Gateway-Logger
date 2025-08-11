import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# Ensure the main module can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import config as config_module
import main as main_module
from main import perform_checks

# --- Mocks for all task functions ---


@pytest.fixture
def mock_tasks():
    """Mocks all the individual task functions and log_results."""
    with (
        patch("main.run_wifi_diagnostics_task", return_value={}) as mock_wifi,
        patch("main.run_local_ping_task", return_value={}) as mock_local_ping,
        patch("main.run_local_speed_test_task", return_value={}) as mock_local_speed,
        patch("main.run_ping_test_task", return_value={}) as mock_gateway_ping,
        patch("main.run_speed_test_task", return_value={}) as mock_gateway_speed,
        patch("main.subprocess.run") as mock_subproc_run,
        patch("main.log_results") as mock_log,
        patch("main.webdriver.Chrome", return_value=MagicMock()) as mock_chrome,
        patch("main.get_access_code", return_value="test-code") as mock_access_code,
        patch("main.ChromeService") as mock_service,
        patch("main.time.sleep"),
    ):
        mock_service.return_value.process = MagicMock()

        yield {
            "wifi": mock_wifi,
            "local_ping": mock_local_ping,
            "local_speed": mock_local_speed,
            "gateway_ping": mock_gateway_ping,
            "gateway_speed": mock_gateway_speed,
            "subprocess_run": mock_subproc_run,
            "log": mock_log,
            "chrome": mock_chrome,
            "access_code": mock_access_code,
        }


# --- Tests for perform_checks orchestration ---


def test_perform_checks_local_ping_toggle(mock_tasks, monkeypatch):
    """Tests that RUN_LOCAL_PING_TEST config toggles the task call."""
    monkeypatch.setattr(config_module, "RUN_LOCAL_GATEWAY_PING_TEST", False)

    monkeypatch.setattr(config_module, "RUN_LOCAL_PING_TEST", True)
    perform_checks()
    mock_tasks["local_ping"].assert_called_with("google.com")

    mock_tasks["local_ping"].reset_mock()

    monkeypatch.setattr(config_module, "RUN_LOCAL_PING_TEST", False)
    perform_checks()
    mock_tasks["local_ping"].assert_not_called()


def test_perform_checks_local_gateway_ping_toggle(mock_tasks, monkeypatch):
    """Tests that RUN_LOCAL_GATEWAY_PING_TEST config toggles the task call."""
    monkeypatch.setattr(config_module, "RUN_LOCAL_PING_TEST", False)

    monkeypatch.setattr(config_module, "RUN_LOCAL_GATEWAY_PING_TEST", True)
    perform_checks()
    # It's called run_local_ping_task, but with the gateway IP
    mock_tasks["local_ping"].assert_called_with("192.168.1.254")

    mock_tasks["local_ping"].reset_mock()

    monkeypatch.setattr(config_module, "RUN_LOCAL_GATEWAY_PING_TEST", False)
    perform_checks()
    mock_tasks["local_ping"].assert_not_called()


def test_perform_checks_local_speed_test_toggle(mock_tasks, monkeypatch):
    """Tests that RUN_LOCAL_SPEED_TEST config toggles the task call."""
    monkeypatch.setattr(config_module, "RUN_LOCAL_SPEED_TEST", True)
    perform_checks()
    mock_tasks["local_speed"].assert_called_once()

    mock_tasks["local_speed"].reset_mock()

    monkeypatch.setattr(config_module, "RUN_LOCAL_SPEED_TEST", False)
    perform_checks()
    mock_tasks["local_speed"].assert_not_called()


def test_perform_checks_gateway_speed_test_interval(mock_tasks, monkeypatch):
    """Tests that RUN_GATEWAY_SPEED_TEST_INTERVAL config works correctly."""
    # Reset the global run counter for predictable behavior
    main_module.run_counter = 0

    # Run on interval 2.
    monkeypatch.setattr(config_module, "RUN_GATEWAY_SPEED_TEST_INTERVAL", 2)

    # Should NOT run on first call (run #1)
    perform_checks()  # Run 1
    mock_tasks["gateway_speed"].assert_not_called()

    # Note: Pre-emptive cleanup now occurs within the context manager.
    # Dedicated tests cover that behavior in tests/test_cleanup.py.


def test_perform_checks_gateway_speed_test_disabled(mock_tasks, monkeypatch):
    """Tests that gateway speed test is disabled when interval is 0."""
    main_module.run_counter = 0
    monkeypatch.setattr(config_module, "RUN_GATEWAY_SPEED_TEST_INTERVAL", 0)

    perform_checks()
    perform_checks()

    mock_tasks["gateway_speed"].assert_not_called()
