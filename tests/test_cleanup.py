import os
import sys
import time
from unittest.mock import MagicMock, patch

# Ensure the main module can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import main


def test_context_manager_runs_pkill_preemptively():
    debug_logger = main.DebugLogger(start_time=time.time())

    fake_service = MagicMock()
    fake_service.process = MagicMock()
    fake_driver = MagicMock()

    with (
        patch("main.subprocess.run") as mock_run,
        patch.object(main, "ChromeService", return_value=fake_service),
        patch.object(main.webdriver, "Chrome", return_value=fake_driver),
        patch.object(main, "log_running_chromedriver_processes"),
    ):
        opts = main.Options()
        with main.managed_webdriver_session(opts, debug_logger):
            pass
        # Pre-emptive cleanup should have been invoked
        mock_run.assert_any_call("pkill -f '[c]hromedriver'", shell=True, check=False)


def test_context_manager_yields_none_on_setup_failure():
    debug_logger = main.DebugLogger(start_time=time.time())

    with (
        patch("main.subprocess.run") as mock_run,
        patch.object(main, "ChromeService") as mock_service,
        patch.object(main.webdriver, "Chrome", side_effect=RuntimeError("boom")),
        patch.object(main, "log_running_chromedriver_processes"),
    ):
        mock_service.return_value.process = MagicMock()
        opts = main.Options()
        with main.managed_webdriver_session(opts, debug_logger) as driver:
            assert driver is None
        # Ensure pkill was attempted even when setup fails
        mock_run.assert_any_call("pkill -f '[c]hromedriver'", shell=True, check=False)
