import re
import os

def clean_cty_file(input_path, output_path):
    with open(input_path, 'r') as f:
        lines = f.readlines()

    cleaned_lines = []
    for line in lines:
        if line.startswith('#') or not line.strip():
            cleaned_lines.append(line)
            continue
        
        # Split by whitespace
        parts = line.split()
        if len(parts) < 4:
            continue
            
        prefix = parts[0]
        # Remove everything after ( or [
        prefix = re.sub(r'[\(\[].*', '', prefix)
        
        # Limit prefix length to 11 (MAX_SPOTCALL_LEN - 1)
        prefix = prefix[:11]
        
        # Construct cleaned line: PREFIX LAT LON DXCC
        # Use simple spacing to ensure sscanf can parse it
        cleaned_line = f"{prefix:<10} {parts[1]:>8} {parts[2]:>8} {parts[3]:>4}\n"
        cleaned_lines.append(cleaned_line)

    with open(output_path, 'w') as f:
        f.writelines(cleaned_lines)

if __name__ == "__main__":
    base_dir = "/projects/antigravity/ESPHamClock/backend/data/processed_data"
    
    # Clean the one in the root of processed_data
    root_path = os.path.join(base_dir, "cty_wt_mod-ll-dxcc.txt")
    if os.path.exists(root_path):
        print(f"Cleaning {root_path}")
        clean_cty_file(root_path, root_path)
    
    # Clean the one in the cty subdirectory
    cty_dir_path = os.path.join(base_dir, "cty", "cty_wt_mod-ll-dxcc.txt")
    if os.path.exists(cty_dir_path):
        print(f"Cleaning {cty_dir_path}")
        clean_cty_file(cty_dir_path, cty_dir_path)
