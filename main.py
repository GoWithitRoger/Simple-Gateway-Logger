# /// script
# dependencies = [
#   "schedule>=1.2.2,<2.0.0",
#   "selenium>=4.18.0,<5.0.0",
#   "python-dotenv>=1.0.1"
# ]
# ///
# main.py

# Standard library imports
import getpass
import json
import os
import re
import subprocess
import time
from datetime import datetime
from typing import Dict, Optional

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

# Local application imports
import config


# --- ANSI Color Codes ---
class Colors:
    """A class to hold ANSI color codes for terminal output."""

    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


# Load environment variables
load_dotenv()

# --- Globals for state management ---
run_counter: int = 0
DEVICE_ACCESS_CODE: str = ""


def get_access_code() -> str:
    """Gets the device access code from an environment variable or prompts the user."""
    code = os.environ.get("GATEWAY_ACCESS_CODE")
    if code:
        print("Device Access Code found in environment variable.")
        return code
    print("\n--- Device Access Code Required ---")
    entered_code = getpass.getpass("Please enter the Device Access Code: ")
    return entered_code


def parse_gateway_ping_results(full_results: str) -> dict[str, float]:
    """Parses the full ping output from the GATEWAY, returning numerical values."""
    results: dict[str, float] = {}
    loss_match = re.search(r"(\d+)% packet loss", full_results)
    if loss_match:
        results["gateway_loss_percentage"] = float(loss_match.group(1))

    rtt_match = re.search(r"round-trip min/avg/max = ([\d./]+) ms", full_results)
    if rtt_match:
        rtt_parts = rtt_match.group(1).split("/")
        if len(rtt_parts) >= 3:
            # Extract the 'avg' value
            results["gateway_rtt_avg_ms"] = float(rtt_parts[1])

    return results


def parse_local_ping_results(ping_output: str) -> dict[str, float]:
    """
    Parses local ping output, returning numerical values for key metrics.
    Focuses on packet loss percentage, average RTT, and standard deviation.
    """
    results: dict[str, float] = {}
    loss_match = re.search(r"(\d+(?:\.\d+)?)% packet loss", ping_output)
    if loss_match:
        results["loss_percentage"] = float(loss_match.group(1))

    rtt_match = re.search(
        r"min/avg/max/(?:stddev|mdev)\s*=\s*([\d./]+)\s*ms", ping_output
    )
    if rtt_match:
        parts = rtt_match.group(1).split("/")
        if len(parts) == 4:
            results["rtt_avg_ms"] = float(parts[1])
            results["ping_stddev"] = float(parts[3])

    return results


