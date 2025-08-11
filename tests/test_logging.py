import importlib
import os
import sys
from typing import Mapping, TypeAlias
from unittest.mock import mock_open, patch

import pytest

# Ensure the main module can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import config
from main import Colors, log_results

# Light typing for inputs to log_results
ResultRow: TypeAlias = Mapping[str, str | float | int | None]

# --- Test Data ---

# Scenario 1: All data is present and correct.
MOCK_DATA_COMPLETE: ResultRow = {
    "gateway_loss_percentage": 1.5,
    "gateway_rtt_avg_ms": 45.0,
    "downstream_speed": 40.0,
    "upstream_speed": 5.0,
    "local_wan_loss_percentage": 0.0,
    "local_wan_rtt_avg_ms": 20.0,
    "local_wan_ping_stddev": 5.0,
    "local_gw_loss_percentage": 0.0,
    "local_gw_rtt_avg_ms": 1.0,
    "local_gw_ping_stddev": 0.531,  # Gateway jitter is present
    "local_downstream_speed": 450.0,
    "local_upstream_speed": 25.0,
    "local_speedtest_jitter": 12.0,
    # New bufferbloat metrics
    "local_latency_down_load_ms": 75.5,
    "local_latency_up_load_ms": 42.0,
    "local_packet_loss_pct": 0.25,
    "wifi_bssid": "a1:b2:c3:d4:e5:f6",
    "wifi_channel": "149,80",
    "wifi_rssi": "-55",
    "wifi_noise": "-90",
    "wifi_tx_rate": "866",
}

# Scenario 2: Gateway ping failed, so its RTT and jitter are missing (None).
MOCK_DATA_MISSING_GW_JITTER: ResultRow = {
    "gateway_loss_percentage": 1.5,
    "gateway_rtt_avg_ms": 45.0,
    "downstream_speed": 40.0,
    "upstream_speed": 5.0,
    "local_wan_loss_percentage": 0.0,
    "local_wan_rtt_avg_ms": 20.0,
    "local_wan_ping_stddev": 5.0,
    "local_gw_loss_percentage": 100.0,
    "local_gw_rtt_avg_ms": None,  # RTT is None
    "local_gw_ping_stddev": None,  # Gateway jitter is None
    "local_downstream_speed": 450.0,
    "local_upstream_speed": 25.0,
    "local_speedtest_jitter": 12.0,
    "wifi_bssid": "a1:b2:c3:d4:e5:f6",
    "wifi_channel": "149,80",
    "wifi_rssi": "-55",
    "wifi_noise": "-90",
    "wifi_tx_rate": "866",
}

# --- Tests for log_results function ---


@patch("builtins.open", new_callable=mock_open)
@patch("main.os.path.exists", return_value=False)
def test_log_results_csv_creation(mock_exists, mock_open_file) -> None:
    """Tests that a new CSV file is created with a header."""
    log_results(MOCK_DATA_COMPLETE)
    handle = mock_open_file()
    written_header = handle.mock_calls[1][1][0]
    written_data_row = handle.mock_calls[2][1][0]
    # Header should include new bufferbloat fields
    assert "Local_Load_Down_ms" in written_header
    assert "Local_Load_Up_ms" in written_header
    assert "Local_Pkt_Loss_Pct" in written_header
    assert MOCK_DATA_COMPLETE["wifi_bssid"] in written_data_row
    # Ensure at least one new value appears in the CSV row with 3-decimal formatting
    assert "75.500" in written_data_row
    assert handle.write.call_count == 2


@patch("builtins.open", new_callable=mock_open)
@patch("main.os.path.exists", return_value=True)
@patch("main.os.path.getsize", return_value=100)
def test_log_results_csv_append(mock_getsize, mock_exists, mock_open_file) -> None:
    """Tests that log_results appends to an existing CSV without a header."""
    log_results(MOCK_DATA_COMPLETE)
    handle = mock_open_file()
    handle.write.assert_called_once()
    written_string = handle.write.call_args[0][0]
    assert "Timestamp" not in written_string
    assert "1.500" in written_string


