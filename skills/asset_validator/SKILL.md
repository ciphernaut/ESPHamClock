# Asset Validator Skill
This skill identifies and resolves integrity issues with binary data files in the HamClock stack.

## Overview
The skill provides tools to verify that binary assets (like VOACAP masks and SDO imagery) are valid, correctly formatted, and contain expected transparency data.

## Components
- `scripts/validate_assets.py`: Validates binary files based on type.

## Workflows

### 1. Verify VOACAP Mask
Check if a local VOACAP mask is valid:
```bash
python3 skills/asset_validator/scripts/validate_assets.py voacap_mask backend/data/processed_data/countries_mask.bin
```

## Guidelines for Agents
- ALWAYS validate binary assets after any modification to the map generation or SDO patching logic.
- Expand the `validate_assets.py` script as new binary formats are introduced.