def log_results(all_data: dict[str, str | float | int | None]) -> None:
    """
    Logs results to a CSV file and prints a color-coded summary to the console
    based on configured anomaly thresholds.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data_points = {
        "Gateway_LossPercentage": all_data.get("gateway_loss_percentage"),
        "Gateway_RTT_avg_ms": all_data.get("gateway_rtt_avg_ms"),
        "Gateway_Downstream_Mbps": all_data.get("downstream_speed"),
        "Gateway_Upstream_Mbps": all_data.get("upstream_speed"),
        "Local_WAN_LossPercentage": all_data.get("local_wan_loss_percentage"),
        "Local_WAN_RTT_avg_ms": all_data.get("local_wan_rtt_avg_ms"),
        "Local_WAN_Ping_StdDev": all_data.get("local_wan_ping_stddev"),
        "Local_GW_LossPercentage": all_data.get("local_gw_loss_percentage"),
        "Local_GW_RTT_avg_ms": all_data.get("local_gw_rtt_avg_ms"),
        "Local_GW_Ping_StdDev": all_data.get("local_gw_ping_stddev"),
        "Local_Downstream_Mbps": all_data.get("local_downstream_speed"),
        "Local_Upstream_Mbps": all_data.get("local_upstream_speed"),
        "Local_Speedtest_Jitter_ms": all_data.get("local_speedtest_jitter"),
        "WiFi_BSSID": all_data.get("wifi_bssid", "N/A"),
        "WiFi_Channel": all_data.get("wifi_channel", "N/A"),
        "WiFi_RSSI": all_data.get("wifi_rssi", "N/A"),
        "WiFi_Noise": all_data.get("wifi_noise", "N/A"),
        "WiFi_TxRate_Mbps": all_data.get("wifi_tx_rate", "N/A"),
    }

    # --- CSV Logging ---
    csv_values = [
        f"{v:.3f}" if isinstance(v, float) else ("N/A" if v is None else v)
        for v in data_points.values()
    ]
    header = "Timestamp," + ",".join(data_points.keys()) + "\n"
    log_entry = timestamp + "," + ",".join(csv_values) + "\n"
    write_header = (
        not os.path.exists(config.LOG_FILE) or os.path.getsize(config.LOG_FILE) == 0
    )
    with open(config.LOG_FILE, "a") as f:
        if write_header:
            f.write(header)
        f.write(log_entry)

    # --- Console Output Formatting ---
    def format_value(
        value: Optional[float],
        unit: str,
        threshold: Optional[float],
        comparison: str = "greater",
        default_color: str = "",
        precision: int = 2,
    ) -> str:
        """Formats and colors a value based on a threshold."""
        if value is None:
            return f"{Colors.YELLOW}N/A{Colors.RESET}"

        is_anomaly = False
        if config.ENABLE_ANOMALY_HIGHLIGHTING and threshold is not None:
            if comparison == "greater" and value > threshold:
                is_anomaly = True
            elif comparison == "less" and value < threshold:
                is_anomaly = True

        color = Colors.RED if is_anomaly else default_color
        return (
            f"{color}{value:.{precision}f}{Colors.RESET} {unit}"
            if color
            else f"{value:.{precision}f} {unit}"
        )

    # --- Print to Console ---
    print("\n--- Gateway Test Results ---")
    loss_pct = format_value(
        data_points['Gateway_LossPercentage'], 
        '%', 
        config.PACKET_LOSS_THRESHOLD
    )
    print(f"  Packet Loss:                {loss_pct}")
    
    rtt_avg = format_value(
        data_points['Gateway_RTT_avg_ms'], 
        'ms', 
        config.PING_RTT_THRESHOLD
    )
    print(f"  WAN RTT (avg):              {rtt_avg}")
    
    down_speed = format_value(
        data_points['Gateway_Downstream_Mbps'], 
        'Mbps', 
        config.GATEWAY_DOWNSTREAM_SPEED_THRESHOLD, 
        'less'
    )
    print(f"  Downstream Speed:           {down_speed}")
    
    up_speed = format_value(
        data_points['Gateway_Upstream_Mbps'], 
        'Mbps', 
        config.GATEWAY_UPSTREAM_SPEED_THRESHOLD, 
        'less'
    )
    print(f"  Upstream Speed:             {up_speed}")

    print("\n--- Local Machine Test Results ---")
    wan_loss = format_value(
        data_points['Local_WAN_LossPercentage'], 
        '%', 
        config.PACKET_LOSS_THRESHOLD
    )
    print(f"  WAN Packet Loss:            {wan_loss}")
    
    wan_rtt = format_value(
        data_points['Local_WAN_RTT_avg_ms'], 
        'ms', 
        config.PING_RTT_THRESHOLD
    )
    print(f"  WAN RTT (avg):              {wan_rtt}")
    
    jitter = format_value(
        data_points['Local_WAN_Ping_StdDev'], 
        'ms', 
        config.JITTER_THRESHOLD, 
        precision=3
    )
    print(f"  Ping Jitter (StdDev):       {jitter}")
    
    gw_loss = format_value(
        data_points['Local_GW_LossPercentage'], 
        '%', 
        config.PACKET_LOSS_THRESHOLD
    )
    print(f"  Gateway Packet Loss:        {gw_loss}")
    
    # Special color for Local GW RTT
    gw_rtt = format_value(
        data_points['Local_GW_RTT_avg_ms'], 
        'ms', 
        config.PING_RTT_THRESHOLD, 
        default_color=Colors.CYAN
    )
    print(f"  Gateway RTT (avg):          {gw_rtt}")
    
    local_down = format_value(
        data_points['Local_Downstream_Mbps'], 
        'Mbps', 
        config.LOCAL_DOWNSTREAM_SPEED_THRESHOLD, 
        'less'
    )
    print(f"  Downstream Speed:           {local_down}")
    
    local_up = format_value(
        data_points['Local_Upstream_Mbps'], 
        'Mbps', 
        config.LOCAL_UPSTREAM_SPEED_THRESHOLD, 
        'less'
    )
    print(f"  Upstream Speed:             {local_up}")
    
    speed_jitter = format_value(
        data_points['Local_Speedtest_Jitter_ms'], 
        'ms', 
        config.JITTER_THRESHOLD, 
        precision=3
    )
    print(f"  Speedtest Jitter:           {speed_jitter}")

    print("\n--- Wi-Fi Diagnostics ---")
    print(f"  Connected AP (BSSID):       {data_points['WiFi_BSSID']}")
    print(f"  Signal Strength (RSSI):     {data_points['WiFi_RSSI']}")
    print(f"  Noise Level:                {data_points['WiFi_Noise']}")
    print(f"  Channel/Band:               {data_points['WiFi_Channel']}")
    print(f"  Transmit Rate:              {data_points['WiFi_TxRate_Mbps']} Mbps")
    print("------------------------------------")
    full_path = os.path.abspath(config.LOG_FILE)
    print(f"Results appended to: {full_path}")


def run_ping_test_task(driver: WebDriver) -> Optional[Dict[str, float]]:
    """Runs the ping test on the gateway's diagnostics page and logs raw output."""
    print("Navigating to gateway diagnostics page for ping test...")
    driver.get(config.DIAG_URL)
    try:
        target_input = WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.ID, "webaddress"))
        )
        driver.execute_script(
            f"arguments[0].value = '{config.PING_TARGET}';", target_input
        )
        ping_button = driver.find_element(By.NAME, "Ping")
        driver.execute_script("arguments[0].click();", ping_button)
        print(f"Gateway ping test started for {config.PING_TARGET}.")
        print("Waiting for gateway ping results...")
        time.sleep(15)
        results_element = driver.find_element(By.ID, "progress")
        results_text = (results_element.get_attribute("value") or "").strip()
        if results_text:
            with open("gateway_raw_output.log", "a") as log_file:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                log_file.write(f"--- Log entry from {timestamp} ---\n")
                log_file.write(results_text + "\n\n")
            print("Successfully retrieved and logged raw gateway ping results text.")
        else:
            print("Warning: Gateway ping results text is empty.")
            return None
        return parse_gateway_ping_results(results_text)
    except Exception as e:
        print(f"Error during gateway ping test: {e}")
        error_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_file = f"error_screenshot_gateway_ping_{error_time}.png"
        driver.save_screenshot(screenshot_file)
        print(f"Saved screenshot to {screenshot_file} for debugging.")
        return None


