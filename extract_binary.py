import sys
import os

def extract_binary(input_file, output_file):
    with open(input_file, 'rb') as f:
        content = f.read()
    
    marker = b'\n--- DATA ---\n'
    idx = content.find(marker)
    if idx == -1:
        print("Marker not found")
        return False
    
    data = content[idx + len(marker):]
    with open(output_file, 'wb') as f:
        f.write(data)
    print(f"Extracted {len(data)} bytes to {output_file}")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 extract.py <input> <output>")
        sys.exit(1)
    extract_binary(sys.argv[1], sys.argv[2])
