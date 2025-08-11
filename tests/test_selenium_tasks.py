import os
import sys
from unittest.mock import MagicMock, mock_open, patch

import pytest
from selenium.common.exceptions import TimeoutException

# Ensure the main module can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import run_ping_test_task, run_speed_test_task

# --- Fixtures ---


@pytest.fixture
def mock_driver():
    """Provides a mock Selenium WebDriver object."""
    driver = MagicMock()
    # Mock methods that are chained
    driver.find_element.return_value = MagicMock()
    driver.find_elements.return_value = [MagicMock(), MagicMock()]
    return driver


# --- Tests for run_ping_test_task ---


@patch("builtins.open", new_callable=mock_open)
@patch("main.time.sleep")
@patch("main.WebDriverWait")
def test_ping_task_success(mock_wait, mock_sleep, mock_open_file, mock_driver):
    """Tests the happy path for the gateway ping test."""
    mock_target_input = MagicMock()
    mock_ping_button = MagicMock()
    mock_progress_element = MagicMock()
    mock_progress_element.get_attribute.return_value = (
        "--- google.com ping statistics ---\n"
        "3 packets transmitted, 3 packets received, 0% packet loss\n"
        "round-trip min/avg/max = 14.8/15.2/15.5 ms"
    )

    # Configure the side effects for find_element
    mock_driver.find_element.side_effect = [
        mock_ping_button,
        mock_progress_element,
    ]
    # WebDriverWait(...).until(...) should first return the input, then the progress element,
    # then True for the lambda condition that checks for "ping statistics".
    mock_wait.return_value.until.side_effect = [
        mock_target_input,  # visibility_of_element_located for input
        mock_progress_element,  # presence_of_element_located for progress
        True,  # lambda condition satisfied
    ]

    results = run_ping_test_task(mock_driver)

    mock_driver.get.assert_called_with("http://192.168.1.254/cgi-bin/diag.ha")
    mock_driver.execute_script.assert_any_call("arguments[0].click();", mock_ping_button)
    assert results is not None
    assert results["gateway_loss_percentage"] == 0.0
    assert results["gateway_rtt_avg_ms"] == 15.2


@patch("main.time.sleep")
@patch("main.WebDriverWait")
def test_ping_task_timeout_exception(mock_wait, mock_sleep, mock_driver):
    """Tests that the function returns None when a timeout occurs."""
    mock_wait.return_value.until.side_effect = TimeoutException("Element not found")
    results = run_ping_test_task(mock_driver)
    assert results is None


@patch("builtins.open", new_callable=mock_open)
@patch("main.time.sleep")
@patch("main.WebDriverWait")
def test_ping_task_empty_results(mock_wait, mock_sleep, mock_open_file, mock_driver):
    """Tests that the function returns None if the result text is empty."""
    mock_progress_element = MagicMock()
    mock_progress_element.get_attribute.return_value = ""
    # find_element used to click Ping and later to access progress in the lambda
    mock_driver.find_element.return_value = mock_progress_element
    # First wait returns the target input, second returns the progress element, third True
    mock_wait.return_value.until.side_effect = [MagicMock(), mock_progress_element, True]

    results = run_ping_test_task(mock_driver)
    assert results is None


# --- Tests for run_speed_test_task ---


@patch("main.time.sleep")
@patch("main.WebDriverWait")
def test_speed_test_task_success(mock_wait, mock_sleep, mock_driver):
    """Tests the happy path for the gateway speed test, assuming already logged in."""
    # Mock the WebDriverWait to simulate no password field
    # Mock the table for result parsing
    mock_downstream_col = MagicMock()
    mock_downstream_col.text = "Downstream"
    mock_speed_col_down = MagicMock()
    mock_speed_col_down.text = "123.45"
    mock_row_down = MagicMock()
    mock_row_down.find_elements.return_value = [
        MagicMock(),
        mock_downstream_col,
        mock_speed_col_down,
    ]
    mock_upstream_col = MagicMock()
    mock_upstream_col.text = "Upstream"
    mock_speed_col_up = MagicMock()
    mock_speed_col_up.text = "67.89"
    mock_row_up = MagicMock()
    mock_row_up.find_elements.return_value = [MagicMock(), mock_upstream_col, mock_speed_col_up]
    mock_table = MagicMock()
    mock_table.find_elements.return_value = [mock_row_down, mock_row_up]

    # This mock will now handle the final table find, after the wait confirms visibility
    mock_driver.find_element.return_value = mock_table

    mock_wait.return_value.until.side_effect = [
        TimeoutException("No password field"),  # First wait for password fails
        MagicMock(),  # Second wait for run button succeeds
        True,  # Third wait for results table visibility (return value is ignored)
    ]

    results = run_speed_test_task(mock_driver, "test_code")

    mock_driver.get.assert_called_with("http://192.168.1.254/cgi-bin/speed.ha")
    assert results is not None
    assert results["downstream_speed"] == 123.45
    assert results["upstream_speed"] == 67.89


@patch("main.time.sleep")
@patch("main.WebDriverWait")
def test_speed_test_task_login_required(mock_wait, mock_sleep, mock_driver):
    """Tests that the function attempts to log in if the password field is found."""
    mock_password_input = MagicMock()
    mock_continue_button = MagicMock()
    mock_run_button = MagicMock()
    mock_results_table = MagicMock()
    mock_results_table.find_elements.return_value = []  # No results

    # Simulate the sequence of waits
    mock_wait.return_value.until.side_effect = [
        mock_password_input,  # First wait finds password field
        mock_run_button,  # Second wait finds run button (clickable)
        mock_results_table,  # Third wait for results table visibility
    ]
    mock_driver.find_element.return_value = mock_continue_button

    run_speed_test_task(mock_driver, "test_code")

    mock_password_input.send_keys.assert_called_with("test_code")
    mock_continue_button.click.assert_called_once()
    mock_run_button.click.assert_called_once()


@patch("main.time.sleep")
@patch("main.WebDriverWait")
def test_speed_test_task_timeout_exception(mock_wait, mock_sleep, mock_driver):
    """Tests that the function returns None when a timeout occurs finding the run button."""
    # First wait for password field times out
    mock_wait.return_value.until.side_effect = TimeoutException("No password field")
    # The find_element for the run button will also time out
    mock_driver.find_element.side_effect = TimeoutException("Button not found")

    results = run_speed_test_task(mock_driver, "test_code")
    assert results is None
