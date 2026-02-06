import numpy as np
import os

mask_path = "/projects/antigravity/ESPHamClock/backend/data/countries_mask.bin"
if not os.path.exists(mask_path):
    print("Mask file not found")
else:
    mask = np.frombuffer(open(mask_path, "rb").read(), dtype=np.uint16)
    print(f"Mask size: {mask.size}")
    print(f"Non-zero pixels: {np.count_nonzero(mask)}")
    print(f"Total possible: {660*330}")
    print(f"Unique values: {np.unique(mask)}")
