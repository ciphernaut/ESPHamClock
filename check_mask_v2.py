import struct
import os

mask_path = "/projects/antigravity/ESPHamClock/backend/data/countries_mask.bin"
if not os.path.exists(mask_path):
    print("Mask file not found")
else:
    with open(mask_path, "rb") as f:
        data = f.read()
    print(f"File size: {len(data)}")
    # Read as uint16
    pixels = struct.unpack(f"<{len(data)//2}H", data)
    non_zero = sum(1 for p in pixels if p != 0)
    print(f"Non-zero pixels: {non_zero}")
    print(f"Total pixels: {len(pixels)}")
    if len(pixels) > 0:
        print(f"First 10 pixels: {pixels[:10]}")
    # Sample some middle pixels
    if len(pixels) > 100000:
        print(f"Sample pixels @ 100k: {pixels[100000:100010]}")
