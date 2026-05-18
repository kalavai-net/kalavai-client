#!/usr/bin/env python3
"""
Billing Event Generator

A script to periodically send events to the stdout. A Vector aggregator can pick them up for billing. Only if pod is labelled "billing=true"

Supports configurable parameters via environment variables.

Vector expects the format:
{
    "event_id": <event id>,
    "timestamp": <+%Y-%m-%dT%H:%M:%S.%3NZ>,
    "user_id": <user id>,
    "job_id": <kalavai job id>,
    "vram_usage": <vram usage>,
    "memory_usage": <memory usage>,
    "cpu_usage": <cpu usage>,
    "gpu_type": <gpu type>,
    "interval_seconds": <interval in seconds>,
    "provider": <kalavai provider>
}

Example:

USER_ID=carlos1 JOB_ID=test-job VRAM_USAGE=10 MEMORY_USAGE=2 CPU_USAGE=4 GPU_TYPE=rtx-ada2000 INTERVAL_SECONDS=60 PROVIDER=shadow python3 usage_event_generator.py
"""

import logging
import os
import time
from datetime import datetime

from pythonjsonlogger.json import JsonFormatter

## Configure logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

logHandler = logging.StreamHandler()
formatter = JsonFormatter()
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)
####################


USER_ID = os.getenv("USER_ID", None)
JOB_ID = os.getenv("JOB_ID", None)
VRAM_USAGE = int(os.getenv("VRAM_USAGE", -1))
MEMORY_USAGE = int(os.getenv("MEMORY_USAGE", -1))
CPU_USAGE = float(os.getenv("CPU_USAGE", -1))
GPU_TYPE = os.getenv("GPU_TYPE", None)
INTERVAL_SECONDS = int(os.getenv("INTERVAL_SECONDS", -1))
PROVIDER = os.getenv("PROVIDER", None)


def main():
    """Main entry point."""
    
    next_event_time = time.time()

    while True:
        # Calculate sleep duration to maintain precise intervals
        current_time = time.time()
        sleep_duration = max(0, next_event_time - current_time)
        
        if sleep_duration > 0:
            time.sleep(sleep_duration)
        
        # Log the event
        print("--> Emitting usage event at:", f"{current_time:.2f}")

        logger.info({
            "event_id": f"{USER_ID}_{JOB_ID}_{int(current_time)}",
            "timestamp": datetime.now().isoformat(),
            "user_id": USER_ID,
            "job_id": JOB_ID,
            "vram_usage": VRAM_USAGE,
            "memory_usage": MEMORY_USAGE,
            "cpu_usage": CPU_USAGE,
            "gpu_type": GPU_TYPE,
            "interval_seconds": INTERVAL_SECONDS,
            "provider": PROVIDER
        })
        
        # Set the next event time
        next_event_time += INTERVAL_SECONDS


if __name__ == "__main__":
    main()
