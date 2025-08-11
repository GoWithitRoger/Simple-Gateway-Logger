import os
import sys
from unittest.mock import mock_open, patch

import pytest

# Ensure the main module can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import config
from main import Colors, log_results, perform_checks


@patch("builtins.open", new_callable=mock_open)
@patch("main.os.path.exists", return_value=False)
@patch("builtins.print")
def test_log_results_includes_bufferbloat_fields_and_highlighting(
    mock_print, mock_exists, mock_open_file
) -> None:
    # Configure threshold so our values trigger highlighting
    config.ENABLE_ANOMALY_HIGHLIGHTING = True
    config.BUFFERBLOAT_DELTA_THRESHOLD = 10.0

    row = {
        # Minimal fields used by log_results
        "gateway_loss_percentage": 0.0,
        "gateway_rtt_avg_ms": 10.0,
        "downstream_speed": None,
        "upstream_speed": None,
        "local_wan_loss_percentage": 0.0,
        "local_wan_rtt_avg_ms": 15.0,
        "local_wan_ping_stddev": 1.0,
        "local_gw_loss_percentage": 0.0,
        "local_gw_rtt_avg_ms": 5.0,
        "local_gw_ping_stddev": 0.5,
        "local_downstream_speed": 100.0,
        "local_upstream_speed": 10.0,
        "local_speedtest_jitter": 1.0,
        # Bufferbloat deltas already computed upstream
        "download_bufferbloat_ms": 15.5,  # > 10.0 threshold
        "upload_bufferbloat_ms": 11.0,  # > 10.0 threshold
        # Under-load raw metrics
        "local_latency_down_load_ms": 30.5,
        "local_latency_up_load_ms": 20.0,
        "local_packet_loss_pct": 0.0,
        "wifi_bssid": "aa:bb:cc:dd:ee:ff",
        "wifi_channel": "1,20",
        "wifi_rssi": "-50",
        "wifi_noise": "-90",
        "wifi_tx_rate": "300",
    }

    log_results(row)

    # CSV header contains the new fields
    handle = mock_open_file()
    header = handle.mock_calls[1][1][0]
    assert "Download_Bufferbloat_ms" in header
    assert "Upload_Bufferbloat_ms" in header

    # Console output contains highlighted bufferbloat lines
    all_output = " ".join([str(call.args[0]) for call in mock_print.call_args_list if call.args])
    assert "Download Bufferbloat:" in all_output
    assert "Upload Bufferbloat:" in all_output
    assert f"{Colors.RED}15.50{Colors.RESET}" in all_output
    assert f"{Colors.RED}11.00{Colors.RESET}" in all_output


@patch("main.run_wifi_diagnostics_task", return_value={})
@patch("main.run_local_ping_task")
@patch("main.run_local_speed_test_task")
@patch("main.run_ping_test_task", return_value={})
@patch("main.run_speed_test_task", return_value={})
@patch("main.subprocess.run")
@patch("main.log_results")
@patch("main.webdriver.Chrome")
@patch("main.get_access_code", return_value="code")
@patch("main.ChromeService")
@patch("main.time.sleep")
def test_perform_checks_computes_bufferbloat(
    _sleep,
    _service,
    _access,
    _chrome,
    mock_log_results,
    _subproc,
    _gw_speed,
    _gw_ping,
    mock_local_speed,
    mock_local_ping,
    _wifi,
    monkeypatch,
):
    # Arrange config to run local ping and local speed, skip gateway interval
    import main as main_module

    monkeypatch.setattr(config, "RUN_LOCAL_PING_TEST", True)
    monkeypatch.setattr(config, "RUN_LOCAL_GATEWAY_PING_TEST", False)
    monkeypatch.setattr(config, "RUN_LOCAL_SPEED_TEST", True)
    monkeypatch.setattr(config, "RUN_GATEWAY_SPEED_TEST_INTERVAL", 0)

    # Idle RTT and under-load latencies
    mock_local_ping.return_value = {
        "loss_percentage": 0.0,
        "rtt_avg_ms": 20.0,
        "ping_stddev": 1.0,
    }
    mock_local_speed.return_value = {
        "local_latency_down_load_ms": 55.0,
        "local_latency_up_load_ms": 41.0,
        # other fields optional for this test
    }

    # Reset run counter for deterministic behavior
    main_module.run_counter = 0

    # Act
    perform_checks()

    # Assert: log_results called with computed deltas
    assert mock_log_results.call_count == 1
    args, _ = mock_log_results.call_args
    passed = args[0]
    assert passed.get("download_bufferbloat_ms") == pytest.approx(35.0)
    assert passed.get("upload_bufferbloat_ms") == pytest.approx(21.0)
