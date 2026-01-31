import zlib
import os

def inspect_z(path):
    print(f"Inspecting {path}...")
    try:
        with open(path, 'rb') as f:
            data = f.read()
            decomp = zlib.decompress(data)
            print(f"  Decompressed size: {len(decomp)}")
            print(f"  Header (hex): {decomp[:54].hex()}")
            if decomp.startswith(b'BM'):
                # BMP header: offset 18 is width, 22 is height (both 4 bytes little endian)
                import struct
                width = struct.unpack('<I', decomp[18:22])[0]
                height = struct.unpack('<i', decomp[22:26])[0]
                bpp = struct.unpack('<H', decomp[28:30])[0]
                print(f"  BMP: {width}x{height}, {bpp}bpp")
    except Exception as e:
        print(f"  Error: {e}")

def inspect_voacap(path):
    print(f"Inspecting {path}...")
    try:
        with open(path, 'rb') as f:
            data = f.read()
            # The lengths reported by server are 50546 and 37692
            l1, l2 = 50546, 37692
            d1 = data[:l1]
            d2 = data[l1:l1+l2]
            print(f"  Total size: {len(data)}")
            print(f"  Chunk 1 size: {len(d1)}")
            print(f"  Chunk 2 size: {len(d2)}")
            
            # Try decompressing
            dec1 = zlib.decompress(d1)
            dec2 = zlib.decompress(d2)
            print(f"  Dec1 size: {len(dec1)}")
            print(f"  Dec2 size: {len(dec2)}")
            
            if dec1.startswith(b'BM'):
                import struct
                width = struct.unpack('<I', dec1[18:22])[0]
                height = struct.unpack('<i', dec1[22:26])[0]
                print(f"  BMP 1: {width}x{height}")
    except Exception as e:
        print(f"  Error: {e}")

if __name__ == "__main__":
    inspect_z('processed_data/sdo_sample.bmp.z')
    inspect_voacap('processed_data/voacap_area_sample.bin')
