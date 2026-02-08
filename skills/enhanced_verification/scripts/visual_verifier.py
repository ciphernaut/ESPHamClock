#!/usr/bin/env python3
"""
Visual Verifier for Enhanced Verification Skill.
Compares BMP images to detect visual discrepancies between HamClock instances.
"""

import sys
import logging
from PIL import Image, ImageChops

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VisualVerifier:
    def __init__(self, diff_threshold=0):
        """
        Initialize the Visual Verifier.
        
        Args:
            diff_threshold (int): Pixel difference threshold to consider a failure (0 = exact match).
        """
        self.diff_threshold = diff_threshold

    def compare_images(self, img1_path, img2_path, diff_output_path=None):
        """
        Compare two images and report differences.
        
        Args:
            img1_path (str): Path to first image (e.g., baseline).
            img2_path (str): Path to second image (e.g., test).
            diff_output_path (str): Optional path to save the difference image.
            
        Returns:
            bool: True if images match within threshold, False otherwise.
        """
        try:
            img1 = Image.open(img1_path).convert('RGB')
            img2 = Image.open(img2_path).convert('RGB')
        except Exception as e:
            logger.error(f"Failed to open images: {e}")
            return False

        # Check dimensions
        if img1.size != img2.size:
            logger.error(f"Image dimensions do not match: {img1.size} vs {img2.size}")
            return False

        # Compute difference
        diff = ImageChops.difference(img1, img2)
        
        # Calculate bounding box of non-zero difference
        bbox = diff.getbbox()
        
        if bbox:
            logger.warning(f"Images differ! Bounding box of difference: {bbox}")
            if diff_output_path:
                diff.save(diff_output_path)
                logger.info(f"Saved difference image to {diff_output_path}")
            return False
            
        logger.info("Images are identical.")
        return True

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Visual Verifier")
    parser.add_argument("image1", help="Path to first image (baseline)")
    parser.add_argument("image2", help="Path to second image (test)")
    parser.add_argument("--diff-out", help="Path to save difference image if failure")
    
    args = parser.parse_args()
    
    verifier = VisualVerifier()
    success = verifier.compare_images(args.image1, args.image2, args.diff_out)
    
    if not success:
        sys.exit(1)
