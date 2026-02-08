#!/usr/bin/env python3
"""
Client Driver for Enhanced Verification Skill.
Handles REST API interactions with retry logic and state stabilization.
"""

import requests
import time
import logging
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class HamClockClient:
    def __init__(self, base_url, timeout=10):
        """
        Initialize the HamClock client wrapper.
        
        Args:
            base_url (str): The base URL of the HamClock instance (e.g., http://localhost:8001).
            timeout (int): Default timeout for requests in seconds.
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()

    def _get_url(self, endpoint):
        return f"{self.base_url}/{endpoint.lstrip('/')}"

    def get(self, endpoint, params=None):
        """
        Execute a GET request to the specified endpoint.
        
        Args:
            endpoint (str): The API endpoint (e.g., 'get_config.txt').
            params (dict): Optional query parameters.
            
        Returns:
            str: The response text, or raises an exception on failure.
        """
        url = self._get_url(endpoint)
        try:
            logger.debug(f"GET {url} with params {params}")
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            logger.error(f"GET {url} failed: {e}")
            raise

    def set(self, endpoint, params=None):
        """
        Execute a SET request (usually GET with params, sometimes POST) to change state.
        
        Args:
            endpoint (str): The API endpoint (e.g., 'set_pane').
            params (dict): Query parameters defining the new state.
            
        Returns:
            bool: True if the operation was successful (response text usually 'ok').
        """
        url = self._get_url(endpoint)
        try:
            logger.info(f"SET {url} with params {params}")
            # Most set_ commands in HamClock use GET query params
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            # Check for 'ok' response which is standard for HamClock set commands
            # 'set_pane' returns 'PaneX ...' on success
            resp_lower = response.text.lower()
            if 'ok' in resp_lower or 'pane' in resp_lower:
                return True
            else:
                logger.warning(f"SET {endpoint} returned unexpected response: {response.text.strip()}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"SET {url} failed: {e}")
            if hasattr(e.response, 'text'):
                 logger.error(f"Response: {e.response.text}")
            raise

    def get_capture(self, filename=None):
        """
        Retrieve a screen capture (BMP) and optionally save to file.
        
        Args:
            filename (str): Optional path to save the BMP file.
            
        Returns:
            bytes: The raw BMP data.
        """
        url = self._get_url('get_capture.bmp')
        try:
            logger.debug(f"GET {url}")
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            if filename:
                with open(filename, 'wb') as f:
                    f.write(response.content)
                logger.info(f"Saved capture to {filename}")
                
            return response.content
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get capture: {e}")
            raise

    def wait_for_settle(self, duration=2.0):
        """
        Wait for a fixed duration to allow the client state to settle.
        
        Args:
            duration (float): Time to wait in seconds.
        """
        logger.info(f"Waiting {duration}s for state to settle...")
        time.sleep(duration)

    def verify_config(self, expected_snippets):
        """
        Verify that get_config.txt contains expected configuration snippets.
        
        Args:
            expected_snippets (list): List of strings expected to be present in get_config.txt.
            
        Returns:
            bool: True if all snippets are found.
        """
        config = self.get('get_config.txt')
        all_found = True
        for snippet in expected_snippets:
            if snippet not in config:
                logger.error(f"VERIFY FAILED: Missing expected config snippet: '{snippet}'")
                all_found = False
        
        return all_found

# Example usage
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="HamClock Client Driver")
    parser.add_argument("--url", default="http://localhost:8001", help="HamClock base URL")
    parser.add_argument("--set-pane", help="Set a pane (e.g., '1=VOACAP')")
    parser.add_argument("--get-config", action="store_true", help="Print current config")
    
    args = parser.parse_args()
    
    client = HamClockClient(args.url)
    
    try:
        if args.set_pane:
            pane, value = args.set_pane.split('=')
            client.set('set_pane', {f'Pane{pane}': value})
            client.wait_for_settle(2)
            
        if args.get_config:
            print(client.get('get_config.txt'))
            
    except Exception as e:
        print(f"Error: {e}")
