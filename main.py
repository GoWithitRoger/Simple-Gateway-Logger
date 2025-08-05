# /// script
# dependencies = [
#   "schedule>=1.2.2,<2.0.0",
#   "selenium>=4.18.0,<5.0.0",
#   "webdriver-manager>=4.0.2",
#   "python-dotenv>=1.0.1"
# ]
# ///

# main.py

# Standard library imports
import getpass
import os
import re
import time
from datetime import datetime

# Third-party imports
import schedule
from dotenv import load_dotenv
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

# Load environment variables
load_dotenv()

# --- Configuration ---
GATEWAY_URL: str = "http://192.168.1.254"
DIAG_URL: str = "http://192.168.1.254/cgi-bin/diag.ha"
PING_TARGET: str = "google.com"
LOG_FILE: str = "ping_log.csv"
RUN_INTERVAL_MINUTES: int = 5
HEADLESS_MODE: bool = True

# --- Speed Test Configuration ---
SPEED_TEST_URL: str = "http://192.168.1.254/cgi-bin/speed.ha"
# Run speed test every N runs. Set to 2 for every other run. Set to 0 to disable.
RUN_SPEED_TEST_INTERVAL: int = 1

# --- Globals for state management ---
run_counter: int = 0
# The script will prompt for the code if this isn't set as an environment variable
DEVICE_ACCESS_CODE: str = ""


def get_access_code() -> str:
    """
    Gets the device access code from an environment variable or prompts the user.
    If prompted, it saves the code to a .env file for future use.
    """
    code = os.environ.get("GATEWAY_ACCESS_CODE")
    if code:
        print("Device Access Code found in environment variable.")
        return code

    print("\n--- Device Access Code Required ---")
    print("The Device Access Code was not found in your environment variables.")
    print(
        "To avoid this prompt, create a file named '.env' in the project root and add:"
    )
    print("GATEWAY_ACCESS_CODE='your_code_here'")
    print("(The .env file is ignored by Git and will not be stored in the repository)")

    # Use getpass for secure, non-echoed input
    entered_code = getpass.getpass("Please enter the Device Access Code: ")

    # If the user entered a code, save it to a .env file for them
    if entered_code and not os.path.exists(".env"):
        try:
            with open(".env", "w") as f:
                f.write(f"GATEWAY_ACCESS_CODE='{entered_code}'\n")
            print("✅ Saved Device Access Code to a new .env file for future runs.")
        except IOError as e:
            print(f"⚠️ Warning: Could not write to .env file: {e}")

    return entered_code


def parse_ping_results(full_results: str) -> dict:
    """
    Parses the full ping output to check for any packet loss and returns
    structured data.
    """
    results = {
        "packet_loss_detected": "No",
        "loss_percentage": "0%",
        "rtt_stats": "N/A",
    }
    loss_match = re.search(r"(\d+)% packet loss", full_results)
    if loss_match:
        results["loss_percentage"] = loss_match.group(0)
        if int(loss_match.group(1)) > 0:
            results["packet_loss_detected"] = "Yes"

    rtt_match = re.search(r"round-trip min/avg/max = ([\d./]+) ms", full_results)
    if rtt_match:
        results["rtt_stats"] = rtt_match.group(1)

    return results


