<p align="left"> <img src="./icon.svg" alt="Simple Gateway Logger" width="200"> </p>

# Simple Gateway Logger

This script automates running diagnostic tests from your AT&T fiber gateway and your local machine. It logs the results to a CSV file, helping you identify and troubleshoot intermittent network issues.

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
- All configuration is neatly organized in a separate `config.py` file.

## Prerequisites
Before running the script, you must install the official Ookla Speedtest CLI.

### macOS (via Homebrew)

If you don't have Homebrew, [install it first](https://brew.sh/). Then, run the following command in your terminal:

  ```bash
    brew install speedtest
  ```

## Usage and Setup
This project offers two distinct paths: a simple one-step command for general use, and a more comprehensive setup for developers.

### For General Use (Single-Step)
If you just want to run the script, you only need Python and `uv` installed.

Simply run the following command in your terminal:

  ```bash 
      uv run main.py
  ```
  `uv` will automatically read the required dependencies from the top of the `main.py` file, create a temporary environment, and run the script.
    
### For Development
If you want to modify the code or run development tools like `ruff`, set up a dedicated project environment.

**1. Clone the Repository**

  ```bash
      git clone <repository-url>
      cd simple-gateway-logger
  ``` 

**2. Create and Activate the Virtual Environment** This creates a persistent environment for the project.
    
  ```bash
      uv venv
      # Activate it
      source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
  ``` 
**3. Install All Dependencies** This installs the core packages plus development tools into your activated environment.
    
  ```bash
      uv pip install -e ".[dev]"
  ```
**4. Running Development Tools** With the environment activated, you can now run the development tools; e.g.:
    
  ```bash  
      # Format the code
      uv run ruff format .
    
      # Check for linting errors and fix them
      uv run ruff check . --fix
  ```
 
## Configuration
All configuration has been moved to the **`config.py`** file for easy editing. Open this file to adjust any settings.

### General Configuration

- `PING_TARGET`: The IP address or hostname to ping (e.g., "google.com").
- `LOG_FILE`: The name of the CSV file for storing results.
- `RUN_INTERVAL_MINUTES`: How often the script should run.
- `HEADLESS_MODE`: Set to `True` to run the browser invisibly in the background.

### Gateway Test Configuration

- `GATEWAY_URL`: The address of the gateway (e.g., `http://192.168.1.254`).
- `DIAG_URL`: The address of the gateway's diagnostics page.
- `SPEED_TEST_URL`: The address of the gateway's speed test page.
- `RUN_GATEWAY_SPEED_TEST_INTERVAL`: How often the gateway speed test runs. For example, a value of `2` means the speed test will run every other time the main checks run. Set to `0` to disable.

### Local Test Configuration

- `RUN_LOCAL_PING_TEST`: Set to `True` to run a ping test from your computer to the `PING_TARGET`.
- `RUN_LOCAL_SPEED_TEST`: Set to `True` to run a speed test from your computer using the Ookla CLI.
- `RUN_LOCAL_GATEWAY_PING_TEST`: Set to `True` to run a ping test from your computer to the gateway.

### Important: Handling the Device Access Code
The gateway speed test requires your gateway's **Device Access Code** to log in. To keep this secure and out of your repository, the script uses an environment variable.

**Recommended Method: `.env` file**

1. Create a file named `.env` in the same directory as `main.py`.

2. Add the following line to the `.env` file, replacing the placeholder with your actual code:

        GATEWAY_ACCESS_CODE='your_code_here'

3. The script will automatically detect and use this code. The `.gitignore` file is already configured to ignore `.env`files.

If you don't provide the code via an environment variable, the script will prompt you to enter it in the terminal when a gateway speed test is scheduled to run.


## License
This project is licensed under the MIT License.