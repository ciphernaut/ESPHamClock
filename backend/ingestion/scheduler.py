import time
import subprocess
import os
import sys

# Path to the fetcher script
FETCH_SCRIPT = os.path.join(os.path.dirname(__file__), "noaa_fetcher.py")

def run_fetcher():
    print(f"[{time.ctime()}] Running NOAA fetcher...")
    try:
        # Run with current python interpreter
        subprocess.run([sys.executable, FETCH_SCRIPT], check=True)
        print(f"[{time.ctime()}] NOAA fetcher completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"[{time.ctime()}] Error running fetcher: {e}")

def main():
    # Initial fetch
    run_fetcher()
    
    # Run every 10 minutes (600 seconds)
    interval = 600
    print(f"Scheduler started. Will run every {interval} seconds.")
    
    try:
        while True:
            time.sleep(interval)
            run_fetcher()
    except KeyboardInterrupt:
        print("Scheduler stopped by user.")

if __name__ == "__main__":
    main()