def run_speed_test_task(
    driver: WebDriver, access_code: str
) -> Optional[Dict[str, float]]:
    """
    Automates the gateway speed test, returning numerical values for speeds.
    """
    print("Navigating to gateway speed test page...")
    driver.get(config.SPEED_TEST_URL)
    try:
        try:
            password_input = WebDriverWait(driver, 5).until(
                EC.visibility_of_element_located((By.ID, "password"))
            )
            print("Device Access Code required. Attempting to log in...")
            password_input.send_keys(access_code)
            driver.find_element(By.NAME, "Continue").click()
            time.sleep(2)
        except TimeoutException:
            print("Already logged in or no password required for gateway speed test.")

        run_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.NAME, "run"))
        )
        run_button.click()
        print("Gateway speed test initiated. This will take up to 90 seconds...")
        WebDriverWait(driver, 90).until(EC.element_to_be_clickable((By.NAME, "run")))
        print("Gateway speed test complete. Parsing results...")

        results: Dict[str, float] = {}
        table = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "table.grid.table100"))
        )
        rows = table.find_elements(By.TAG_NAME, "tr")
        for row in rows:
            cols = row.find_elements(By.TAG_NAME, "td")
            if len(cols) >= 3:
                direction = cols[1].text.lower()
                try:
                    speed = float(cols[2].text)
                    if "downstream" in direction and "downstream_speed" not in results:
                        results["downstream_speed"] = speed
                    elif "upstream" in direction and "upstream_speed" not in results:
                        results["upstream_speed"] = speed
                except (ValueError, IndexError):
                    continue
            if "downstream_speed" in results and "upstream_speed" in results:
                break
        return results if results else None
    except Exception as e:
        print(f"Error during gateway speed test: {e}")
        return None


