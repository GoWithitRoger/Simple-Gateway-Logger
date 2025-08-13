<p align="left"> <img src="./icon.svg" alt="Simple Gateway Logger" width="150"> </p>

# Simple Gateway Logger

This script automates running diagnostic network tests from your AT&T fiber gateway and your local machine. It logs the results to a CSV file, helping identify and troubleshoot intermittent network issues.

By comparing gateway-to-WAN tests against local-machine-to-WAN tests, you can better distinguish between potential ISP issues and local network problems (e.g., Wi-Fi interference, router performance).

## Features

- Uses Selenium to automate interaction with the gateway's web interface.
- Runs gateway-based Ping tests to measure the quality of the direct ISP connection.
- Optionally runs a gateway-based Speed Test.
- Runs local Ping tests from the machine executing the script to both the gateway and the internet.
- Runs local Speed Tests using the **official Ookla Speedtest CLI** for accurate, reliable results.
- Measures **WAN Bufferbloat** (latency under load) to see how your internet connection handles congestion.
- Optionally measures **LAN Bufferbloat** to specifically test for latency issues on your local Wi-Fi or wired network, independent of your ISP.
- Runs in headless mode, so no browser window is required.
- Schedules tests to run at a configurable interval.
- Provides color-coded console output, highlighting anomalous results (e.g., high latency, packet loss) for at-a-glance diagnosis.
- Appends combined results to a single, local CSV log file.
- Captures detailed Wi-Fi metrics on macOS (signal, noise, channel, etc.).
- All configuration is organized in the `config.py` file.

## Prerequisites

- Designed to run on MacOS with Homebrew package manager installed.
- Before running the script, you must install the official Ookla Speedtest CLI.

### Installing Ookla Speedtest CLI on macOS (via Homebrew)

If you don't have Homebrew, [install it first](https://brew.sh/). Then, run the following command in your terminal:
    
    
        brew install speedtest
      
    

## Usage and Setup

Simply run the following command in a terminal window:
    
    
        uv run main.py
    ```uv` will automatically read the required dependencies from the top of the `main.py` file, create a temporary environment, and run the script.
    
    ## Configuration
    All configuration has been moved to the **`config.py`** file for easy editing.
    
    ### General Configuration
    
    - `PING_TARGET`: The IP address or hostname to ping (e.g., "google.com").
    - `LOG_FILE`: The name of the CSV file for storing results.
    - `RUN_INTERVAL_MINUTES`: How often the script should run.
    - `HEADLESS_MODE`: Set to `True` to run the browser invisibly in the background.
    - `ENABLE_DEBUG_LOGGING`: Set to `True` for verbose console output.
    
    ### Gateway Test Configuration
    
    - `GATEWAY_URL`: The address of the fiber gateway.
    - `DIAG_URL`: The address of the gateway's diagnostics page.
    - `SPEED_TEST_URL`: The address of the gateway's speed test page.
    - `RUN_GATEWAY_SPEED_TEST_INTERVAL`: How often the gateway speed test runs. Set to `0` to disable.
    
    ### Local Test Configuration
    
    - `RUN_LOCAL_PING_TEST`: Set to `True` to run a ping test from your computer to the `PING_TARGET`.
    - `RUN_LOCAL_SPEED_TEST`: Set to `True` to run a speed test from your computer using the Ookla CLI.
    - `RUN_LOCAL_GATEWAY_PING_TEST`: Set to `True` to run a ping test from your computer to the gateway.
    
    ### Anomaly Highlighting & Thresholds
    The console can color-highlight anomalous results to make issues obvious. You can toggle highlighting and configure all thresholds for packet loss, latency, jitter, and bufferbloat in `config.py`.
    
    ### Important: Handling the Device Access Code
    The gateway speed test requires your gateway's **Device Access Code** to log in. The script will securely prompt you for this code when needed and save it to a local `.env` file for future runs.
    
    ## Advanced Configuration
    
    ### Getting Wi-Fi Details (macOS only)
    To capture detailed Wi-Fi metrics like signal strength (RSSI) and noise level, the script uses the built-in `wdutil` command-line tool. However, `wdutil` requires administrator privileges. To allow the script to run `wdutil` without asking for a password every time, you can add a custom rule to the `sudoers` file.
    
    **Follow these steps carefully:**
    
    1.  Open the Terminal and run `sudo visudo`.
    2.  Use the arrow keys to scroll to the bottom of the file and press `o` to start editing on a new line.
    3.  Add the following rule, **replacing `your_username` with your actual macOS username** (type `whoami` in a new terminal to find it):
      ```
      your_username ALL=(ALL) NOPASSWD: /usr/bin/wdutil
      ```
    4.  Press `Escape`, then type `:wq` and press `Enter` to save and exit.
    
    ### Isolating LAN Bufferbloat (Optional)
    By default, the bufferbloat test measures latency on your entire internet connection. To isolate your local network and test if your Wi-Fi router (e.g., Eero) is the source of latency, you can run an optional, LAN-specific test. This requires a second computer on your network to act as a test server.
    
    **Setup Steps:**
    
    1.  **Install `iperf3` on Both Computers**: On your main machine and the second computer, install the `iperf3` network testing tool.
      ```bash
      brew install iperf3
      ```
    2.  **Start the `iperf3` Server**: On the second computer, find its Local IP address (e.g., in System Settings > Wi-Fi). Then, open a Terminal and run it in server mode. Leave this terminal open.
      ```bash
      iperf3 -s
      ```
    3.  **Update `config.py`**: On your main machine, open `config.py` and enable the test:
      * Set `RUN_LAN_BUFFERBLOAT_TEST` to `True`.
      * Set `LAN_TEST_TARGET_IP` to the IP address of your second computer.
    
    The script will now run the additional LAN bufferbloat test during each cycle.
    
    ## License
    This project is licensed under the MIT License.