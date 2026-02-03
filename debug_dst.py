import sys
import os

# Add ingestion to path
sys.path.append(os.path.join(os.getcwd(), "backend", "ingestion"))

from noaa_fetcher import fetch_dst

if __name__ == "__main__":
    fetch_dst()
