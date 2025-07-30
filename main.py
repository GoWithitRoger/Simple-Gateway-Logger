import re
import os
import time
import schedule
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC

# Automatically manages chromedriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

# --- Configuration with Type Hints ---
GATEWAY_URL: str = "http://192.168.1.254"
DIAG_URL: str = "http://192.168.1.254/cgi-bin/diag.ha"
PING_TARGET: str = "google.com"
LOG_FILE: str = "ping_log.csv"
RUN_INTERVAL_MINUTES: int = 5
HEADLESS_MODE: bool = True 

def parse_and_log_results(full_results: str) -> None:
    """
    Parses the full ping output to check for any packet loss and logs
    the findings in a CSV format.
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    packet_loss_detected = "No"
    loss_percentage = "0%"
    rtt_stats = "N/A"

    # Use a regular expression to find the packet loss percentage
    loss_match = re.search(r'(\d+)% packet loss', full_results)
    if loss_match:
        loss_percentage = loss_match.group(0) # e.g., "5% packet loss"
        # Check if the numeric value of the loss is greater than 0
        if int(loss_match.group(1)) > 0:
            packet_loss_detected = "Yes"

    # Use a regular expression to find the round-trip time stats
    rtt_match = re.search(r'round-trip min/avg/max = ([\d./]+) ms', full_results)
    if rtt_match:
        rtt_stats = rtt_match.group(1)

    # Create the condensed log entry
    log_entry = f"{timestamp},{packet_loss_detected},{loss_percentage},{rtt_stats}\n"

    # Create the log file with a header if it doesn't exist
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w") as f:
            f.write("Timestamp,PacketLossDetected,LossPercentage,RTT (min/avg/max ms)\n")
    
    # Append the new condensed entry
    with open(LOG_FILE, "a") as f:
        f.write(log_entry)
    
    print(f"Ping analysis complete. Results appended to {LOG_FILE}.")


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
    user_agent: str = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
    chrome_options.add_argument(f'user-agent={user_agent}')
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = None
    try:
        print("Setting up WebDriver...")
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
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

        # **FIX**: Reverted to clicking the "Ping" button
        ping_button = driver.find_element(By.NAME, "Ping")
        driver.execute_script("arguments[0].click();", ping_button)
        print(f"Ping test started for {PING_TARGET}.")

        print("Waiting for results to populate...")
        time.sleep(15)
        
        results_element = driver.find_element(By.ID, "progress")
        results_text: str = results_element.get_attribute('value').strip()
        
        if not results_text:
             print("Warning: Results text is empty. The test might not have completed.")
        else:
            print("Ping test complete. Full results captured.")
            parse_and_log_results(results_text)

    except Exception as e:
        print(f"An error occurred during the automation process: {e}")
        if driver:
            driver.save_screenshot("error_screenshot.png")
            print("Saved screenshot to error_screenshot.png for debugging.")

    finally:
        if driver:
            print("Closing WebDriver.")
            driver.quit()

# --- Scheduler ---
if __name__ == "__main__":
    run_gateway_ping_test()
    schedule.every(RUN_INTERVAL_MINUTES).minutes.do(run_gateway_ping_test)
    print(f"Script scheduled to run every {RUN_INTERVAL_MINUTES} minutes. Press Ctrl+C to exit.")

    while True:
        schedule.run_pending()
        time.sleep(1)
