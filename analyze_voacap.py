import sys
import zlib
import struct
import os

def analyze_binary(file_path):
    print(f"Analyzing: {file_path}")
    with open(file_path, "rb") as f:
        full_data = f.read()

    # HamClock captures often have a header (Path, Status, etc.)
    if b"--- DATA ---" in full_data:
        parts = full_data.split(b"--- DATA ---", 1)
        full_data = parts[1].lstrip()

    print(f"Full Data size: {len(full_data)}")

    offset = 0
    map_idx = 0
    while offset < len(full_data):
        try:
            # Try to find the start of a zlib stream (usually 0x78)
            # or just decompress if we are at the start
            d = zlib.decompressobj()
            decompressed = d.decompress(full_data[offset:])
            unused = d.unused_data
            
            consumed = len(full_data[offset:]) - len(unused)
            print(f"\nMap {map_idx}:")
            print(f"  Compressed consumed: {consumed}")
            print(f"  Decompressed size: {len(decompressed)}")
            
            if decompressed.startswith(b"BM"):
                print("  BMP Marker found")
                file_size, res1, res2, pix_offset = struct.unpack("<LHH L", decompressed[2:14])
                print(f"  BMP File Size: {file_size}")
                print(f"  Pixel Data Offset: {pix_offset}")
                
                w, h = struct.unpack("<ll", decompressed[18:26])
                print(f"  Dimensions: {w}x{h}")
                
                # Sample some pixels
                sample_count = 10
                if len(decompressed) >= pix_offset + sample_count * 2:
                    pixels = struct.unpack("<" + "H"*sample_count, decompressed[pix_offset:pix_offset+sample_count*2])
                    hex_pixels = [hex(p) for p in pixels]
                    print(f"  Sample Pixels (RGB565): {hex_pixels}")

            # Save decompressed
            out_name = f"{file_path}.map{map_idx}.decompressed"
            with open(out_name, "wb") as f_out:
                f_out.write(decompressed)
            
            offset += consumed
            map_idx += 1
            
            if not unused:
                break
        except Exception as e:
            print(f"Error at offset {offset}: {e}")
            break

if __name__ == "__main__":
    if len(sys.argv) > 1:
        analyze_binary(sys.argv[1])
    else:
        print("Usage: python3 analyze_voacap.py [file.bin]")
