import time
from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import MagicMock, mock_open, patch

import pytest

import config
import main


def _make_service_with_process(pid: int = 12345) -> MagicMock:
    process = MagicMock()
    process.pid = pid
    service = MagicMock()
    service.process = process
    return service


def _make_driver() -> MagicMock:
    driver = MagicMock()
    return driver


def test_managed_webdriver_session_teardown_calls_quit_and_kill() -> None:
    debug_logger = main.DebugLogger(start_time=time.time())

    fake_service = _make_service_with_process()
    fake_driver = _make_driver()

    with patch.object(main, "ChromeService", return_value=fake_service):
        with patch.object(main.webdriver, "Chrome", return_value=fake_driver):
            with patch.object(main, "log_running_chromedriver_processes") as mock_log_procs:
                chrome_options = main.Options()
                # Exercise context manager
                with main.managed_webdriver_session(chrome_options, debug_logger) as d:
                    assert d is fake_driver
                # After exit: ensure proper teardown
                fake_driver.quit.assert_called_once()
                fake_service.process.kill.assert_called_once()
                fake_service.process.wait.assert_called_once()
                mock_log_procs.assert_called_once_with(debug_logger)


def test_managed_webdriver_session_handles_missing_pid_gracefully() -> None:
    debug_logger = main.DebugLogger(start_time=time.time())

    fake_service = _make_service_with_process(pid=None)  # type: ignore[arg-type]
    fake_service.process.pid = None
    fake_driver = _make_driver()

    with patch.object(main, "ChromeService", return_value=fake_service):
        with patch.object(main.webdriver, "Chrome", return_value=fake_driver):
            with patch.object(main, "log_running_chromedriver_processes"):
                chrome_options = main.Options()
                with main.managed_webdriver_session(chrome_options, debug_logger):
                    pass
                # Still should attempt kill/wait even without a PID
                fake_driver.quit.assert_called_once()
                fake_service.process.kill.assert_called_once()
                fake_service.process.wait.assert_called_once()


def test_perform_checks_uses_context_manager_once(monkeypatch: pytest.MonkeyPatch) -> None:
    # Configure to ensure the gateway session is actually invoked once
    monkeypatch.setattr(config, "RUN_GATEWAY_SPEED_TEST_INTERVAL", 1, raising=False)
    monkeypatch.setattr(main, "run_counter", 0, raising=False)
    monkeypatch.setattr(config, "RUN_LOCAL_PING_TEST", False, raising=False)
    monkeypatch.setattr(config, "RUN_LOCAL_GATEWAY_PING_TEST", False, raising=False)
    monkeypatch.setattr(config, "RUN_LOCAL_SPEED_TEST", False, raising=False)

    # Stub out local tasks to avoid subprocess work
    monkeypatch.setattr(main, "run_local_ping_task", lambda target: {})
    monkeypatch.setattr(main, "run_local_speed_test_task", lambda: {})
    monkeypatch.setattr(main, "run_wifi_diagnostics_task", lambda: {})

    # Stub Selenium tasks called inside the context
    monkeypatch.setattr(main, "run_ping_test_task", lambda driver: {})
    monkeypatch.setattr(main, "get_access_code", lambda: "dummy")
    monkeypatch.setattr(main, "run_speed_test_task", lambda driver, code: {})

    calls = SimpleNamespace(count=0)

    @contextmanager
    def fake_manager(chrome_options, debug_logger):  # type: ignore[no-untyped-def]
        calls.count += 1
        yield MagicMock()

    monkeypatch.setattr(main, "managed_webdriver_session", fake_manager)

    # Prevent file writes in log_results
    monkeypatch.setattr(main.os.path, "exists", lambda p: False)
    monkeypatch.setattr(main.os.path, "getsize", lambda p: 0)

    # Exercise perform_checks and ensure context manager used once, while mocking open
    with patch("builtins.open", new_callable=mock_open):
        main.perform_checks()
    assert calls.count == 1