def log_results(ping_data: dict, speed_data: dict | None = None) -> None:
    """
    Logs parsed ping and speed test results to a CSV file and prints a summary.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Get speed data, defaulting to "N/A" if not provided
    downstream = speed_data.get("downstream_speed", "N/A") if speed_data else "N/A"
    upstream = speed_data.get("upstream_speed", "N/A") if speed_data else "N/A"

    log_entry = (
        f"{timestamp},{ping_data['packet_loss_detected']},"
        f"{ping_data['loss_percentage']},{ping_data['rtt_stats']},"
        f"{downstream},{upstream}\n"
    )

    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w") as f:
            f.write(
                "Timestamp,PacketLossDetected,LossPercentage,RTT (min/avg/max ms),"
                "DownstreamSpeed (Mbps),UpstreamSpeed (Mbps)\n"
            )

    with open(LOG_FILE, "a") as f:
        f.write(log_entry)

    print("\n--- Test Results ---")
    print(f"  Packet Loss Detected: {ping_data['packet_loss_detected']}")
    print(f"  Loss Percentage:      {ping_data['loss_percentage']}")
    print(f"  RTT (min/avg/max):    {ping_data['rtt_stats']} ms")
    if speed_data:
        print(f"  Downstream Speed:     {downstream} Mbps")
        print(f"  Upstream Speed:       {upstream} Mbps")
    print("--------------------")

    full_path = os.path.abspath(LOG_FILE)
    print(f"Results appended to: {full_path}")


def run_ping_test_task(driver: WebDriver) -> dict | None:
    """
    Runs the ping test on the gateway's diagnostics page.
    """
    print("Navigating to diagnostics page for ping test...")
    driver.get(DIAG_URL)

    target_input = WebDriverWait(driver, 20).until(
        EC.visibility_of_element_located((By.ID, "webaddress"))
    )
    driver.execute_script(f"arguments[0].value = '{PING_TARGET}';", target_input)

    ping_button = driver.find_element(By.NAME, "Ping")
    driver.execute_script("arguments[0].click();", ping_button)
    print(f"Ping test started for {PING_TARGET}.")

    print("Waiting for ping results...")
    time.sleep(15)

    results_element = driver.find_element(By.ID, "progress")
    results_text = (results_element.get_attribute("value") or "").strip()

    if not results_text:
        print("Warning: Ping results text is empty.")
        return None

    return parse_ping_results(results_text)


def run_speed_test_task(driver: WebDriver, access_code: str) -> dict | None:
    """
    NEW: Automates the gateway speed test, including login if required.
    """
    print("Navigating to speed test page...")
    driver.get(SPEED_TEST_URL)

    # Check if login is required by looking for the password field
    try:
        password_input = WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.ID, "password"))
        )
        print("Device Access Code required. Attempting to log in...")
        password_input.send_keys(access_code)
        driver.find_element(By.NAME, "Continue").click()
        # FIX: Add a short, static pause to resolve the race condition
        # by allowing the page to fully stabilize after a login reload.
        time.sleep(2)
    except TimeoutException:
        # This path is taken when already logged in (or no password is required)
        # and does not have the same timing issue.
        print("Already logged in or no password required.")

    # Wait for the "Run Speed Test" button to be ready and click it
    run_button = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.NAME, "run"))
    )
    run_button.click()
    print("Speed test initiated. This will take up to 90 seconds...")

    # Wait for the test to complete by waiting for the run button to be clickable again
    WebDriverWait(driver, 90).until(EC.element_to_be_clickable((By.NAME, "run")))
    print("Speed test complete. Parsing results...")

    # Parse results from the table
    results = {}
    table = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, "table.grid.table100"))
    )
    rows = table.find_elements(By.TAG_NAME, "tr")

    # Iterate over all rows to find the latest downstream and upstream results
    for row in rows:
        cols = row.find_elements(By.TAG_NAME, "td")
        if len(cols) >= 3:
            direction = cols[1].text.lower()
            try:
                speed = f"{float(cols[2].text):.2f}"
                if "downstream" in direction and "downstream_speed" not in results:
                    results["downstream_speed"] = speed
                elif "upstream" in direction and "upstream_speed" not in results:
                    results["upstream_speed"] = speed
            except (ValueError, IndexError):
                # Ignore rows that don't parse correctly (like headers)
                continue
        # Stop once we have both results
        if "downstream_speed" in results and "upstream_speed" in results:
            break

    if "downstream_speed" not in results or "upstream_speed" not in results:
        print("Warning: Could not parse both downstream and upstream speeds.")
        return None

    return results


def perform_checks() -> None:
    """
    Main automation function to set up WebDriver, run tests, and log results.
    """
    global run_counter, DEVICE_ACCESS_CODE
    run_counter += 1

    print(
        f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
        f"Starting checks (Run #{run_counter})..."
    )

    # Get access code on first run if needed for a speed test
    should_run_speed_test = (
        RUN_SPEED_TEST_INTERVAL > 0 and run_counter % RUN_SPEED_TEST_INTERVAL == 0
    )
    if should_run_speed_test and not DEVICE_ACCESS_CODE:
        DEVICE_ACCESS_CODE = get_access_code()

    # --- Setup WebDriver ---
    chrome_options = Options()
    if HEADLESS_MODE:
        chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1280,1024")
    user_agent = (
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
        time.sleep(2)  # Allow time for any session cookies to be set

        # --- Run Ping Test ---
        ping_results = run_ping_test_task(driver)

        # --- Conditionally Run Speed Test ---
        speed_results = None
        if should_run_speed_test:
            speed_results = run_speed_test_task(driver, DEVICE_ACCESS_CODE)
        else:
            print("Skipping speed test for this interval.")

        # --- Log Results ---
        if ping_results:
            log_results(ping_results, speed_results)
        else:
            print("Could not log results as ping test failed.")

    except Exception as e:
        print(f"An error occurred during the automation process: {e}")
        if driver:
            error_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_file = f"error_screenshot_{error_time}.png"
            driver.save_screenshot(screenshot_file)
            print(f"Saved screenshot to {screenshot_file} for debugging.")
    finally:
        if driver:
            print("Closing WebDriver.")
            driver.quit()
        print("\n" + "=" * 60 + "\n")


# --- Scheduler ---
if __name__ == "__main__":
    perform_checks()
    schedule.every(RUN_INTERVAL_MINUTES).minutes.do(perform_checks)

    if schedule.jobs:
        next_run_datetime = schedule.jobs[0].next_run
        print(
            "Next test is scheduled for: "
            f"{next_run_datetime.strftime('%Y-%m-%d %H:%M:%S')}"
        )

    print("Press Ctrl+C to exit.")

    while True:
        schedule.run_pending()
        time.sleep(1)
