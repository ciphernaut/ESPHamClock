#!/usr/bin/env python3
"""
Complex Parity Verification Orchestrator.
Runs end-to-end test scenarios comparing two HamClock instances.
"""

import argparse
import logging
import time
import sys
import os
from client_driver import HamClockClient
from visual_verifier import VisualVerifier

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Default Ports
DUT_PORT = 8001      # ax4test
BASELINE_PORT = 8002 # ax4upstream

def run_voacap_scenario(dut, baseline, verifier):
    """
    Test Scenario: VOACAP on Pane 1
    1. Set both clients to show VOACAP on Pane 1.
    2. Wait for calculation to settle.
    3. Compare config strings.
    4. Compare screen captures.
    """
    logger.info("Starting VOACAP Pane 1 Scenario...")
    # 1. State Injection (Reset background panes first to free up VOACAP)
    logger.info("Clearing potential conflicts in Panes 2 & 3...")
    for client in [dut, baseline]:
        client.set('set_pane', {'Pane2': 'Solar_Flux'})
        client.set('set_pane', {'Pane3': 'Planetary_K'})

    logger.info("Setting Pane 1 to VOACAP on both instances...")
    dut.set('set_pane', {'Pane1': 'VOACAP_DEDX'})
    baseline.set('set_pane', {'Pane1': 'VOACAP_DEDX'})
    
    # 2. Wait for Settle (VOACAP execution takes time)
    logger.info("Waiting 5s for VOACAP calculations...")
    time.sleep(5) 
    
    # 3. Verify Config
    logger.info("Verifying configuration parity...")
    dut_config = dut.get('get_config.txt')
    baseline_config = baseline.get('get_config.txt')

    def normalize_config(config_str):
        normalized = []
        for line in config_str.splitlines():
            # Filter out dynamic timer/rotation info
            if "rotating in" in line:
                line = line.split(" rotating in")[0]
            # Filter out One Alarm which seems time-dependent
            if "One Alarm" in line:
                continue
            # Filter out callsign differences if we haven't synced them (though we should)
            if line.startswith("CALL"):
                continue # We'll set this explicitly in future, but ignore for now
            normalized.append(line)
        return "\n".join(normalized)

    dut_norm = normalize_config(dut_config)
    baseline_norm = normalize_config(baseline_config)
    
    if dut_norm != baseline_norm:
        logger.error("Configuration Mismatch!")
        import difflib
        diff = difflib.unified_diff(
            dut_norm.splitlines(), 
            baseline_norm.splitlines(), 
            fromfile='DUT', 
            tofile='Baseline', 
            lineterm=''
        )
        for line in diff:
            logger.error(line)
        return False
    logger.info("Configuration matches.")
        
    # 4. Visual Verification
    logger.info("Capturing screenshots...")
    dut_img = "/tmp/dut_voacap.bmp"
    baseline_img = "/tmp/baseline_voacap.bmp"
    diff_img = "/tmp/diff_voacap.png"
    
    dut.get_capture(dut_img)
    baseline.get_capture(baseline_img)
    
    logger.info("Comparing screenshots...")
    if not verifier.compare_images(baseline_img, dut_img, diff_img):
        logger.error(f"Visual mismatch! Diff saved to {diff_img}")
        return False
        
    logger.info("Visual verification successful.")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Complex Parity Verification")
    parser.add_argument("--scenario", default="voacap_pane1", help="Test scenario to run")
    args = parser.parse_args()
    
    # Initialize Clients
    dut = HamClockClient(f"http://localhost:{DUT_PORT}")
    baseline = HamClockClient(f"http://localhost:{BASELINE_PORT}")
    verifier = VisualVerifier()

    # Verify connection first
    logger.info("Checking connection to clients...")
    try:
        dut.get("get_config.txt")
        baseline.get("get_config.txt")
    except Exception as e:
        logger.error(f"Failed to connect to clients: {e}")
        logger.error("Ensure HamClock instances are running on ports %d and %d", DUT_PORT, BASELINE_PORT)
        sys.exit(1)
    
    success = False
    if args.scenario == "voacap_pane1":
        success = run_voacap_scenario(dut, baseline, verifier)
    else:
        logger.error(f"Unknown scenario: {args.scenario}")
        
    if success:
        logger.info("Test Scenario PASSED")
        sys.exit(0)
    else:
        logger.error("Test Scenario FAILED")
        sys.exit(1)
