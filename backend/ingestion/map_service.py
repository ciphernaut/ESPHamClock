import os
import re
import struct
import zlib
import numpy as np
import logging

logger = logging.getLogger(__name__)

# Base directory setup
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data", "processed_data")
MAPS_DIR = os.path.join(DATA_DIR, "maps")

if not os.path.exists(MAPS_DIR):
    os.makedirs(MAPS_DIR)

def create_bmp_565_header(w, h):
    """
    Creates a 16bpp RGB565 BMP header (BITMAPV4HEADER).
    """
    core_size = 14
    dib_size = 108
    hdr_len = core_size + dib_size
    
    # 16bpp aligned to 4 bytes per row
    row_bytes = ((16 * w + 31) // 32) * 4
    pix_bytes = row_bytes * h
    file_bytes = hdr_len + pix_bytes
    
    # BITMAPFILEHEADER
    header = bytearray(b'BM')
    header += struct.pack('<L', file_bytes)    # size
    header += struct.pack('<H', 0)             # res1
    header += struct.pack('<H', 0)             # res2
    header += struct.pack('<L', hdr_len)       # offset
    
    # BITMAPV4HEADER
    header += struct.pack('<L', dib_size)      # size
    header += struct.pack('<l', w)             # width
    header += struct.pack('<l', -h)            # height (negative for top-down)
    header += struct.pack('<H', 1)             # planes
    header += struct.pack('<H', 16)            # bpp
    header += struct.pack('<L', 3)             # compression (BI_BITFIELDS)
    header += struct.pack('<L', pix_bytes)     # image size
    header += struct.pack('<l', 0)             # hres
    header += struct.pack('<l', 0)             # vres
    header += struct.pack('<L', 0)             # ncolors
    header += struct.pack('<L', 0)             # nimportant
    
    # Masks
    header += struct.pack('<L', 0xF800)        # R mask
    header += struct.pack('<L', 0x07E0)        # G mask
    header += struct.pack('<L', 0x001F)        # B mask
    header += struct.pack('<L', 0x0000)        # A mask
    
    header += struct.pack('<L', 1)             # CSType (LCS_sRGB)
    header += bytearray(36)                    # Endpoints (unused)
    header += struct.pack('<L', 0)             # Gamma Red
    header += struct.pack('<L', 0)             # Gamma Green
    header += struct.pack('<L', 0)             # Gamma Blue
    
    return header

def ensure_map(rel_path):
    """
    Check if a map exists. If not, try to generate it by resizing a base map.
    rel_path expect like: maps/map-D-1320x660-Countries.bmp.z
    """
    # Check if we should even try
    if not rel_path.startswith("maps/"):
        return None

    filename = os.path.basename(rel_path)
    # Expected format: map-[Type]-[W]x[H]-[Style].bmp[.z]
    # e.g. map-D-1320x660-Countries.bmp.z
    match = re.match(r"map-([DN])-(\d+)x(\d+)-(.+)\.bmp(\.z)?", filename)
    
    if not match:
        return None
        
    m_type = match.group(1) # D or N
    width = int(match.group(2))
    height = int(match.group(3))
    style = match.group(4) # Countries or Terrain or DRAP etc.
    is_compressed = match.group(5) == ".z"
    
    # Identify Source Map (Base 660x330)
    # We currently only have Countries and Terrain at 660x330
    src_filename = f"map-{m_type}-660x330-{style}.bmp"
    src_path = os.path.join(DATA_DIR, src_filename)
        
    if not os.path.exists(src_path):
        logger.warning(f"Base map not found: {src_path}")
        return None
        
    target_path = os.path.join(DATA_DIR, rel_path)
    
    try:
        logger.info(f"Generating {filename} from {src_filename}...")
        
        with open(src_path, "rb") as f:
            # Skip header (122 bytes for our standard maps)
            # NOTE: If we use the new header format it might be bigger (138 bytes?).
            # But the existing ones are likely 122 or 138.
            # Let's read the whole thing and skip based on 'BM' and offset.
            raw = f.read()
            offset = struct.unpack_from('<L', raw, 10)[0]
            
            # Assuming 660x330 16bpp
            pixel_data = raw[offset:]
            # Ensure it matches expected size
            if len(pixel_data) != 660*330*2:
                # If size mismatch, fallback or fail.
                # It might be 660*330*2. Check if we have padding?
                # 660 * 2 = 1320 bytes, divisible by 4. No padding.
                pass

            data = np.frombuffer(pixel_data, dtype='<u2').reshape(330, 660)

        # Basic resizing logic
        # For integer multiples, repeat is fast and good for pixel art/maps
        # For non-integers, we might need scipy.ndimage.zoom or similar, but
        # standard numpy doesn't have image resize.
        # HamClock usually asks for 1320x660 (2x), 1600x960 (2.42x? maybe?), 2400x1440...
        # 
        # If we only support integer scaling for now:
        if width % 660 == 0 and height % 330 == 0:
            scale_x = width // 660
            scale_y = height // 330
            newdata = data.repeat(scale_y, axis=0).repeat(scale_x, axis=1)
        else:
            # Nearest neighbor for arbitrary size
            # Create grid of indices
            row_indices = (np.arange(height) * 330 // height).astype(int)
            col_indices = (np.arange(width) * 660 // width).astype(int)
            newdata = data[row_indices[:, None], col_indices]
            
        header = create_bmp_565_header(width, height)
        new_pixel_data = newdata.astype('<u2').tobytes()
        full_data = header + new_pixel_data
        
        final_data = zlib.compress(full_data) if is_compressed else full_data
        
        # Save to cache
        with open(target_path, "wb") as f:
            f.write(final_data)
            
        logger.info(f"Generated {target_path}")
        return target_path
        
    except Exception as e:
        logger.error(f"Failed to generate map {filename}: {e}", exc_info=True)
        return None
