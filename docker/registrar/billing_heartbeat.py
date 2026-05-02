#!/usr/bin/env python3
"""
Billing Event Generator

A script to periodically send events to the Flexprice payment system API.
Supports configurable parameters via environment variables.

# TODO:
- Deploy as side car of server pod
- Downward API to generate metadata:
    get kalavai/region and kalavai/instance for
    properties filter (region and instance)
- Add a health check endpoint (start billing then)

EVENT_PROPERTIES should include enough info to then filter by provicer/gpu. Example:

EVENT_PROPERTIES='{"provider": <kalavai/region>, "instance": <kalavai/instance>, "count": X}' 
python3 billing_heartbeat.py
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from typing import Dict, Any, Optional

import aiohttp

FLEXPRICE_URL = os.getenv("FLEXPRICE_URL", "https://api.cloud.flexprice.io")
FLEXPRICE_API_KEY = os.getenv("FLEXPRICE_API_KEY", "")
EVENT_NAME = os.getenv("EVENT_NAME", "vram_usage")
EVENT_EXTERNAL_CUSTOMER_ID = os.getenv("EVENT_EXTERNAL_CUSTOMER_ID", "cust-carlos")
EVENT_PROPERTIES = os.getenv("EVENT_PROPERTIES", '{"vram_minutes": 160, "instance": "rtx-ada2000", "region": "uspor01"}')
HEARTBEAT_INTERVAL = int(os.getenv("HEARTBEAT_INTERVAL", "1"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
RETRY_DELAY = float(os.getenv("RETRY_DELAY", "1.0"))


class BillingEventGenerator:
    """Handles sending events to Flexprice API with configurable parameters."""
    
    def __init__(
        self,
        flexprice_url: str,
        api_key: str,
        external_customer_id: str, 
        event_name: str,
        interval: int,
        properties: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the Billing Event Generator.
        
        Args:
            flexprice_url: Base URL for Flexprice API
            api_key: API key for authentication
            external_customer_id: External subscription ID
            event_name: Event code to send
            interval: Time interval between events in minutes
            properties: Optional event properties
        """
        self.flexprice_url = flexprice_url.rstrip('/')
        self.api_key = api_key
        self.external_customer_id = external_customer_id
        self.event_name = event_name
        self.interval = interval * 60
        self.properties = properties or {}
        self.session = None
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def _ensure_session(self):
        """Ensure aiohttp session is created."""
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
    
    async def send_event_async(self) -> bool:
        """
        Send a single event to the Flexprice API asynchronously with retry logic.
        
        Returns:
            bool: True if event was sent successfully, False otherwise
        """
        await self._ensure_session()
        
        url = f"{self.flexprice_url}/v1/events"
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        time_now = datetime.utcnow()
        timestamp = time_now.strftime('%Y-%m-%dT%H:%M:%SZ')
        event_id = f"{self.external_customer_id}_{self.event_name}_{int(time_now.timestamp())}".lower()
        
        payload = {
            "external_customer_id": self.external_customer_id,
            "event_name": self.event_name,
            "properties": self.properties,
            "event_id": event_id,
            "source": "heartbeat",
            "timestamp": timestamp
        }

        for attempt in range(MAX_RETRIES):
            try:
                self.logger.info(f"Sending event '{self.event_name}' to subscription '{self.external_customer_id}' (attempt {attempt + 1}/{MAX_RETRIES})")
                
                async with self.session.post(url, headers=headers, json=payload) as response:
                    if response.status < 300:
                        self.logger.info(f"Event '{self.event_name}' sent successfully on attempt {attempt + 1}")
                        return True
                    else:
                        response_text = await response.text()
                        self.logger.warning(
                            f"Failed to send event '{self.event_name}' on attempt {attempt + 1}. "
                            f"Status: {response.status}, Response: {response_text}"
                        )
                        if attempt < MAX_RETRIES - 1:
                            await asyncio.sleep(RETRY_DELAY * (2 ** attempt))  # Exponential backoff
                        continue
                        
            except aiohttp.ClientError as e:
                self.logger.warning(f"Request failed on attempt {attempt + 1}: {e}")
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_DELAY * (2 ** attempt))  # Exponential backoff
                continue
            except Exception as e:
                self.logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_DELAY * (2 ** attempt))
                continue
        
        self.logger.error(f"Failed to send event '{self.event_name}' after {MAX_RETRIES} attempts")
        return False
    
    async def run_periodic_async(self):
        """
        Run the event generator periodically with fixed intervals using async.
        """
        self.logger.info(
            f"Starting periodic event generation. "
            f"Interval: {self.interval}s, Max retries: {MAX_RETRIES}"
        )
        
        event_count = 0
        
        try:
            while True:
                # Schedule the next event immediately to maintain fixed intervals
                asyncio.create_task(self.send_event_async())
                event_count += 1
                
                self.logger.info(f"Scheduled event {event_count}, waiting {self.interval} seconds...")
                await asyncio.sleep(self.interval)
                
        except KeyboardInterrupt:
            self.logger.info("Received interrupt signal, stopping...")
        except Exception as e:
            self.logger.error(f"Unexpected error in periodic execution: {e}")
        finally:
            self.logger.info(f"Event generation stopped. Total events scheduled: {event_count}")
    
    def run_periodic(self):
        """
        Synchronous wrapper for run_periodic_async.
        """
        try:
            asyncio.run(self.run_periodic_async())
        except KeyboardInterrupt:
            self.logger.info("Received interrupt signal, stopping...")
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")


def main():
    """Main entry point."""
    
    # Parse properties if provided
    properties = {}
    if EVENT_PROPERTIES:
        try:
            properties = json.loads(EVENT_PROPERTIES)
        except json.JSONDecodeError as e:
            print(f"Error parsing properties JSON: {e}")
            sys.exit(1)
    
    # Validate interval
    if HEARTBEAT_INTERVAL <= 0:
        print("Error: Interval must be a positive integer")
        sys.exit(1)
    
    
    # Create and run event generator
    generator = BillingEventGenerator(
        flexprice_url=FLEXPRICE_URL,
        api_key=FLEXPRICE_API_KEY,
        external_customer_id=EVENT_EXTERNAL_CUSTOMER_ID,
        event_name=EVENT_NAME,
        interval=HEARTBEAT_INTERVAL,
        properties=properties
    )
    
    generator.run_periodic()


if __name__ == "__main__":
    main()
