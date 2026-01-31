import os
import requests
import subprocess
import zlib
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
    "170": "latest_1024_0171.jpg", # Fallback for 170
    "HMI": "latest_1024_HMII.jpg",
    "HMIB": "latest_1024_HMIB.jpg",
    "HMIIC": "latest_1024_HMIIC.jpg",
}

def get_sdo_image(path):
    """
    Fetches, processes, and returns a .bmp.z solar image.
    path: e.g. /SDO/latest_170_HMIB.bmp.z
    """
    filename = os.path.basename(path)
    
    # Extract wavelength/type
    wavelength = "171" # Default
    if "HMIB" in filename: wavelength = "HMIB"
    elif "HMIIC" in filename: wavelength = "HMIIC"
    elif "HMII" in filename: wavelength = "HMI"
    elif "171" in filename: wavelength = "171"
    elif "193" in filename: wavelength = "193"
    elif "211" in filename: wavelength = "211"
    elif "304" in filename: wavelength = "304"
    elif "170" in filename: wavelength = "171" # HamClock uses 170 for 171?

    sdo_filename = SDO_MAP.get(wavelength, "latest_1024_0171.jpg")
    cache_path = os.path.join(CACHE_DIR, f"{wavelength}.bmp.z")
    
    # Cache for 30 minutes
    if os.path.exists(cache_path) and (time.time() - os.path.getmtime(cache_path) < 1800):
        logger.debug(f"Serving SDO {wavelength} from cache")
        with open(cache_path, "rb") as f:
            return f.read()

    try:
        url = f"{SDO_BASE_URL}{sdo_filename}"
        logger.info(f"Fetching SDO image from {url}")
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        
        temp_jpg = os.path.join(CACHE_DIR, "temp.jpg")
        temp_bmp = os.path.join(CACHE_DIR, "temp.bmp")
        
        with open(temp_jpg, "wb") as f:
            f.write(resp.content)
            
        # Process with ImageMagick: Resize to 170x170, convert to 24bpp BMP
        # HamClock expects 170x170 24bpp.
        # magick temp.jpg -resize 170x170! -type truecolor BMP3:temp.bmp
        subprocess.run([
            "magick", temp_jpg, 
            "-resize", "170x170!", 
            "-type", "truecolor", 
            "BMP3:" + temp_bmp
        ], check=True)
        
        with open(temp_bmp, "rb") as f:
            bmp_data = f.read()
            
        # Compress with Zlib
        compressed = zlib.compress(bmp_data)
        
        with open(cache_path, "wb") as f:
            f.write(compressed)
            
        # Cleanup
        if os.path.exists(temp_jpg): os.remove(temp_jpg)
        if os.path.exists(temp_bmp): os.remove(temp_bmp)
        
        return compressed

    except Exception as e:
        logger.error(f"Error fetching SDO image: {e}")
        return None
