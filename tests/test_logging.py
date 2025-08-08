import os
import sys
from unittest.mock import MagicMock, patch, mock_open, call
import importlib

import pytest

# Ensure the main module can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import log_results, Colors
import config

# --- Test Data ---

MOCK_DATA = {
    "gateway_loss_percentage": 1.5,  # Anomaly
    "gateway_rtt_avg_ms": 45.0,  # Anomaly
    "downstream_speed": 40.0,  # Anomaly
    "upstream_speed": 5.0,  # Anomaly
    "local_wan_loss_percentage": 0.0,
    "local_wan_rtt_avg_ms": 20.0,
    "local_wan_ping_stddev": 5.0,
    "local_gw_loss_percentage": 0.0,
    "local_gw_rtt_avg_ms": 1.0,
    "local_downstream_speed": 450.0,
    "local_upstream_speed": 25.0,
    "local_speedtest_jitter": 12.0,  # Anomaly
    "wifi_bssid": "a1:b2:c3:d4:e5:f6",
    "wifi_channel": "149,80",
    "wifi_rssi": "-55",
    "wifi_noise": "-90",
    "wifi_tx_rate": "866",
}

# --- Tests for log_results function ---

@patch("builtins.open", new_callable=mock_open)
@patch("main.os.path.exists", return_value=False)
def test_log_results_csv_creation(mock_exists, mock_open_file):
    """Tests that a new CSV file is created with a header."""
    log_results(MOCK_DATA)
    handle = mock_open_file()

    header = ("Timestamp,Gateway_LossPercentage,Gateway_RTT_avg_ms,Gateway_Downstream_Mbps,"
              "Gateway_Upstream_Mbps,Local_WAN_LossPercentage,Local_WAN_RTT_avg_ms,"
              "Local_WAN_Ping_StdDev,Local_GW_LossPercentage,Local_GW_RTT_avg_ms,"
                  "Local_GW_Ping_StdDev,Local_Downstream_Mbps,Local_Upstream_Mbps,Local_Speedtest_Jitter_ms,"
              "WiFi_BSSID,WiFi_Channel,WiFi_RSSI,WiFi_Noise,WiFi_TxRate_Mbps\n")

    # The mock records all calls, including the context manager __enter__ and __exit__.
    # We are interested in the calls to the write method.

    # Extract the written data from the mock calls
    written_header = handle.mock_calls[1][1][0]
    written_data_row = handle.mock_calls[2][1][0]

    assert header.strip() == written_header.strip()
    assert MOCK_DATA['wifi_bssid'] in written_data_row

    assert handle.write.call_count == 2


@patch("builtins.open", new_callable=mock_open)
@patch("main.os.path.exists", return_value=True)
@patch("main.os.path.getsize", return_value=100)
def test_log_results_csv_append(mock_getsize, mock_exists, mock_open_file):
    """Tests that log_results appends to an existing CSV without a header."""
    log_results(MOCK_DATA)
    handle = mock_open_file()
    # Header should not be written, only the data row
    handle.write.assert_called_once()
    # Extract the string that was written
    written_string = handle.write.call_args[0][0]
    assert "Timestamp" not in written_string
    assert "1.500" in written_string  # Check for a formatted value


@patch("builtins.print")
def test_log_results_console_output_highlighting(mock_print):
    """Tests that anomaly highlighting works correctly in console output."""
    # Temporarily modify config for this test
    config.ENABLE_ANOMALY_HIGHLIGHTING = True
    config.PACKET_LOSS_THRESHOLD = 1.0
    config.PING_RTT_THRESHOLD = 40.0
    config.GATEWAY_DOWNSTREAM_SPEED_THRESHOLD = 50.0
    config.GATEWAY_UPSTREAM_SPEED_THRESHOLD = 10.0
    config.JITTER_THRESHOLD = 10.0

    log_results(MOCK_DATA)

    # Convert mock_print calls to a single string for easier searching
    all_output = " ".join([str(call.args[0]) for call in mock_print.call_args_list])

    # Check for RED color code on anomalous values
    assert f"{Colors.RED}1.50{Colors.RESET}" in all_output
    assert f"{Colors.RED}45.00{Colors.RESET}" in all_output
    assert f"{Colors.RED}40.00{Colors.RESET}" in all_output
    assert f"{Colors.RED}5.00{Colors.RESET}" in all_output
    assert f"{Colors.RED}12.000{Colors.RESET}" in all_output

    # Check for a non-anomalous value to ensure it's not colored red
    assert f"{Colors.RED}20.00{Colors.RESET}" not in all_output
    # Check for the special CYAN color on Local GW RTT
    assert f"{Colors.CYAN}1.00{Colors.RESET}" in all_output

    # Restore config
    # This is important if other tests depend on the original config
    importlib.reload(config)
