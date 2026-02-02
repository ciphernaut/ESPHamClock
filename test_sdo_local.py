import sys
import os
import zlib

# Add ingestion to path
sys.path.append(os.path.join(os.getcwd(), "ingestion"))
import sdo_service

test_files = [
    "f_211_193_171_170.bmp.z",
    "f_304_170.bmp.z",
    "f_171_170.bmp.z",
    "f_211_170.bmp.z",
    "f_193_170.bmp.z",
    "latest_170_HMIB.bmp.z",
    "latest_170_HMIIC.bmp.z"
]

for fn in test_files:
    print(f"Testing {fn}...")
    path = f"/SDO/{fn}"
    data = sdo_service.get_sdo_image(path)
    if data:
        print(f"  Success! Compressed size: {len(data)}")
        try:
            decomp = zlib.decompress(data)
            print(f"  Decompressed size: {len(decomp)}")
            print(f"  Magic: {decomp[:2].decode()}")
            if decomp.startswith(b'BM'):
                filesize = int.from_bytes(decomp[2:6], byteorder='little')
                print(f"  BMP Header Filesize: {filesize}")
                if len(decomp) == filesize:
                    print("  Filesize matches!")
                else:
                    print(f"  Filesize MISMATCH: {len(decomp)} vs {filesize}")
        except Exception as e:
            print(f"  Failed to decompress/parse: {e}")
    else:
        print("  FAILED to get image")
    print("-" * 20)
