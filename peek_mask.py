import struct

mask_path = "/projects/antigravity/ESPHamClock/backend/data/countries_mask.bin"
with open(mask_path, "rb") as f:
    data = f.read()

# Read first 1000 pixels
pixels = struct.unpack(f"<{min(len(data)//2, 1000)}H", data[:2000])
print(f"Sample pixels: {pixels[:100]}")
print(f"Non-zero in sample: {sum(1 for p in pixels if p != 0)}")