@patch("builtins.print")
def test_log_results_console_output_highlighting(mock_print) -> None:
    """Tests that anomaly highlighting works correctly in console output."""
    config.ENABLE_ANOMALY_HIGHLIGHTING = True
    config.PACKET_LOSS_THRESHOLD = 1.0
    config.PING_RTT_THRESHOLD = 40.0
    config.GATEWAY_DOWNSTREAM_SPEED_THRESHOLD = 50.0
    config.GATEWAY_UPSTREAM_SPEED_THRESHOLD = 10.0
    config.JITTER_THRESHOLD = 10.0
    config.LATENCY_UNDER_LOAD_THRESHOLD = 100.0
    config.SPEEDTEST_PACKET_LOSS_THRESHOLD = 0.5
    # Use a modified dataset to trigger anomalies for bufferbloat metrics
    data_for_highlighting = dict(MOCK_DATA_COMPLETE)
    data_for_highlighting["local_latency_down_load_ms"] = 150.0  # > 100 threshold
    data_for_highlighting["local_latency_up_load_ms"] = 125.0  # > 100 threshold
    data_for_highlighting["local_packet_loss_pct"] = 0.75  # > 0.5 threshold

    log_results(data_for_highlighting)
    all_output = " ".join([str(call.args[0]) for call in mock_print.call_args_list])

    assert f"{Colors.RED}1.50{Colors.RESET}" in all_output
    assert f"{Colors.RED}45.00{Colors.RESET}" in all_output
    assert f"{Colors.RED}40.00{Colors.RESET}" in all_output
    assert f"{Colors.RED}5.00{Colors.RESET}" in all_output
    assert f"{Colors.RED}12.000{Colors.RESET}" in all_output
    assert f"{Colors.CYAN}1.00{Colors.RESET}" in all_output
    # New assertions: anomalous bufferbloat metrics are highlighted in red
    assert f"{Colors.RED}150.00{Colors.RESET}" in all_output  # Download load latency
    assert f"{Colors.RED}125.00{Colors.RESET}" in all_output  # Upload load latency
    assert f"{Colors.RED}0.75{Colors.RESET}" in all_output  # Packet loss percentage
    importlib.reload(config)


@patch("builtins.print")
def test_log_results_console_boundary_not_highlighted(mock_print) -> None:
    """Values equal to thresholds should NOT be highlighted (strictly greater logic)."""
    config.ENABLE_ANOMALY_HIGHLIGHTING = True
    config.LATENCY_UNDER_LOAD_THRESHOLD = 100.0
    config.SPEEDTEST_PACKET_LOSS_THRESHOLD = 0.50

    data = dict(MOCK_DATA_COMPLETE)
    data["local_latency_down_load_ms"] = 100.0
    data["local_latency_up_load_ms"] = 100.0
    data["local_packet_loss_pct"] = 0.50

    log_results(data)
    all_output = " ".join([str(call.args[0]) for call in mock_print.call_args_list])

    # Ensure red highlighting is NOT applied on boundary equality
    assert f"{Colors.RED}100.00{Colors.RESET}" not in all_output
    assert f"{Colors.RED}0.50{Colors.RESET}" not in all_output
    # Plain uncolored values should appear
    assert "100.00 ms" in all_output
    assert "0.50 %" in all_output


@patch("builtins.open", new_callable=mock_open)
@patch("main.os.path.exists", return_value=False)
def test_log_results_csv_precision_for_new_fields(mock_exists, mock_open_file) -> None:
    """CSV should format floats to 3 decimals for new bufferbloat fields."""
    data = dict(MOCK_DATA_COMPLETE)
    data["local_latency_down_load_ms"] = 1.23456
    data["local_latency_up_load_ms"] = 9.87654
    data["local_packet_loss_pct"] = 0.78901
    log_results(data)
    handle = mock_open_file()
    written_data_row = handle.mock_calls[2][1][0]
    assert ",1.235," in written_data_row
    assert ",9.877," in written_data_row
    assert ",0.789," in written_data_row


@patch("builtins.print")
def test_log_results_console_precision_for_latency_and_packet_loss(mock_print) -> None:
    """Console formatting: latency rounded to 2 decimals, packet loss to 2 decimals."""
    config.ENABLE_ANOMALY_HIGHLIGHTING = False  # Disable colors to check raw strings
    data = dict(MOCK_DATA_COMPLETE)
    data["local_latency_down_load_ms"] = 123.456
    data["local_latency_up_load_ms"] = 7.891
    data["local_packet_loss_pct"] = 1.234
    log_results(data)
    all_output = " ".join([str(call.args[0]) for call in mock_print.call_args_list])
    assert "123.46 ms" in all_output
    assert "7.89 ms" in all_output
    assert "1.23 %" in all_output


@pytest.mark.parametrize(
    "test_data, expected_jitter_csv, expected_jitter_console",
    [
        (MOCK_DATA_COMPLETE, ",0.531,", "0.531"),  # Happy path
        (MOCK_DATA_MISSING_GW_JITTER, ",N/A,", "N/A"),  # Failure case
    ],
)
@patch("builtins.open", new_callable=mock_open)
@patch("main.os.path.exists", return_value=False)
@patch("builtins.print")
def test_log_results_handles_gateway_jitter(
    mock_print,
    mock_exists,
    mock_open_file,
    test_data: ResultRow,
    expected_jitter_csv: str,
    expected_jitter_console: str,
) -> None:
    """
    Tests that gateway ping jitter is logged correctly, handling both
    successful results and missing data ('N/A').
    """
    log_results(test_data)
    handle = mock_open_file()

    # 1. Check that the CSV Header is always correct
    written_header = handle.mock_calls[1][1][0]
    assert "Local_GW_Ping_StdDev" in written_header

    # 2. Check that the CSV Data Row contains the expected value ('0.531' or 'N/A')
    written_data_row = handle.mock_calls[2][1][0]
    assert expected_jitter_csv in written_data_row

    # 3. Check that the Console Output contains the expected value
    all_output = " ".join([str(call.args[0]) for call in mock_print.call_args_list if call.args])
    assert "Gateway Jitter (StdDev):" in all_output
    assert expected_jitter_console in all_output
