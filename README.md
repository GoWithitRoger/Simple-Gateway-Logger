# Simple Gateway Logger

This Python script automates running the ping testing capability of AT&T fiber gateway and logging the results to track internet quality. It's useful for sussing out ISP issues (with the ISP's connection to the home and gateway), as opposed to subscriber issues inside the home (a 3rd-party router, wifi access points, etc.).

## Features
Uses Selenium to automate interaction with the gateway's web interface. [cite: main.py]
Runs in headless mode, so no browser window is required. [cite: main.py]
Schedules the test to run at a configurable interval. [cite: main.py]
Appends results to a local log file. [cite: main.py]
Usage and Setup
This project offers two distinct paths: a simple one-step command for general use, and a more comprehensive setup for developers.

## For General Use (Single-Step)
If you just want to run the script, you only need Python and uv installed. There is no need to create or activate a virtual environment.

Simply run the following command in your terminal:

```bash
uv run main.py
```

`uv` will automatically read the required dependencies from the top of the `main.py` file, create a temporary environment, and run the script.

## For Development

If you want to modify the code or run development tools like `ruff`, set up a dedicated project environment.

**1. Clone the Repository**

```bash
git clone <repository-url>
cd simple-gateway-logger
```

2. Create and Activate the Virtual Environment
This creates a persistent environment for the project.


```bash
# Create the venv
uv venv

# Activate it
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
```

3. Install All Dependencies
This installs the core packages plus development tools into your activated environment.

```bash
uv pip install -e ".[dev]"
```

4. Running Development Tools
With the environment activated, you can now run the development tools; e.g.:

```bash
# Format the code
ruff format .

# Check for linting errors and fix them
ruff check . --fix
```

## Configuration
Before running the script (using either method), open the main.py file and update the following configuration variables:

- GATEWAY_URL: The address of the gateway; defaults to http://192.168.1.254.
- DIAG_URL: The address of the gateway's diagnostics page; defaults to "http://192.168.1.254/cgi-bin/diag.ha"
- PING_TARGET: The IP address to ping; defaults to google.com.
- RUN_INTERVAL_MINUTES: How often the script should run; defaults to 5 minutes.
