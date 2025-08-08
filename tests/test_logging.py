import importlib
import os
import sys
from unittest.mock import mock_open, patch

# Ensure the main module can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import config
from main import Colors, log_results

# --- Test Data ---

MOCK_DATA = {
    "gateway_loss_percentage": 1.5,
    "gateway_rtt_stats": "10/12/14",
    "downstream_speed": "40.0",
    "upstream_speed": "5.0",
    "local_wan_loss_percentage": 0.0,
    "local_wan_rtt_stats": "18/20/22",
    "local_wan_ping_stddev": 5.0,
    "local_gw_loss_percentage": 0.0,
    "local_gw_rtt_stats": "1/1/2",
    "local_downstream_speed": "450.0",
    "local_upstream_speed": "25.0",
    # Bufferbloat data
    "local_idle_latency_ms": "5.123",
    "local_speedtest_jitter": "1.456",
    "local_down_latency_ms": "25.789",
    "local_up_latency_ms": "35.987",
    "local_packet_loss_pct": "0.10%",
    # Wi-Fi data
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

    # This header must exactly match the keys in the log_results function
    header = ("Timestamp,Gateway_LossPercentage,Gateway_RTT_ms,Gateway_Downstream_Mbps,"
              "Gateway_Upstream_Mbps,Local_WAN_LossPercentage,Local_WAN_RTT_ms,"
              "Local_WAN_Ping_StdDev,Local_GW_LossPercentage,Local_GW_RTT_ms,"
              "Local_GW_Ping_StdDev,Local_Downstream_Mbps,Local_Upstream_Mbps,"
              "Local_Idle_Latency_ms,Local_Speedtest_Jitter_ms,Local_Down_Latency_ms,"
              "Local_Up_Latency_ms,Local_Packet_Loss_pct,WiFi_BSSID,WiFi_Channel,"
              "WiFi_RSSI,WiFi_Noise,WiFi_TxRate_Mbps\n")

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
    handle.write.assert_called_once()
    written_string = handle.write.call_args[0][0]
    assert "Timestamp" not in written_string
    # Check for a non-formatted value, as the new logger just uses str()
    assert str(MOCK_DATA["gateway_loss_percentage"]) in written_string


@patch("builtins.print")
def test_log_results_console_output_conditional_bufferbloat(mock_print):
    """
    Tests that the bufferbloat section is only printed to the console when
    the relevant data is available in the input dictionary.
    """
    # Case 1: Data IS available, so the section should be printed
    log_results(MOCK_DATA)
    all_output_with_data = " ".join([str(call.args[0]) for call in mock_print.call_args_list])
    assert "--- Latency & Bufferbloat (Speedtest) ---" in all_output_with_data
    assert "Idle Latency:" in all_output_with_data
    assert MOCK_DATA["local_idle_latency_ms"] in all_output_with_data
    assert MOCK_DATA["local_packet_loss_pct"] in all_output_with_data

    # Reset mock for the next call
    mock_print.reset_mock()

    # Case 2: Data is NOT available, so the section should be skipped
    mock_data_missing_key = MOCK_DATA.copy()
    # The conditional check is specifically on "local_idle_latency_ms" being "N/A"
    # The .get() in the function will cause this if the key is missing.
    del mock_data_missing_key["local_idle_latency_ms"]

    log_results(mock_data_missing_key)
    all_output_without_data = " ".join([str(call.args[0]) for call in mock_print.call_args_list])
    assert "--- Latency & Bufferbloat (Speedtest) ---" not in all_output_without_data
    assert "Idle Latency:" not in all_output_without_data
