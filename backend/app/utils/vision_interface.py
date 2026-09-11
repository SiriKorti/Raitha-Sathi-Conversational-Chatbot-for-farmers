"""
vision_interface.py — Image Analysis Stub for Crop Disease Detection

WHAT IT DOES:
Provides a stub for future integration with Gemini Vision or other 
image recognition models. It accepts an image path and returns 
a basic diagnostic state update.

WHY IT EXISTS:
Farmers often can't describe symptoms accurately, but they can 
easily take a photo. This allows the system to extract `symptoms` 
and `affected_part` directly from an image.
"""

from typing import Dict, Any
from app.utils.logger import logger

class VisionInterface:
    def __init__(self):
        logger.info("VisionInterface stub initialised.")

    async def analyze_crop_image(self, image_path: str) -> Dict[str, Any]:
        """
        Stub method to analyze an uploaded crop image.
        
        Args:
            image_path: Path to the image file.
            
        Returns:
            Dictionary containing extracted diagnostic features.
        """
        logger.info(f"Mock analyzing image: {image_path}")
        
        # In the future, this would call Gemini 1.5 Pro Vision API
        # Example mock response:
        return {
            "crop_name": "Ragi",
            "symptoms": ["yellowing", "drying edges"],
            "affected_part": "lower leaves",
            "pest_visible": "No",
            "confidence": 0.85
        }
