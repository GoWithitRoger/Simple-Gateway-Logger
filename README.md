# Simple Gateway Logger

This script automates running the ping testing capability of your AT\&T fiber gateway and logging the results. It's useful for sussing out ISP issues (with the ISP's connection to the home and gateway), as opposed to subscriber issues inside the home (a 3rd-party router, wifi access points, etc.).

## Features

  - Uses Selenium to automate interaction with the gateway's web interface.
  - Runs in headless mode, so no browser window is required.
  - Schedules the test to run at a configurable interval.
  - Appends results to a local log file (csv).

### New in this Version: Speed Testing\!

  - In addition to ping tests, the script can now automatically run a **Speed Test** using the gateway's built-in tool.
  - Results (Downstream and Upstream Mbps) are logged to the console and the CSV file.

## Usage and Setup

This project offers two distinct paths: a simple one-step command for general use, and a more comprehensive setup for developers.

### For General Use (Single-Step)

If you just want to run the script, you only need Python and uv installed. There is no need to create or activate a virtual environment.

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

**2. Create and Activate the Virtual Environment**
This creates a persistent environment for the project.

```bash
# Create the venv
uv venv

# Activate it
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
```

**3. Install All Dependencies**
This installs the core packages plus development tools into your activated environment.

```bash
uv pip install -e ".[dev]"
```

**4. Running Development Tools**
With the environment activated, you can now run the development tools; e.g.:

```bash
# Format the code
uv run ruff format .

# Check for linting errors and fix them
uv run ruff check . --fix

# type checking
uv run ty check .

# testing
uv run pytest
```

## Configuration

Before running the script, open the `main.py` file and update the following configuration variables:

  - `GATEWAY_URL`: The address of the gateway; defaults to `http://192.168.1.254`.
  - `DIAG_URL`: The address of the gateway's diagnostics page.
  - `SPEED_TEST_URL`: The address of the gateway's speed test page.
  - `PING_TARGET`: The IP address to ping; defaults to `google.com`.
  - `RUN_INTERVAL_MINUTES`: How often the script should run; defaults to 5 minutes.
  - `RUN_SPEED_TEST_INTERVAL`: How often the speed test runs. For example, a value of `2` means the speed test will run every other time the ping test runs. Set to `0` to disable speed tests completely.

### **Important: Handling the Device Access Code**

The speed test requires your gateway's **Device Access Code** to log in. To keep this secure and out of your repository, the script uses an environment variable.

**Recommended Method: `.env` file**

1.  Create a file named `.env` in the same directory as `main.py`.
2.  Add the following line to the `.env` file, replacing the placeholder with your actual code:
    ```
    GATEWAY_ACCESS_CODE='your_code_here'
    ```
3.  The script will automatically detect and use this code. The `.gitignore` file is already configured to ignore `.env` files.

If you don't provide the code via an environment variable, the script will prompt you to enter it in the terminal on the first run.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE.md) file for details.