import sys
import os
sys.path.append(os.path.join(os.getcwd(), "backend/ingestion"))
import sdo_service
import zlib

def test_sdo_gen():
    path = "/SDO/latest_170_HMIIC.bmp.z"
    print(f"Generating {path}...")
    data = sdo_service.get_sdo_image(path)
    if data:
        print(f"Generated {len(data)} bytes")
        with open("test_sdo.bmp.z", "wb") as f:
            f.write(data)
        
        # Decompress to check BMP header
        raw_bmp = zlib.decompress(data)
        print(f"Decompressed BMP size: {len(raw_bmp)} bytes")
        header = raw_bmp[:54]
        print(f"BMP Header: {header.hex()}")
        # Check specific fields
        print(f"Image Size field (34-37): {header[34:38].hex()}")
        print(f"Xperm field (38-41): {header[38:42].hex()}")
        print(f"Yperm field (42-45): {header[42:46].hex()}")
    else:
        print("Failed to generate image")

if __name__ == "__main__":
    test_sdo_gen()
