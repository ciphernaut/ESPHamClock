#!/usr/bin/env python3
"""
Set DX location to Augsburg, Germany (48.37N, 10.90E) for both clients.
"""

import sys
import logging
import argparse
from client_driver import HamClockClient

# Augsburg Coordinates
LAT = 48.37
LNG = 10.90
GRID = "JN58" # Approximate grid for Augsburg

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def set_dx(client_name, port):
    client = HamClockClient(f"http://localhost:{port}")
    logger.info(f"Setting DX for {client_name} (Port {port}) to Augsburg ({LAT}, {LNG})...")

    # Use key-value map for params as expected by client_driver
    try:
        params = {
            'grid': GRID
        }
        client.set('set_newdx', params)
        client.wait_for_settle(1.0)
        
        # Verify
        config = client.get('get_config.txt')
        # Check if Grid or Lat/Lng allows us to confirm. 
        # get_config.txt might show DX Lat/Lng or Grid.
        if "JN58" in config or f"lat {LAT}" in config or str(LAT) in config:
             logger.info(f"{client_name}: DX set successfully.")
        else:
             logger.warning(f"{client_name}: Could not verify DX setting in config.")
             logger.debug(config)
             
    except Exception as e:
        logger.error(f"{client_name}: Failed to set DX: {e}")

if __name__ == "__main__":
    set_dx("DUT", 8001)
    set_dx("Baseline", 8002)
