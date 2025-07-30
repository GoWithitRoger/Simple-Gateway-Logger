# Internet Quality Monitor

A Python script that automates logging into an AT&T gateway, running a ping test, and logging the results to track internet quality over time.

## Features

- Uses Selenium to automate interaction with the gateway's web interface.
- Runs in headless mode, so no browser window is required.
- Schedules the test to run at a configurable interval.
- Appends results to a local log file for historical analysis.

## Setup and Installation

1.  **Prerequisites**:
    *   Python 3.11+
    *   [uv](https://github.com/astral-sh/uv) (the Python package manager).
    *   Google Chrome and the matching version of `chromedriver` installed and available in your system's PATH.

2.  **Clone the Repository**:
    ```bash
    git clone <repository-url>
    cd internet-quality-monitor
    ```

3.  **Create Virtual Environment and Install Dependencies**:
    ```bash
    # Create and activate the virtual environment
    uv venv
    source .venv/bin/activate  # On Windows use: .venv\Scripts\activate

    # Install dependencies from pyproject.toml
    uv sync
    ```

4.  **Configuration**:
    Open the `main.py` file and update the following configuration variables:
    *   `DEVICE_ACCESS_CODE`: **This is required.** Enter the Device Access Code found on the back of your AT&T gateway.
    *   `GATEWAY_URL`: The default is `http://192.168.1.254`. Change if your gateway's IP is different.
    *   `PING_TARGET`: The IP address to ping. Defaults to Google's DNS (`8.8.8.8`).
    *   `RUN_INTERVAL_MINUTES`: How often the script should run. Defaults to `10` minutes.

## Usage

Once configured, you can run the script directly:

```bash
python main.py
```

The script will run the ping test once immediately and then schedule subsequent runs based on your configuration. Press `Ctrl+C` to stop the script.

## Scraped Data

The results of each ping test are appended to `ping_log.txt` in the project's root directory. Each entry includes a timestamp, the ping target, and the raw output from the gateway's diagnostic tool.

## Development Tools

This project uses `ruff` for linting/formatting and `ty` for type checking.

### Linting and Formatting

```bash
# Format the code
uv run ruff format .

# Check for linting errors and automatically fix them
uv run ruff check . --fix
```

### Type Checking

```bash
# Run the type checker
uv run ty check .
```

## License

MIT
