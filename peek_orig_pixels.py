import struct
from collections import Counter

file_path = "local_voacap.bin.map0.decompressed"
try:
    with open(file_path, "rb") as f:
        f.seek(122)
        pixels = struct.unpack("<217800H", f.read(435600))
    
    print(f"Total pixels: {len(pixels)}")
    print(f"Non-zero: {sum(1 for p in pixels if p != 0)}")
    
    # Most common colors
    c = Counter(pixels)
    print("Most common colors:")
    for color, count in c.most_common(20):
        r = (color >> 11) & 0x1F
        g = (color >> 5) & 0x3F
        b = color & 0x1F
        print(f"  {hex(color)}: {count} pixels (RGB: {r},{g},{b})")

except Exception as e:
    print(f"Error: {e}")
