import sys
import os
import time

print("Start debug script", flush=True)

try:
    print("Importing os...", flush=True)
    import os
    print("Importing time...", flush=True)
    import time
    print("Importing logging...", flush=True)
    import logging
    print("Importing numpy...", flush=True)
    import numpy as np
    print("Numpy imported.", flush=True)
except Exception as e:
    print(f"Basic imports failed: {e}", flush=True)
    sys.exit(1)

sys.path.append(os.path.join(os.path.dirname(__file__), 'ingestion'))
print(f"Sys path: {sys.path}", flush=True)

try:
    print("Attempting to import voacap_service...", flush=True)
    # create a dummy logger to suppress output if needed
    logging.basicConfig(level=logging.DEBUG)
    
    # Manually load the module spec to see where it is
    import importlib.util
    spec = importlib.util.find_spec("ingestion.voacap_service")
    if spec is None:
        # Try local import style
        spec = importlib.util.find_spec("voacap_service")
        
    print(f"Found spec: {spec}", flush=True)

    from ingestion import voacap_service
    print("Imported voacap_service successfully", flush=True)
except Exception as e:
    print(f"Failed to import voacap_service: {e}", flush=True)
    # Try direct import
    try:
        print("Trying direct import...", flush=True)
        import voacap_service
        print("Direct import successful", flush=True)
    except Exception as e2:
        print(f"Direct import failed too: {e2}", flush=True)

try:
    print("Attempting to import band_service...", flush=True)
    from ingestion import band_service
    print("Imported band_service successfully", flush=True)
except Exception as e:
    print(f"Failed to import band_service: {e}", flush=True)

print("Done.", flush=True)
