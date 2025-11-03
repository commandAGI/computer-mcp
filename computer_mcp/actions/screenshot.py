"""Screenshot actions."""

from typing import Any

from computer_mcp.core.screenshot import capture_screenshot


def get_screenshot() -> dict[str, Any]:
    """Capture a screenshot of the display.
    
    Returns:
        Dictionary with screenshot data (format, data, width, height) or error
    """
    return capture_screenshot()

