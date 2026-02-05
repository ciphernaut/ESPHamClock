import re
import os

def clean(line):
    if line.startswith('#') or not line.strip():
        return line
    parts = line.split()
    if len(parts) < 4:
        return line
    prefix = re.sub(r'[\(\[].*', '', parts[0])
    # Strictly limit to 10 characters as per client sscanf %10s
    prefix = prefix[:10]
    return f"{prefix:<10} {parts[1]:>8} {parts[2]:>8} {parts[3]:>4}\n"

input_files = [
    "/projects/antigravity/ESPHamClock/backend/data/processed_data/cty_wt_mod-ll-dxcc.txt",
    "/projects/antigravity/ESPHamClock/backend/data/processed_data/cty/cty_wt_mod-ll-dxcc.txt"
]

for file_path in input_files:
    if os.path.exists(file_path):
        print(f"Reading {file_path}")
        with open(file_path, 'r') as f:
            lines = f.readlines()
        print(f"Read {len(lines)} lines")
        cleaned_lines = [clean(l) for l in lines]
        with open(file_path + ".tmp", 'w') as f:
            f.writelines(cleaned_lines)
        os.rename(file_path + ".tmp", file_path)
        print(f"Updated {file_path}")
