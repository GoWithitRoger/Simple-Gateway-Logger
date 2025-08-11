# tests/test_main.py

import os
import subprocess
import sys
from unittest.mock import MagicMock, patch

import pytest

# Ensure the main module can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import (
    parse_gateway_ping_results,
    parse_local_ping_results,
    run_local_speed_test_task,
    run_wifi_diagnostics_task,
)

# --- Test Data ---

# Test case for successful local ping with stddev
LOCAL_PING_SUCCESS_OUTPUT = """
PING google.com (142.250.191.174): 56 data bytes
64 bytes from 142.250.191.174: icmp_seq=0 ttl=115 time=2.535 ms
--- google.com ping statistics ---
3 packets transmitted, 3 packets received, 0.0% packet loss
round-trip min/avg/max/mdev = 2.463/2.610/2.834/0.123 ms
"""

# Test case for local ping with packet loss
LOCAL_PING_PACKET_LOSS_OUTPUT = """
PING example.com (93.184.216.34): 56 data bytes
Request timeout for icmp_seq 0
--- example.com ping statistics ---
2 packets transmitted, 1 packets received, 50.0% packet loss
round-trip min/avg/max/mdev = 12.345/12.345/12.345/0.000 ms
"""

# Test case for gateway ping (simpler format)
GATEWAY_PING_SUCCESS_OUTPUT = """
PING google.com (142.250.191.174): 56 data bytes
64 bytes from 142.250.191.174: icmp_seq=0 ttl=115 time=15.2 ms
--- google.com ping statistics ---
3 packets transmitted, 3 packets received, 0% packet loss
round-trip min/avg/max = 14.8/15.2/15.5 ms
"""

# Test case for malformed or incomplete ping output
MISSING_RTT_OUTPUT = """
PING google.com (142.250.191.174): 56 data bytes
--- google.com ping statistics ---
5 packets transmitted, 5 packets received, 0% packet loss
"""

# Mock JSON for Ookla Speedtest
SPEEDTEST_JSON_OUTPUT = (
    '{"type": "result", "timestamp": "2025-08-06T22:00:00Z", '
    '"ping": {"jitter": 2.789, "latency": 10.123}, '
    '"download": {"bandwidth": 37500000, "bytes": 300000000, "elapsed": 8000}, '
    '"upload": {"bandwidth": 2500000, "bytes": 20000000, "elapsed": 8000}}'
)  # 300 Mbps down, 20 Mbps up

# Mock data for Wi-Fi diagnostics
WIFI_DIAG_OUTPUT = "RSSI: -55\nNoise: -90\nTxRate: 866\nChannel: 149,80"
ARP_OUTPUT = "? (192.168.1.1) at a1:b2:c3:d4:e5:f6 on en0 ifscope [ethernet]"


# --- Tests for Ping Parsers ---


def test_parse_local_ping_success():
    """Ensures local ping parser correctly extracts metrics as floats."""
    result = parse_local_ping_results(LOCAL_PING_SUCCESS_OUTPUT)
    assert result.get("loss_percentage") == 0.0
    assert result.get("rtt_avg_ms") == 2.610
    assert result.get("ping_stddev") == 0.123


def test_parse_local_ping_with_loss():
    """Ensures local ping parser handles non-zero packet loss."""
    result = parse_local_ping_results(LOCAL_PING_PACKET_LOSS_OUTPUT)
    assert result.get("loss_percentage") == 50.0
    assert result.get("rtt_avg_ms") == 12.345


def test_parse_local_ping_missing_rtt():
    """Ensures local ping parser returns an empty dict for missing RTT."""
    result = parse_local_ping_results(MISSING_RTT_OUTPUT)
    assert "rtt_avg_ms" not in result
    assert "ping_stddev" not in result


def test_parse_gateway_ping_success():
    """Ensures gateway ping parser correctly extracts metrics as floats."""
    result = parse_gateway_ping_results(GATEWAY_PING_SUCCESS_OUTPUT)
    assert result.get("gateway_loss_percentage") == 0.0
    assert result.get("gateway_rtt_avg_ms") == 15.2


def test_parse_gateway_ping_missing_rtt():
    """Ensures gateway ping parser returns an empty dict for missing RTT."""
    result = parse_gateway_ping_results(MISSING_RTT_OUTPUT)
    assert "gateway_rtt_avg_ms" not in result


