# config.py

# --- General Configuration ---
# The IP address or hostname for the target of the WAN ping test.
PING_TARGET: str = "google.com"
# The name of the file where results will be logged.
LOG_FILE: str = "network_log.csv"
# How often the script should run, in minutes.
RUN_INTERVAL_MINUTES: int = 5
# Set to True to run the browser in headless mode (no visible UI).
HEADLESS_MODE: bool = True

# --- Gateway Configuration ---
# The base URL for your AT&T gateway.
GATEWAY_URL: str = "http://192.168.1.254"
# The full URL to the gateway's diagnostics page.
DIAG_URL: str = "http://192.168.1.254/cgi-bin/diag.ha"
# The full URL to the gateway's speed test page.
SPEED_TEST_URL: str = "http://192.168.1.254/cgi-bin/speed.ha"
# How often the gateway speed test runs. For example, a value of 2 means the
# speed test will run every other time the main checks run.
# Set to 0 to disable gateway speed tests entirely.
RUN_GATEWAY_SPEED_TEST_INTERVAL: int = 1

# --- Local Machine Test Configuration ---
# Set to True to run a ping test from the local machine to the PING_TARGET.
RUN_LOCAL_PING_TEST: bool = True
# Set to True to run a speed test from the local machine using the Ookla CLI.
RUN_LOCAL_SPEED_TEST: bool = True
# Set to True to run a ping test from the local machine to the gateway itself.
RUN_LOCAL_GATEWAY_PING_TEST: bool = True