def run_local_ping_task(target: str) -> Dict[str, float]:
    """Runs a ping test from the local OS to the specified target."""
    print(f"Running local ping test to {target}...")
    try:
        command = ["ping", "-c", "4", target]
        process = subprocess.run(command, capture_output=True, text=True, timeout=15)
        if process.returncode == 0:
            print(f"Local ping to {target} complete.")
            return parse_local_ping_results(process.stdout)
        else:
            print(
                f"Warning: Local ping test to {target} failed. Stderr: {process.stderr}"
            )
            return {}
    except FileNotFoundError:
        print(
            "Error: 'ping' command not found. Please ensure it's in your system's PATH."
        )
        return {}
    except Exception as e:
        print(f"An error occurred during local ping test to {target}: {e}")
        return {}


def run_local_speed_test_task() -> Optional[Dict[str, float]]:
    """
    Runs a local speed test, returning numerical values for key metrics.
    """
    print("Running local speed test using the official Ookla CLI...")

    ookla_path = None
    possible_paths = ["/opt/homebrew/bin/speedtest", "/usr/local/bin/speedtest"]
    for path in possible_paths:
        if os.path.exists(path):
            ookla_path = path
            break

    if not ookla_path:
        print("\n---")
        print("Error: Could not find the Ookla 'speedtest' executable.")
        print(
            "Please ensure it is installed via Homebrew and located in one of these paths:"
        )
        print(f"  {', '.join(possible_paths)}")
        print("Installation command: brew install speedtest")
        print("---\n")
        return None

    try:
        command = [ookla_path, "--accept-license", "--accept-gdpr", "--format=json"]
        process = subprocess.run(
            command, capture_output=True, text=True, timeout=120, check=True
        )

        json_output = None
        for line in process.stdout.splitlines():
            if line.strip().startswith("{"):
                json_output = line
                break

        if not json_output:
            print("Error: Could not find JSON in the speedtest command output.")
            print(f"--- Raw STDOUT ---\n{process.stdout}\n--------------------")
            if process.stderr:
                print(f"--- Raw STDERR ---\n{process.stderr}\n--------------------")
            return None

        results = json.loads(json_output)

        download_speed = (
            results.get("download", {}).get("bandwidth", 0) * 8
        ) / 1_000_000
        upload_speed = (results.get("upload", {}).get("bandwidth", 0) * 8) / 1_000_000
        jitter = results.get("ping", {}).get("jitter", 0.0)

        print("Local speed test complete.")

        return {
            "local_downstream_speed": download_speed,
            "local_upstream_speed": upload_speed,
            "local_speedtest_jitter": jitter,
        }

    except subprocess.CalledProcessError as e:
        print(f"Error: The 'speedtest' command failed with return code {e.returncode}.")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        return None
    except subprocess.TimeoutExpired:
        print("Error: The speed test command timed out after 120 seconds.")
        return None
    except json.JSONDecodeError:
        print("Error: Could not parse JSON output from the 'speedtest' command.")
        if "process" in locals():
            print(f"--- Raw STDOUT ---\n{process.stdout}\n--------------------")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during the local speed test: {e}")
        return None


def run_wifi_diagnostics_task() -> dict[str, str]:
    """
    Uses a hybrid approach: wdutil for live Wi-Fi stats (signal, etc.) and
    arp for a reliable BSSID (via the default gateway's MAC address).

    Returns:
        A dictionary of Wi-Fi metrics.
    """
    print("Running local Wi-Fi diagnostics...")
    results: dict[str, str] = {}

    # --- Part 1: Get Signal, Noise, etc. from wdutil ---
    try:
        # This command requires the sudoers file to be configured for NOPASSWD.
        command = ["sudo", "wdutil", "info"]
        process = subprocess.run(
            command, capture_output=True, text=True, timeout=10, check=True
        )
        output = process.stdout

        def find_value(key: str, text: str) -> str:
            """Helper to find values in the wdutil output using regex."""
            match = re.search(rf"^\s*{key}\s*:\s*(.*)$", text, re.MULTILINE)
            return match.group(1).strip() if match else "N/A"

        results["wifi_rssi"] = find_value("RSSI", output)
        results["wifi_noise"] = find_value("Noise", output)
        results["wifi_tx_rate"] = find_value("TxRate", output)
        results["wifi_channel"] = find_value("Channel", output)

    except Exception as e:
        print(f"Warning: Could not parse wdutil output. Error: {e}")

    # --- Part 2: Programmatically find Gateway IP and get its MAC Address (BSSID) ---
    try:
        route_command = ["route", "-n", "get", "default"]
        route_process = subprocess.run(
            route_command, capture_output=True, text=True, timeout=10, check=True
        )
        gateway_match = re.search(
            r"^\s*gateway:\s*(\S+)", route_process.stdout, re.MULTILINE
        )

        if not gateway_match:
            raise Exception("Could not determine default gateway IP.")

        gateway_ip = gateway_match.group(1)
        ping_command = ["ping", "-c", "1", gateway_ip]
        subprocess.run(ping_command, capture_output=True, text=True, timeout=10)
        arp_command = ["arp", "-n", gateway_ip]
        arp_process = subprocess.run(
            arp_command, capture_output=True, text=True, timeout=10, check=True
        )
        arp_match = re.search(r"at\s+([0-9a-fA-F:]+)", arp_process.stdout)

        if arp_match:
            results["wifi_bssid"] = arp_match.group(1)

    except Exception as e:
        print(f"Warning: Could not get BSSID from ARP table. Error: {e}")

    # Fill any missing keys with "N/A" to ensure consistent dictionary structure
    for key in [
        "wifi_rssi",
        "wifi_noise",
        "wifi_tx_rate",
        "wifi_channel",
        "wifi_bssid",
    ]:
        if key not in results:
            results[key] = "N/A"

    print("Local Wi-Fi diagnostics complete.")
    return results