def test_parse_local_ping_empty_input():
    """Ensures the local ping parser handles empty string input gracefully."""
    result = parse_local_ping_results("")
    assert result == {}


def test_parse_local_ping_garbage_input():
    """Ensures the local ping parser handles random non-matching text."""
    result = parse_local_ping_results("this is not valid ping output")
    assert result == {}


def test_parse_gateway_ping_empty_input():
    """Ensures the gateway ping parser handles empty string input gracefully."""
    result = parse_gateway_ping_results("")
    assert result == {}


def test_parse_gateway_ping_garbage_input():
    """Ensures the gateway ping parser handles random non-matching text."""
    result = parse_gateway_ping_results("some random text, not ping results")
    assert result == {}


# --- Tests for Task Functions ---


@patch("main.os.path.exists", return_value=True)
@patch("main.subprocess.run")
def test_local_speed_test_parsing(mock_run, mock_exists):
    """Ensures the local speed test task correctly parses JSON and returns floats."""
    mock_run.return_value = MagicMock(stdout=SPEEDTEST_JSON_OUTPUT, returncode=0, stderr="")
    results = run_local_speed_test_task()
    assert results is not None
    # Bandwidth is in bytes, so we convert to Mbps (bytes * 8 / 1,000,000)
    assert results.get("local_downstream_speed") == 300.0
    assert results.get("local_upstream_speed") == 20.0
    assert results.get("local_speedtest_jitter") == 2.789


@patch("main.subprocess.run")
def test_wifi_diagnostics_success(mock_run):
    """Tests successful parsing of wdutil and arp output."""
    # Mock the sequence of subprocess calls
    route_output = "gateway: 192.168.1.1"
    mock_run.side_effect = [
        MagicMock(stdout=WIFI_DIAG_OUTPUT, returncode=0, stderr=""),  # For wdutil
        MagicMock(stdout=route_output, returncode=0, stderr=""),  # For route
        MagicMock(stdout="", returncode=0, stderr=""),  # For ping
        MagicMock(stdout=ARP_OUTPUT, returncode=0, stderr=""),  # For arp
    ]
    results = run_wifi_diagnostics_task()
    assert results["wifi_rssi"] == "-55"
    assert results["wifi_noise"] == "-90"
    assert results["wifi_bssid"] == "a1:b2:c3:d4:e5:f6"
    assert results["wifi_tx_rate"] == "866"
    assert results["wifi_channel"] == "149,80"


@patch("main.subprocess.run")
def test_wifi_diagnostics_failure(mock_run):
    """Tests graceful failure when diagnostic commands fail."""
    mock_run.side_effect = subprocess.CalledProcessError(1, "cmd", stderr="Error")
    results = run_wifi_diagnostics_task()
    # Should return a dictionary with 'N/A' values, not crash
    assert results["wifi_rssi"] == "N/A"
    assert results["wifi_noise"] == "N/A"
    assert results["wifi_bssid"] == "N/A"


@patch("main.subprocess.run")
@pytest.mark.parametrize(
    "tx_key",
    [
        "Tx Rate",
        "TxRate",
        "Last Tx Rate",
        "Max PHY Rate",
    ],
)
def test_wifi_diagnostics_tx_rate_variants(mock_run, tx_key):
    """Ensure tx rate is parsed correctly across multiple wdutil key variants."""
    # Build wdutil output with the variant key
    wd_output = f"RSSI: -55\nNoise: -90\n{tx_key}: 866\nChannel: 149,80"
    route_output = "gateway: 192.168.1.1"
    arp_output = "? (192.168.1.1) at a1:b2:c3:d4:e5:f6 on en0 ifscope [ethernet]"
    mock_run.side_effect = [
        MagicMock(stdout=wd_output, returncode=0, stderr=""),  # wdutil
        MagicMock(stdout=route_output, returncode=0, stderr=""),  # route
        MagicMock(stdout="", returncode=0, stderr=""),  # ping
        MagicMock(stdout=arp_output, returncode=0, stderr=""),  # arp
    ]
    results = run_wifi_diagnostics_task()
    assert results["wifi_tx_rate"] == "866"
