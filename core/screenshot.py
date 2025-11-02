"""Screenshot capture functionality."""

import base64
from io import BytesIO
from typing import Any

import mss
from PIL import Image


def capture_screenshot() -> dict[str, Any]:
    """Capture screenshot and return as base64-encoded PNG.
    
    Returns:
        Dictionary with format, data (base64), width, and height
    """
    with mss.mss() as sct:
        monitor = sct.monitors[1]  # Index 0 is all monitors, 1+ are individual
        screenshot = sct.grab(monitor)
        
        # Convert to PIL Image
        img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
        
        # Convert to base64
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        img_bytes = buffer.getvalue()
        img_base64 = base64.b64encode(img_bytes).decode("utf-8")
        
        return {
            "format": "base64_png",
            "data": img_base64,
            "width": screenshot.width,
            "height": screenshot.height
        }

