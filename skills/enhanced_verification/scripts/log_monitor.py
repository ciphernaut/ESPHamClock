#!/usr/bin/env python3
"""
Log Monitor for Enhanced Verification Skill.
Tails and analyzes HamClock diagnostic logs.
"""

import time
import os
import logging
import select

logger = logging.getLogger(__name__)

class LogMonitor:
    def __init__(self, log_path):
        self.log_path = log_path
        self._f = None

    def start(self):
        """Open the log file and seek to the end."""
        try:
            self._f = open(self.log_path, 'r')
            self._f.seek(0, os.SEEK_END)
        except FileNotFoundError:
            logger.warning(f"Log file not found: {self.log_path}")

    def stop(self):
        if self._f:
            self._f.close()
            self._f = None

    def wait_for_pattern(self, pattern, timeout=5.0):
        """
        Wait for a specific string pattern to appear in new log lines.
        
        Args:
            pattern (str): The string to search for.
            timeout (float): Max time to wait in seconds.
            
        Returns:
            str: The matching line, or None if timeout.
        """
        if not self._f:
            self.start()
            if not self._f:
                return None

        start_time = time.time()
        while time.time() - start_time < timeout:
            line = self._f.readline()
            if line:
                if pattern in line:
                    return line.strip()
            else:
                time.sleep(0.1)
        
        return None

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: log_monitor.py <log_file>")
        sys.exit(1)
        
    mon = LogMonitor(sys.argv[1])
    print(f"Monitoring {sys.argv[1]}...")
    mon.start()
    found = mon.wait_for_pattern("error", timeout=10)
    if found:
        print(f"Found error: {found}")
    else:
        print("No error found in 10s")
