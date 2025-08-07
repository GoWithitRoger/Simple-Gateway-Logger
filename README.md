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
- Runs in headless mode, so no browser window is required.
- Schedules tests to run at a configurable interval.
- Appends combined results to a single, local CSV log file, creating headers if the file is new or empty.
- Captures detailed Wi-Fi metrics on macOS (Signal, Noise, Channel, etc.).
- All configuration is organized in the `config.py` file.


## Prerequisites
- Designed to run on MacOS with Homebrew package manager installed.
- Before running the script, you must install the official Ookla Speedtest CLI.

### Installing Ookla Speedtest CLI on macOS (via Homebrew)
If you don't have Homebrew, [install it first](https://brew.sh/). Then, run the following command in your terminal:

  ```bash
    brew install speedtest
  ```

## Usage and Setup
Simply run the following command in a terminal window:

  ```bash 
      uv run main.py
  ```
  `uv` will automatically read the required dependencies from the top of the `main.py` file, create a temporary environment, and run the script.
    
## Configuration
All configuration has been moved to the **`config.py`** file for easy editing.

### General Configuration

- `PING_TARGET`: The IP address or hostname to ping (e.g., "google.com").
- `LOG_FILE`: The name of the CSV file for storing results.
- `RUN_INTERVAL_MINUTES`: How often the script should run.
- `HEADLESS_MODE`: Set to `True` to run the browser invisibly in the background.

### Gateway Test Configuration

- `GATEWAY_URL`: The address of the fiber gateway (e.g., `http://192.168.1.254`).
- `DIAG_URL`: The address of the gateway's diagnostics page.
- `SPEED_TEST_URL`: The address of the gateway's speed test page.
- `RUN_GATEWAY_SPEED_TEST_INTERVAL`: How often the gateway speed test runs. For example, a value of `2` means the speed test will run every other time the main checks run. Set to `0` to disable.

### Local Test Configuration

- `RUN_LOCAL_PING_TEST`: Set to `True` to run a ping test from your computer to the `PING_TARGET`.
- `RUN_LOCAL_SPEED_TEST`: Set to `True` to run a speed test from your computer using the Ookla CLI.
- `RUN_LOCAL_GATEWAY_PING_TEST`: Set to `True` to run a ping test from your computer to the gateway.

### Important: Handling the Device Access Code
The gateway speed test requires your gateway's **Device Access Code** to log in. To store this securely, the script uses an environment variable.

**Recommended Method: `.env` file**

If you don't provide the code via an environment variable (see instructions below), the script will prompt you to enter it in the terminal when a gateway speed test is scheduled to run and it will create this file for you.

If you want to create the `.env` file manually, follow these steps:

1. Create a file named `.env` in the same directory as `main.py`.
2. Add the following line to the `.env` file, replacing the placeholder with your actual code:

        GATEWAY_ACCESS_CODE='your_code_here'

3. The script will automatically detect and use this code.


## Advanced Configuration

### Getting Wi-Fi Details (macOS only)

To capture detailed Wi-Fi metrics like signal strength (RSSI), noise level, channel, and band, the script uses the built-in `wdutil` command-line tool. However, `wdutil` requires `sudo` (administrator) privileges to run.

To allow the script to run `wdutil` without asking for a password every time, you need to add a custom rule to the `sudoers` file.

**Follow these steps carefully:**

1.  **Open the sudoers file for editing:**
    Open the Terminal app and run the following command. You will be prompted to enter your macOS user password.
    ```bash
    sudo visudo
    ```
2.  **Edit the file:**
    This will open the `sudoers` file in the `vim` text editor. Don't be intimidated!
    - Use the arrow keys to scroll to the very bottom of the file.
    - Press the `o` key to start "insert mode" on a new line.
3.  **Add the new rule:**
    Carefully type or paste the following line. **Replace `your_username` with your actual macOS username** (the one you use to log in).
    ```
    your_username ALL=(ALL) NOPASSWD: /usr/bin/wdutil
    ```
    *To find your username, you can open a new terminal window and type `whoami`.*
4.  **Save and exit:**
    - Press the `Escape` key to exit insert mode.
    - Type `:wq` and press `Enter` to save the file and quit `vim`.

If you make a mistake, `visudo` will warn you. In that case, type `e` and press `Enter` to re-edit the file and fix the error.

Once this is done, the script will be able to gather and log Wi-Fi details automatically.

## License
This project is licensed under the MIT License.
