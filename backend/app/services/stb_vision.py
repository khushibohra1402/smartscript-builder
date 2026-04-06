"""
STB Vision Service - HDMI Capture & Computer Vision
Handles frame capture, template matching, and OCR for Set-Top Box testing.
"""

import time
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from datetime import datetime
from loguru import logger

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    logger.warning("OpenCV not available - STB vision disabled")

try:
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    logger.warning("pytesseract not available - OCR disabled")


class STBVisionService:
    """
    Captures frames from HDMI input and performs vision-based analysis.
    
    Capabilities:
    - Frame capture from HDMI capture card
    - Template matching for UI element detection
    - OCR text extraction from screen regions
    """
    
    def __init__(self, hdmi_capture_index: int = 0):
        self.capture_index = hdmi_capture_index
        self.cap: Optional[Any] = None
        self._connected = False
    
    def connect(self, timeout: float = 10.0) -> bool:
        """Initialize connection to HDMI capture device."""
        if not CV2_AVAILABLE:
            logger.error("OpenCV not installed. Run: pip install opencv-python")
            return False
        
        start = time.time()
        while time.time() - start < timeout:
            try:
                self.cap = cv2.VideoCapture(self.capture_index)
                if self.cap.isOpened():
                    # Set capture resolution
                    self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
                    self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
                    self._connected = True
                    logger.info(f"HDMI capture connected on index {self.capture_index}")
                    return True
                self.cap.release()
            except Exception as e:
                logger.warning(f"HDMI capture attempt failed: {e}")
            time.sleep(1.0)
        
        logger.error(f"HDMI capture failed after {timeout}s on index {self.capture_index}")
        return False
    
    def get_frame(self, retries: int = 3) -> Optional[Any]:
        """
        Capture the latest frame from HDMI input.
        
        Returns:
            numpy array (BGR) or None on failure
        """
        if not self._connected or not self.cap:
            logger.error("HDMI capture not connected")
            return None
        
        for attempt in range(retries):
            ret, frame = self.cap.read()
            if ret and frame is not None:
                return frame
            logger.warning(f"Frame capture failed (attempt {attempt + 1}/{retries})")
            time.sleep(0.5)
        
        return None
    
    def find_template(
        self,
        template_path: str,
        threshold: float = 0.8,
        timeout: float = 10.0
    ) -> Optional[Tuple[int, int, float]]:
        """
        Find a template image on screen using template matching.
        
        Args:
            template_path: Path to template image file
            threshold: Matching confidence threshold (0-1)
            timeout: Max time to search in seconds
            
        Returns:
            (x, y, confidence) center coordinates if found, None otherwise
        """
        if not CV2_AVAILABLE:
            return None
        
        template = cv2.imread(template_path, cv2.IMREAD_COLOR)
        if template is None:
            logger.error(f"Template not found: {template_path}")
            return None
        
        start = time.time()
        while time.time() - start < timeout:
            frame = self.get_frame()
            if frame is None:
                continue
            
            result = cv2.matchTemplate(frame, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= threshold:
                h, w = template.shape[:2]
                center_x = max_loc[0] + w // 2
                center_y = max_loc[1] + h // 2
                logger.info(f"Template found at ({center_x}, {center_y}) conf={max_val:.3f}")
                return (center_x, center_y, float(max_val))
            
            time.sleep(0.5)
        
        logger.warning(f"Template not found within {timeout}s (best={max_val:.3f})")
        return None
    
    def extract_text(self, region: Optional[Tuple[int, int, int, int]] = None) -> str:
        """
        Extract text from the current screen using OCR.
        
        Args:
            region: Optional (x, y, width, height) crop region
            
        Returns:
            Extracted text string
        """
        if not OCR_AVAILABLE:
            logger.error("pytesseract not installed. Run: pip install pytesseract")
            return ""
        
        frame = self.get_frame()
        if frame is None:
            return ""
        
        if region:
            x, y, w, h = region
            frame = frame[y:y+h, x:x+w]
        
        # Convert to grayscale for better OCR
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # Apply threshold for cleaner text
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
        
        try:
            text = pytesseract.image_to_string(thresh)
            return text.strip()
        except Exception as e:
            logger.error(f"OCR failed: {e}")
            return ""
    
    def save_frame(self, output_path: str) -> bool:
        """Save the current frame as an image file."""
        frame = self.get_frame()
        if frame is None:
            return False
        
        try:
            cv2.imwrite(output_path, frame)
            logger.info(f"Frame saved to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save frame: {e}")
            return False
    
    def disconnect(self):
        """Release the capture device."""
        if self.cap:
            self.cap.release()
            self._connected = False
            logger.info("HDMI capture disconnected")
    
    def is_connected(self) -> bool:
        """Check if capture device is active."""
        return self._connected and self.cap is not None and self.cap.isOpened()
