# Simple Gateway Logger

This is a Python script that automates logging into an AT&T fiber gateway/modem, running a ping test, and logging the results to track internet quality. It's useful for sussing out ISP issues (with the ISP's connection to the home and gateway), as opposed subscriber issues inside the home (LAN - router, wifi access points, etc).

## Features

- Uses Selenium to automate interaction with the gateway's web interface.
- Runs in headless mode, so no browser window is required.
- Schedules the test to run at a configurable interval.
- Appends results to a local log file.

## Setup and Installation

1.  **Prerequisites**:
    *   Python 3.11+
    *   [uv](https://github.com/astral-sh/uv) (the Python package manager).
    *   Google Chrome and the matching version of `chromedriver` installed and available in your system's PATH.

2.  **Clone the Repository**:
    ```bash
    git clone <repository-url>
    cd simple-gateway-logger
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
    *   `PING_TARGET`: The IP address to ping. Defaults to Google.com.
    *   `RUN_INTERVAL_MINUTES`: How often the script should run. Defaults to `5` minutes.

## Usage

Once configured, you can run the script directly:

```bash
uv run main.py
```

or

```bash
python main.py
```

The script will run the ping test once immediately, then perform subsequent runs based on your configuration. Press `Ctrl+C` to stop the script.

## Scraped Data

The results of each ping test are appended to `ping_log.csv` in the project's root directory.

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
