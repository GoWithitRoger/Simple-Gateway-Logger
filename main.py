# /// script
# dependencies = [
#   "schedule>=1.2.2,<2.0.0",
#   "selenium>=4.18.0,<5.0.0",
#   "webdriver-manager>=4.0.2"
# ]
# ///

# main.py

import os
import re
import time
from datetime import datetime

import schedule
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

# --- Configuration ---
GATEWAY_URL: str = "http://192.168.1.254"
DIAG_URL: str = "http://192.168.1.254/cgi-bin/diag.ha"
PING_TARGET: str = "google.com"
LOG_FILE: str = "ping_log.csv"
RUN_INTERVAL_MINUTES: int = 5
HEADLESS_MODE: bool = True


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
        "loss_percentage": "0%",
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


def log_results(ping_data: dict) -> None:
    """
    Logs the parsed ping results to a CSV file.

    Args:
        ping_data: A dictionary containing parsed ping results
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Create the condensed log entry
    log_entry = (
        f"{timestamp},{ping_data['packet_loss_detected']},"
        f"{ping_data['loss_percentage']},{ping_data['rtt_stats']}\n"
    )

    # Create the log file with a header if it doesn't exist
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w") as f:
            f.write(
                "Timestamp,PacketLossDetected,LossPercentage,RTT (min/avg/max ms)\n"
            )

    # Append the new entry to the log file
    with open(LOG_FILE, "a") as f:
        f.write(log_entry)

    # Get the full, absolute path for the user
    full_path = os.path.abspath(LOG_FILE)
    print(f"Ping analysis complete. Results appended to: {full_path}")


# --- Main Automation Function ---
def run_gateway_ping_test() -> None:
    """
    Automates navigating to the AT&T gateway's diagnostics page,
    running a ping test, and logging the results.
    """
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting ping test...")

    chrome_options = Options()
    if HEADLESS_MODE:
        chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1280,1024")
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
    )
    chrome_options.add_argument(f"user-agent={user_agent}")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = None
    try:
        print("Setting up WebDriver...")
        driver = webdriver.Chrome(
            service=ChromeService(ChromeDriverManager().install()),
            options=chrome_options,
        )
        print("WebDriver setup complete.")

        print(f"Performing initial visit to {GATEWAY_URL} to establish session...")
        driver.get(GATEWAY_URL)
        time.sleep(2)

        print(f"Navigating directly to diagnostics page: {DIAG_URL}...")
        driver.get(DIAG_URL)

        print("Waiting for page elements to be ready...")
        target_input = WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.ID, "webaddress"))
        )
        driver.execute_script(f"arguments[0].value = '{PING_TARGET}';", target_input)

        ping_button = driver.find_element(By.NAME, "Ping")
        driver.execute_script("arguments[0].click();", ping_button)
        print(f"Ping test started for {PING_TARGET}.")

        print("Waiting for results to populate...")
        time.sleep(15)

        results_element = driver.find_element(By.ID, "progress")
        results_text_value = results_element.get_attribute("value")
        results_text: str = results_text_value.strip() if results_text_value else ""

        if not results_text:
            print("Warning: Results text is empty. The test might not have completed.")
        else:
            print("Ping test complete. Full results captured.")
            # Use the new, refactored functions
            parsed_data = parse_ping_results(results_text)
            log_results(parsed_data)

    except Exception as e:
        print(f"An error occurred during the automation process: {e}")
        if driver:
            # Create a unique screenshot name to avoid overwriting
            error_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_file = f"error_screenshot_{error_time}.png"
            driver.save_screenshot(screenshot_file)
            print(f"Saved screenshot to {screenshot_file} for debugging.")

    finally:
        if driver:
            print("Closing WebDriver.")
            driver.quit()


# --- Scheduler ---
if __name__ == "__main__":
    # Run the test once immediately on start
    run_gateway_ping_test()

    # Schedule the job to run at the specified interval
    schedule.every(RUN_INTERVAL_MINUTES).minutes.do(run_gateway_ping_test)

    # Inform the user about the next scheduled run
    if schedule.jobs:
        next_run_datetime = schedule.jobs[0].next_run
        next_run_time = next_run_datetime.strftime("%Y-%m-%d %H:%M:%S")
        print(f"\nInitial test complete. Next test is scheduled for: {next_run_time}")
    else:
        # This case should not happen with the current logic, but it's good practice
        print("\nInitial test complete. No further tests are scheduled.")

    print("Press Ctrl+C to exit.")

    while True:
        schedule.run_pending()
        time.sleep(1)
