import os
import zlib
from ingestion import voacap_service

def check_map_stats(stream):
    # Decompress
    data = zlib.decompress(stream)
    # Header is 122 bytes
    pixels = data[122:]
    # Count unique colors (RGB565)
    unique_colors = set()
    for i in range(0, len(pixels), 2):
        color = pixels[i] | (pixels[i+1] << 8)
        unique_colors.add(color)
    return len(unique_colors)

def get_pixel_at(stream, x, y):
    data = zlib.decompress(stream)
    pixels = data[122:]
    offset = (y * voacap_service.MAP_W + x) * 2
    return pixels[offset] | (pixels[offset+1] << 8)

def test_voacap():
    print("Testing VOACAP Diversity...")
    # Map 1: Denver
    res1 = voacap_service.generate_voacap_response({'TXLAT': [40], 'TXLNG': [-105], 'MHZ': [0]})
    # Map 2: London
    res2 = voacap_service.generate_voacap_response({'TXLAT': [51], 'TXLNG': [0], 'MHZ': [0]})
    
    unique1 = check_map_stats(res1[0])
    unique2 = check_map_stats(res2[0])
    
    print(f"Denver map unique colors: {unique1}")
    print(f"London map unique colors: {unique2}")
    
    if unique1 < 10 or unique2 < 10:
        print("FAIL: Map is too solid!")
    else:
        print("PASS: Map has diversity.")
        
    p1 = get_pixel_at(res1[0], 330, 165) # Center of map
    p2 = get_pixel_at(res2[0], 330, 165)
    
    print(f"Pixel at (330, 165): Denver={p1}, London={p2}")
    if p1 != p2:
        print("PASS: Location changes the map.")
    else:
        print("FAIL: Location does NOT change the map (or identical at this point).")

if __name__ == "__main__":
    test_voacap()
