#!/usr/bin/env python3
"""Checks HTTP endpoints and reports UP/DOWN status with response times."""

import logging
import os
import sys
import time

try:
    import requests
except ImportError:
    sys.exit("missing dependency: pip install requests")

URLS = [
    "https://www.google.com",
    "http://localhost:4499",
]
TIMEOUT = 10
INTERVAL = 30
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_health.log")


def init_logging():
    log = logging.getLogger("apphealth")
    log.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    for h in [logging.StreamHandler(sys.stdout), logging.FileHandler(LOG_FILE)]:
        h.setFormatter(fmt)
        log.addHandler(h)
    return log


def probe(url, log):
    try:
        r = requests.get(url, timeout=TIMEOUT)
        if r.status_code == 200:
            log.info("UP   %s — %d in %.2fs", url, r.status_code, r.elapsed.total_seconds())
            return True
        log.warning("DOWN %s — unexpected %d", url, r.status_code)
    except requests.ConnectionError:
        log.error("DOWN %s — connection refused", url)
    except requests.Timeout:
        log.error("DOWN %s — timed out (%ds)", url, TIMEOUT)
    except requests.RequestException as e:
        log.error("DOWN %s — %s", url, e)
    return False


def main():
    log = init_logging()
    log.info("watching %d endpoint(s)", len(URLS))
    try:
        while True:
            healthy = sum(probe(u, log) for u in URLS)
            log.info("%d/%d up", healthy, len(URLS))
            time.sleep(INTERVAL)
    except KeyboardInterrupt:
        log.info("stopped")
    except Exception:
        log.exception("fatal")
        sys.exit(1)


if __name__ == "__main__":
    main()
