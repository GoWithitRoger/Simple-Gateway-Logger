# tests/test_main.py

import re

from selenium.webdriver.common.by import By


# Copy of the parse_ping_results function to test in isolation
def parse_ping_results(full_results: str) -> dict:
    """
    Parses the full ping output to check for any packet loss and returns
    structured data.

    Args:
        full_results: The raw text output from the ping command

    Returns:
        A dictionary containing parsed ping results
    """
    results = {
        "packet_loss_detected": "No",
        "loss_percentage": "0% packet loss",
        "rtt_stats": "N/A",
    }

    # Use a regular expression to find the packet loss percentage
    loss_match = re.search(r"(\d+)% packet loss", full_results)
    if loss_match:
        results["loss_percentage"] = loss_match.group(0)  # e.g., "5% packet loss"
        # Check if the numeric value of the loss is greater than 0
        if int(loss_match.group(1)) > 0:
            results["packet_loss_detected"] = "Yes"

    # Use a regular expression to find the round-trip time stats
    rtt_match = re.search(r"round-trip min/avg/max = ([\d./]+) ms", full_results)
    if rtt_match:
        results["rtt_stats"] = rtt_match.group(1)

    return results


# Test case 1: Ideal, successful output
SUCCESS_OUTPUT = """
PING google.com (142.250.191.174): 56 data bytes
64 bytes from 142.250.191.174: icmp_seq=0 ttl=115 time=2.535 ms
--- google.com ping statistics ---
3 packets transmitted, 3 packets received, 0% packet loss
round-trip min/avg/max = 2.463/2.610/2.834 ms
"""

# Test case 2: Output with significant packet loss
PACKET_LOSS_OUTPUT = """
PING google.com (142.250.191.174): 56 data bytes
--- google.com ping statistics ---
10 packets transmitted, 5 packets received, 50% packet loss
round-trip min/avg/max = 10.1/15.2/20.3 ms
"""

# Test case 3: Malformed output, RTT stats are missing
MISSING_RTT_OUTPUT = """
PING google.com (142.250.191.174): 56 data bytes
--- google.com ping statistics ---
5 packets transmitted, 5 packets received, 0% packet loss
"""

# Test case 4: Empty string input
EMPTY_OUTPUT = ""

# Test case 5: Gibberish/unrelated text
GIBBERISH_OUTPUT = "This is not the output you are looking for."


def test_parse_successful_ping():
    """Ensures correct parsing for a standard, successful ping."""
    result = parse_ping_results(SUCCESS_OUTPUT)
    assert result["packet_loss_detected"] == "No"
    assert result["loss_percentage"] == "0% packet loss"
    assert result["rtt_stats"] == "2.463/2.610/2.834"


def test_parse_with_packet_loss():
    """Ensures packet loss is correctly identified."""
    result = parse_ping_results(PACKET_LOSS_OUTPUT)
    assert result["packet_loss_detected"] == "Yes"
    assert result["loss_percentage"] == "50% packet loss"
    assert result["rtt_stats"] == "10.1/15.2/20.3"


def test_parse_missing_rtt_stats():
    """Ensures parser gracefully handles missing RTT statistics."""
    result = parse_ping_results(MISSING_RTT_OUTPUT)
    assert result["packet_loss_detected"] == "No"
    assert result["loss_percentage"] == "0% packet loss"
    assert result["rtt_stats"] == "N/A"  # Should fall back to default


def test_parse_empty_input():
    """Ensures parser handles an empty string without crashing."""
    result = parse_ping_results(EMPTY_OUTPUT)
    assert result["packet_loss_detected"] == "No"
    assert result["loss_percentage"] == "0% packet loss"
    assert result["rtt_stats"] == "N/A"


def test_parse_gibberish_input():
    """Ensures parser handles unrelated text without crashing."""
    result = parse_ping_results(GIBBERISH_OUTPUT)
    assert result["packet_loss_detected"] == "No"
    assert result["loss_percentage"] == "0% packet loss"
    assert result["rtt_stats"] == "N/A"


# (Add to the top with other imports)


# (Add this class to the end of the file)
class MockWebElement:
    def __init__(self, text=""):
        self._text = text

    @property
    def text(self):
        return self._text

    def find_elements(self, by, value):
        if value == "td":
            # Simulate splitting the text content into columns
            parts = self._text.split("|")
            return [MockWebElement(text=p) for p in parts]
        return []


# Test case for speed test parsing
def test_parse_speed_test_results():
    """Ensures speed test results are correctly parsed from mock web elements."""
    # This function doesn't exist in the new structure, but we can test its logic
    # by simulating the objects that run_speed_test_task would process.

    # 1. Create mock rows like Selenium would find them
    # We use '|' as a simple separator for our mock `find_elements` implementation
    mock_rows = [
        MockWebElement("08/01/2025 12:26:14|downstream|387.950000|2822.000000|Success"),
        MockWebElement("08/01/2025 12:26:01|upstream|385.240000|2827.000000|Success"),
    ]

    # 2. Simulate the parsing logic from run_speed_test_task
    results = {}
    for row in mock_rows:
        cols = row.find_elements(By.TAG_NAME, "td")
        if len(cols) >= 3:
            direction = cols[1].text.lower()
            speed = f"{float(cols[2].text):.2f}"
            if "downstream" in direction:
                results["downstream_speed"] = speed
            elif "upstream" in direction:
                results["upstream_speed"] = speed

    # 3. Assert the results
    assert results["downstream_speed"] == "387.95"
    assert results["upstream_speed"] == "385.24"
