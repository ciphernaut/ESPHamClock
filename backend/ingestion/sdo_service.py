import os
import requests
import subprocess
import zlib
import re
import logging
import time

logger = logging.getLogger(__name__)

SDO_BASE_URL = "https://sdo.gsfc.nasa.gov/assets/img/latest/"
CACHE_DIR = "/tmp/sdo_cache"

if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

# Mapping from HamClock filename patterns to SDO wavelengths
SDO_MAP = {
    "171": "latest_1024_0171.jpg",
    "193": "latest_1024_0193.jpg",
    "211": "latest_1024_0211.jpg",
    "304": "latest_1024_0304.jpg",
    "131": "latest_1024_0131.jpg",
    "1600": "latest_1024_1600.jpg",
    "1700": "latest_1024_1700.jpg",
    "170": "latest_1024_0171.jpg", # Fallback for 170
    "HMIB": "latest_1024_HMIB.jpg",
    "HMIIC": "latest_1024_HMIIC.jpg",
    "HMI": "latest_1024_HMIIC.jpg", # Map generic HMI to Intensity Continuum
    "211193171": "latest_1024_211193171.jpg",
}

def get_sdo_image(path):
    """
    Fetches and processes an SDO image based on the requested filename.
    Filenames like f_304_170.bmp or latest_170_HMIIC.bmp.z
    """
    filename = os.path.basename(path)
    
    # 1. Determine resolution
    # Resolutions: 170, 340, 510, 680
    resolution = 170
    res_match = re.search(r'(170|340|510|680)', filename)
    if res_match:
        resolution = int(res_match.group(1))
        
    # 2. Determine wavelength
    wavelength = "171" # Default
    if "211_193_171" in filename or "211193171" in filename: wavelength = "211193171"
    elif "HMIB" in filename: wavelength = "HMIB"
    elif "HMIIC" in filename: wavelength = "HMIIC"
    elif "HMI" in filename: wavelength = "HMI"
    elif "131" in filename: wavelength = "131"
    elif "304" in filename: wavelength = "304"
    elif "193" in filename: wavelength = "193"
    elif "211" in filename: wavelength = "211"
    elif "171" in filename: wavelength = "171"
    elif "1600" in filename: wavelength = "1600"
    elif "1700" in filename: wavelength = "1700"

    sdo_filename = SDO_MAP.get(wavelength, "latest_1024_0171.jpg")
    cache_id = f"{wavelength}_{resolution}"
    cache_path = os.path.join(CACHE_DIR, f"{cache_id}.bmp.z")

    # Check cache (30 mins)
    if os.path.exists(cache_path):
        if time.time() - os.path.getmtime(cache_path) < 1800:
            logger.debug(f"Serving SDO {cache_id} from cache")
            with open(cache_path, "rb") as f:
                return f.read()

    logger.info(f"Fetching fresh SDO image for {wavelength} at {resolution}x{resolution}")
    img_url = f"https://sdo.gsfc.nasa.gov/assets/img/latest/{sdo_filename}"
    
    try:
        resp = requests.get(img_url, timeout=15)
        resp.raise_for_status()
        
        # Process using ImageMagick
        # Use PID in temp filenames to avoid race conditions between threaded requests
        pid = os.getpid()
        temp_jpg = f"/tmp/sdo_{wavelength}_{pid}.jpg"
        temp_bmp = f"/tmp/sdo_{wavelength}_{pid}.bmp"
        
        with open(temp_jpg, "wb") as f:
            f.write(resp.content)
            
        # Resize to requested resolution and convert to BMP 24bpp (truecolor)
        # Force BMP3 to ensure compatibility with HamClock's bmp.cpp
        # Use -strip to remove metadata/profiles
        res_str = f"{resolution}x{resolution}!"
        try:
            subprocess.run(["magick", temp_jpg, "-strip", "-colorspace", "sRGB", "-filter", "Mitchell", "-resize", res_str, "-type", "truecolor", f"BMP3:{temp_bmp}"], 
                           check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Magick failed: {e.stderr}")
            raise
        
        with open(temp_bmp, "rb") as f:
            bmp_data = bytearray(f.read())
            
        # Patch BMP header for perfect parity:
        # Original has 0 for Image Size (34-37), Xppm (38-41), and Yppm (42-45)
        if len(bmp_data) >= 54:
            bmp_data[34:46] = b'\x00' * 12

        # Compress with level 6 (standard) as it matched HMIIC closely
        compressed = zlib.compress(bmp_data, level=6)
        
        # Save to cache
        with open(cache_path, "wb") as f:
            f.write(compressed)
            
        # Cleanup temp files
        if os.path.exists(temp_jpg): os.remove(temp_jpg)
        if os.path.exists(temp_bmp): os.remove(temp_bmp)
            
        return compressed
    except Exception as e:
        logger.error(f"Error processing SDO image {wavelength}: {e}")
        return None
