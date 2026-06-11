#!/usr/bin/env python3
"""Monitors CPU, memory, and disk usage. Logs alerts when thresholds are exceeded."""

import logging
import os
import sys
import time

try:
    import psutil
except ImportError:
    sys.exit("missing dependency: pip install psutil")

CPU_THRESH = 80
MEM_THRESH = 80
DISK_THRESH = 85
POLL_INTERVAL = 5
LOG_FILE = "/var/log/system_health.log"


def init_logging():
    log = logging.getLogger("syshealth")
    log.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

    log.addHandler(_make_handler(logging.StreamHandler(sys.stdout), fmt))

    # fall back to cwd if /var/log isn't writable
    path = LOG_FILE
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        fh = logging.FileHandler(path)
    except PermissionError:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "system_health.log")
        fh = logging.FileHandler(path)

    log.addHandler(_make_handler(fh, fmt))
    log.info("log file: %s", path)
    return log


def _make_handler(handler, fmt):
    handler.setFormatter(fmt)
    return handler


def check_cpu(log):
    pct = psutil.cpu_percent(interval=1)
    if pct > CPU_THRESH:
        log.warning("CPU  %.1f%% — exceeds %d%% threshold", pct, CPU_THRESH)
    else:
        log.info("CPU  %.1f%%", pct)


def check_memory(log):
    mem = psutil.virtual_memory()
    used_gb = mem.used / (1 << 30)
    total_gb = mem.total / (1 << 30)
    if mem.percent > MEM_THRESH:
        log.warning("MEM  %.1f%% (%.1f/%.1f GB) — exceeds %d%% threshold",
                     mem.percent, used_gb, total_gb, MEM_THRESH)
    else:
        log.info("MEM  %.1f%%", mem.percent)


def check_disk(log):
    for part in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(part.mountpoint)
        except PermissionError:
            continue
        if usage.percent > DISK_THRESH:
            log.warning("DISK %s %.1f%% (%.1f/%.1f GB) — exceeds %d%% threshold",
                         part.mountpoint, usage.percent,
                         usage.used / (1 << 30), usage.total / (1 << 30), DISK_THRESH)
        else:
            log.info("DISK %s %.1f%%", part.mountpoint, usage.percent)


def top_procs(log, n=5):
    procs = []
    for p in psutil.process_iter(["pid", "name", "cpu_percent"]):
        try:
            procs.append(p.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    procs.sort(key=lambda x: x.get("cpu_percent") or 0, reverse=True)
    summary = ", ".join(f"{p['name']}({p['pid']})={p.get('cpu_percent', 0):.0f}%"
                        for p in procs[:n])
    log.info("TOP  %s", summary)


def main():
    log = init_logging()
    log.info("thresholds — cpu:%d%% mem:%d%% disk:%d%%", CPU_THRESH, MEM_THRESH, DISK_THRESH)
    try:
        while True:
            check_cpu(log)
            check_memory(log)
            check_disk(log)
            top_procs(log)
            log.info("---")
            time.sleep(POLL_INTERVAL)
    except KeyboardInterrupt:
        log.info("stopped")
    except Exception:
        log.exception("fatal")
        sys.exit(1)


if __name__ == "__main__":
    main()
