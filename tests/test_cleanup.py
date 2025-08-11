import os
import sys
from unittest.mock import patch

# Ensure the main module can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import main


def test_cleanup_old_processes_invokes_pkill():
    with patch("main.subprocess.run") as mock_run:
        main.cleanup_old_processes()
        mock_run.assert_called()
        args, kwargs = mock_run.call_args
        # Ensure pkill is targeted at chromedriver with -f and shell=True
        assert "pkill -f '[c]hromedriver'" in args[0]
        assert kwargs.get("shell") is True
        assert kwargs.get("check") is False


def test_cleanup_old_processes_handles_exception():
    with patch("main.subprocess.run", side_effect=RuntimeError("boom")):
        # Should not raise
        main.cleanup_old_processes()
