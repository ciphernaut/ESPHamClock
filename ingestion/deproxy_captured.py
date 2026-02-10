import os
import re

CAPTURED_DIR = "captured_data"
PROCESSED_DIR = "processed_data"

def deproxy(filename, target_filename):
    print(f"De-proxying {filename} -> {target_filename}")
    captured_path = os.path.join(CAPTURED_DIR, filename)
    if not os.path.exists(captured_path):
        print(f"  Error: File {captured_path} not found. Skipping.")
        return
        
    with open(captured_path, "r") as f:
        content = f.read()
    
    # Split by --- DATA ---
    parts = content.split("--- DATA ---")
    if len(parts) < 2:
        print(f"  Warning: No DATA section found in {filename}")
        return
    
    data = parts[1].strip()
    
    # Ensure directory exists
    target_path = os.path.join(PROCESSED_DIR, target_filename)
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    
    with open(target_path, "w") as f:
        f.write(data)
    print(f"  Saved to {target_path}")

if __name__ == "__main__":
    # Mapping of latest captured files for key missing endpoints
    # Format: (captured_filename, processed_relative_path)
    mappings = [
        ("20260130_231056_ham_HamClock_worldwx_wx.txt.bin", "worldwx/wx.txt"),
        ("20260130_231013_ham_HamClock_dst_dst.txt.bin", "dst/dst.txt"),
        ("20260130_230913_ham_HamClock_aurora_aurora.txt.bin", "aurora/aurora.txt"),
        ("20260130_230843_ham_HamClock_ONTA_onta.txt.bin", "ONTA/onta.txt"),
        ("20260130_230502_ham_HamClock_dxpeds_dxpeditions.txt.bin", "dxpeds/dxpeditions.txt"),
        ("20260130_230113_ham_HamClock_NOAASpaceWX_rank2_coeffs.txt.bin", "NOAASpaceWX/rank2_coeffs.txt"),
        ("20260130_230032_ham_HamClock_drap_stats.txt.bin", "drap/stats.txt"),
        ("20260130_225305_ham_HamClock_cty_cty_wt_mod-ll-dxcc.txt.bin", "cty/cty_wt_mod-ll-dxcc.txt"),
        ("20260130_225232_ham_HamClock_contests_contests311.txt.bin", "contests/contests311.txt"),
        ("20260130_230614_ham_HamClock_solar-wind_swind-24hr.txt.bin", "solar-wind/swind-24hr.txt"),
        ("20260130_231343_ham_HamClock_ssn_ssn-31.txt.bin", "ssn/ssn-31.txt"),
        ("20260130_231413_ham_HamClock_xray_xray.txt.bin", "xray/xray.txt"),
        ("20260130_231213_ham_HamClock_geomag_kindex.txt.bin", "geomag/kindex.txt"),
        ("20260130_231143_ham_HamClock_solar-flux_solarflux-99.txt.bin", "solar-flux/solarflux-99.txt"),
        ("20260130_231313_ham_HamClock_NOAASpaceWX_noaaswx.txt.bin", "NOAASpaceWX/noaaswx.txt"),
        ("20260130_230813_ham_HamClock_Bz_Bz.txt.bin", "Bz/Bz.txt")
    ]
    
    for captured, processed in mappings:
        deproxy(captured, processed)