def perform_checks() -> None:
    """Main automation function to run all configured tests and log results."""
    global run_counter, DEVICE_ACCESS_CODE
    run_counter += 1
    master_results = {}
    print(
        f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
        f"Starting checks (Run #{run_counter})..."
    )

    # --- Run Local Tests (No Browser Required) ---
    wifi_results = run_wifi_diagnostics_task()
    if wifi_results:
        master_results.update(wifi_results)

    if config.RUN_LOCAL_PING_TEST:
        wan_ping_results = run_local_ping_task(config.PING_TARGET)
        master_results.update(
            {f"local_wan_{k}": v for k, v in wan_ping_results.items()}
        )
    if config.RUN_LOCAL_GATEWAY_PING_TEST:
        gateway_ip = config.GATEWAY_URL.split("//")[-1].split("/")[0]
        gw_ping_results = run_local_ping_task(gateway_ip)
        master_results.update({f"local_gw_{k}": v for k, v in gw_ping_results.items()})
    if config.RUN_LOCAL_SPEED_TEST:
        local_speed_results = run_local_speed_test_task()
        if local_speed_results:
            master_results.update(local_speed_results)

    # --- Run Gateway Tests (Selenium Required) ---
    should_run_gateway_speed_test = (
        config.RUN_GATEWAY_SPEED_TEST_INTERVAL > 0
        and run_counter % config.RUN_GATEWAY_SPEED_TEST_INTERVAL == 0
    )
    if should_run_gateway_speed_test and not DEVICE_ACCESS_CODE:
        DEVICE_ACCESS_CODE = get_access_code()

    chrome_options = Options()
    if config.HEADLESS_MODE:
        chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1280,1024")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = None
    service = ChromeService()  # Use Selenium Manager to handle the driver
    try:
        print("Setting up WebDriver for gateway tests...")
        driver = webdriver.Chrome(
            service=service,  # Use the predefined service object
            options=chrome_options,
        )
        driver.get(config.GATEWAY_URL)
        time.sleep(2)
        gateway_ping_results = run_ping_test_task(driver)
        if gateway_ping_results:
            master_results.update(gateway_ping_results)
        if should_run_gateway_speed_test:
            gateway_speed_results = run_speed_test_task(driver, DEVICE_ACCESS_CODE)
            if gateway_speed_results:
                master_results.update(gateway_speed_results)
    except Exception as e:
        print(f"An error occurred during the gateway automation process: {e}")
        if driver:
            error_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_file = f"error_screenshot_{error_time}.png"
            driver.save_screenshot(screenshot_file)
            print(f"Saved screenshot to {screenshot_file} for debugging.")
    finally:
        if driver:
            print("Closing WebDriver...")
            driver.quit()
        # NEW: Add a more aggressive cleanup to prevent zombie processes
        if service and service.process:
            print("Ensuring chromedriver service is terminated...")
            try:
                service.process.kill()
            except Exception as e:
                print(f"Error while trying to kill service process: {e}")

    log_results(master_results)
    print("\n" + "=" * 60 + "\n")


# --- Scheduler ---
if __name__ == "__main__":
    perform_checks()
    schedule.every(config.RUN_INTERVAL_MINUTES).minutes.do(perform_checks)
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
