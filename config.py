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
# Set to True to enable verbose, high-resolution debug logging for troubleshooting.
ENABLE_DEBUG_LOGGING: bool = True

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


# --- Anomaly Detection Configuration ---
# Set to True to enable highlighting of anomalous results in the console output.
ENABLE_ANOMALY_HIGHLIGHTING: bool = True

# --- Anomaly Thresholds ---
# NOTE: Set a value to None to disable the check for that specific metric.
# Any packet loss percentage strictly greater than this value is an anomaly.
PACKET_LOSS_THRESHOLD: float = 0.0
# Any ping RTT (average) strictly greater than this value (in ms) is an anomaly.
PING_RTT_THRESHOLD: float = 30.0
# Any jitter measurement strictly greater than this value (in ms) is an anomaly.
JITTER_THRESHOLD: float = 5.0
# A latency increase (in ms) greater than this is an anomaly (bufferbloat delta).
BUFFERBLOAT_DELTA_THRESHOLD: float = 75.0
# Latency (in ms) during download/upload that is an anomaly.
LATENCY_UNDER_LOAD_THRESHOLD: float = 100.0
# Packet loss percentage from the speedtest that is an anomaly.
SPEEDTEST_PACKET_LOSS_THRESHOLD: float = 0.5

# --- Speed Test Thresholds (in Mbps) ---
# Set separate thresholds for speed tests. Anomalies are values strictly LESS than these.
LOCAL_DOWNSTREAM_SPEED_THRESHOLD: float = 225.0
LOCAL_UPSTREAM_SPEED_THRESHOLD: float = 225.0
GATEWAY_DOWNSTREAM_SPEED_THRESHOLD: float = 300.0
GATEWAY_UPSTREAM_SPEED_THRESHOLD: float = 300.0

# --- LAN Bufferbloat Test Configuration ---
# Set to True to run the LAN-specific bufferbloat test against another
# machine on your local network. Requires `iperf3` on both machines.
RUN_LAN_BUFFERBLOAT_TEST: bool = True
# The IP address of the second machine on your LAN running `iperf3 -s`.
LAN_TEST_TARGET_IP: str = "192.168.4.135"  # <--- CHANGE THIS TO YOUR SERVER's IP
# How long (in seconds) the LAN load test should run.
LAN_BUFFERBLOAT_TEST_DURATION: int = 10
# Threshold for LAN bufferbloat delta (in ms).
LAN_BUFFERBLOAT_DELTA_THRESHOLD: float = 50.0
