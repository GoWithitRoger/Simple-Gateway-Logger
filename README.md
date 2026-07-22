<p align="left"><img src="./icon.svg" alt="Simple Gateway Logger" width="120"></p>

# Simple Gateway Logger

A focused macOS diagnostic script for AT&T fiber gateways. It compares gateway-side checks with local-machine checks, then logs each check cycle to CSV so intermittent ISP, router, Wi-Fi, and client issues are easier to separate.

If the gateway path is healthy but the local path is not, look closer to the LAN or client device. If both degrade together, you have better evidence for an ISP-facing problem.

This is a personal hobby project maintained on a best-effort basis. It is useful for the setup it was
built around, but other gateway models and network environments may need adjustments.

## Requirements

- macOS with Homebrew.
- AT&T fiber gateways using the `192.168.1.254` diagnostic pages in [config.py](config.py).
- Google Chrome for Selenium gateway checks. Selenium Manager handles ChromeDriver resolution.
- Ookla's official `speedtest` CLI for local speed and under-load latency.

This is intentionally not a router-agnostic framework, dashboard, daemon, or replacement for ISP tooling.

## Quickstart

Install local tools and make sure Google Chrome is installed:

```bash
brew install uv speedtest
```

Clone, review config, and run:

```bash
git clone https://github.com/GoWithitRoger/Simple-Gateway-Logger.git
cd Simple-Gateway-Logger
uv run python main.py
```

Before leaving it running, review [config.py](config.py). Optional checks such as LAN bufferbloat, raw gateway logs, stale ChromeDriver cleanup, and privileged Wi-Fi diagnostics are off by default.

## What It Logs

- Gateway ping and optional gateway speed test.
- Local WAN ping, gateway ping, Ookla speed test, jitter, packet loss, and WAN bufferbloat.
- Optional macOS Wi-Fi metrics.
- Optional LAN bufferbloat against a second machine running `iperf3`.
- Terminal summaries plus one CSV row per check cycle.

## Configuration

All user-facing settings live in [config.py](config.py). The most common ones are:

- `PING_TARGET`: WAN host to ping, such as `google.com`.
- `LOG_FILE`: CSV output path.
- `RUN_INTERVAL_MINUTES`: check cadence.
- `RUN_GATEWAY_PING_TEST`: gateway ping toggle.
- `RUN_GATEWAY_SPEED_TEST_INTERVAL`: gateway speed cadence; `0` disables it.
- `RUN_LOCAL_PING_TEST`, `RUN_LOCAL_GATEWAY_PING_TEST`, `RUN_LOCAL_SPEED_TEST`: local check toggles.
- `ENABLE_ANOMALY_HIGHLIGHTING`: terminal highlighting for threshold misses.

The gateway speed test may require your Device Access Code. To avoid being prompted, create a local `.env` file:

```bash
GATEWAY_ACCESS_CODE=your-device-access-code
```

`.env` is ignored by Git.

## Output

The script prints a compact summary and appends to `network_log.csv`.

```text
--- Local Machine Test Results ---
  WAN Packet Loss:            0.00 %
  WAN RTT (avg):              18.42 ms
  Downstream Speed:           318.76 Mbps
  Download Bufferbloat:       24.13 ms
```

CSV and raw log files can include local network metadata such as gateway latency, Wi-Fi channel, RSSI/noise, and BSSID when optional diagnostics are enabled. Sanitize local artifacts before sharing them.

<details>
<summary>Optional diagnostics</summary>

### macOS Wi-Fi Metrics

Set `RUN_WIFI_DIAGNOSTICS_TEST = True` to collect Wi-Fi metrics using `wdutil`. The command runs with `sudo -n`, so it fails fast instead of prompting if passwordless sudo is not configured.

If you choose to allow passwordless use, edit sudoers only with `sudo visudo`:

```text
your_username ALL=(ALL) NOPASSWD: /usr/bin/wdutil
```

### LAN Bufferbloat

Set `RUN_LAN_BUFFERBLOAT_TEST = True` only when a second machine on your LAN is running `iperf3 -s`.

```bash
brew install iperf3
iperf3 -s
```

Then set `LAN_TEST_TARGET_IP` in [config.py](config.py) to that machine's LAN IP.

### Debug Toggles

- `LOG_RAW_GATEWAY_OUTPUT`: append raw gateway ping output to `gateway_raw_output.log`.
- `CLEANUP_STALE_CHROMEDRIVER_PROCESSES`: best-effort cleanup for stale ChromeDriver processes. This can terminate unrelated ChromeDriver sessions.
- `ENABLE_CHROME_NO_SANDBOX`: troubleshooting-only Chrome flag; leave off unless Chrome fails to start.

</details>

## Development

```bash
uv sync
uv run ruff check .
uv run ruff format . --check
uv run ty check
uv run pytest -q
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the small-project contribution workflow.

## License

MIT License. See [LICENSE](LICENSE).
