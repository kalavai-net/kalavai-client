#!/usr/bin/env python3
"""
Lago Event Generator

A script to periodically send events to the Lago payment system API.
Supports configurable parameters via command line arguments.
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime
from typing import Dict, Any, Optional

import requests


class LagoEventGenerator:
    """Handles sending events to Lago API with configurable parameters."""
    
    def __init__(
        self,
        lago_url: str,
        api_key: str,
        external_subscription_id: str, 
        event_code: str,
        interval: int,
        properties: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the Lago Event Generator.
        
        Args:
            lago_url: Base URL for Lago API
            api_key: API key for authentication
            external_subscription_id: External subscription ID
            event_code: Event code to send
            interval: Time interval between events in seconds
            properties: Optional event properties
        """
        self.lago_url = lago_url.rstrip('/')
        self.api_key = api_key
        self.external_subscription_id = external_subscription_id
        self.event_code = event_code
        self.interval = interval
        self.properties = properties or {}
        
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
    
    def send_event(self) -> bool:
        """
        Send a single event to the Lago API.
        
        Returns:
            bool: True if event was sent successfully, False otherwise
        """
        url = f"{self.lago_url}/api/v1/events"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Add timestamp to properties
        event_properties = self.properties.copy()
        event_properties["timestamp"] = datetime.utcnow().isoformat()
        
        payload = {
            "event": {
                "external_subscription_id": self.external_subscription_id,
                "code": self.event_code,
                "properties": event_properties
            }
        }
        
        try:
            self.logger.info(f"Sending event '{self.event_code}' to subscription '{self.external_subscription_id}'")
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                self.logger.info(f"Event '{self.event_code}' sent successfully")
                return True
            else:
                self.logger.error(
                    f"Failed to send event '{self.event_code}'. "
                    f"Status: {response.status_code}, Response: {response.text}"
                )
                return False
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            return False
    
    def run_periodic(self, max_events: Optional[int] = None):
        """
        Run the event generator periodically.
        
        Args:
            max_events: Maximum number of events to send (None for infinite)
        """
        self.logger.info(
            f"Starting periodic event generation. "
            f"Interval: {self.interval}s, Max events: {max_events or 'unlimited'}"
        )
        
        event_count = 0
        
        try:
            while True:
                if max_events and event_count >= max_events:
                    self.logger.info(f"Reached maximum events limit ({max_events})")
                    break
                
                success = self.send_event()
                event_count += 1
                
                if not success:
                    self.logger.warning(f"Event {event_count} failed, continuing...")
                
                self.logger.info(f"Waiting {self.interval} seconds before next event...")
                time.sleep(self.interval)
                
        except KeyboardInterrupt:
            self.logger.info("Received interrupt signal, stopping...")
        except Exception as e:
            self.logger.error(f"Unexpected error in periodic execution: {e}")
        finally:
            self.logger.info(f"Event generation stopped. Total events sent: {event_count}")


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Send periodic events to Lago payment system API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Send events every 60 seconds
  python event_generator.py --lago_url "https://api.getlago.com" \\
    --api_key "your_api_key" \\
    --external_subscription_id "sub_123" \\
    --event_code "usage" \\
    --interval 60

  # Send events with custom properties
  python event_generator.py --lago_url "https://api.getlago.com" \\
    --api_key "your_api_key" \\
    --external_subscription_id "sub_123" \\
    --event_code "api_call" \\
    --interval 30 \\
    --properties '{"requests": 1, "endpoint": "/api/v1/users"}'

  # Send limited number of events
  python event_generator.py --lago_url "https://api.getlago.com" \\
    --api_key "your_api_key" \\
    --external_subscription_id "sub_123" \\
    --event_code "test" \\
    --interval 10 \\
    --max_events 5
        """
    )
    
    # Required arguments
    parser.add_argument(
        "--lago_url", 
        required=True, 
        help="Lago API base URL (e.g., https://api.getlago.com)"
    )
    parser.add_argument(
        "--api_key", 
        required=True, 
        help="Lago API key for authentication"
    )
    parser.add_argument(
        "--external_subscription_id", 
        required=True, 
        help="External subscription ID"
    )
    parser.add_argument(
        "--event_code", 
        required=True, 
        help="Event code to send"
    )
    parser.add_argument(
        "--interval", 
        type=int, 
        required=True, 
        help="Time interval between events in seconds"
    )
    
    # Optional arguments
    parser.add_argument(
        "--properties", 
        type=str, 
        help="JSON string of event properties (e.g., '{\"requests\": 1, \"endpoint\": \"/api\"}')"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true", 
        help="Enable verbose logging"
    )
    
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_arguments()
    
    # Setup logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Parse properties if provided
    properties = {}
    if args.properties:
        try:
            properties = json.loads(args.properties)
        except json.JSONDecodeError as e:
            print(f"Error parsing properties JSON: {e}")
            sys.exit(1)
    
    # Validate interval
    if args.interval <= 0:
        print("Error: Interval must be a positive integer")
        sys.exit(1)
    
    # Create and run event generator
    generator = LagoEventGenerator(
        lago_url=args.lago_url,
        api_key=args.api_key,
        external_subscription_id=args.external_subscription_id,
        event_code=args.event_code,
        interval=args.interval,
        properties=properties
    )
    
    generator.run_periodic(max_events=args.max_events)


if __name__ == "__main__":
    main()
