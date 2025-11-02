"""Utility functions."""

from typing import Any, Optional

from mcp.types import ImageContent
from pynput.keyboard import Key, KeyCode
from pynput.mouse import Button


def key_from_string(key_str: str):
    """Convert string key name to pynput Key or KeyCode."""
    key_str = key_str.lower().strip()
    
    key_map = {
        "ctrl": Key.ctrl, "control": Key.ctrl,
        "alt": Key.alt,
        "shift": Key.shift,
        "cmd": Key.cmd, "command": Key.cmd, "win": Key.cmd, "windows": Key.cmd, "meta": Key.cmd,
        "space": Key.space,
        "enter": Key.enter, "return": Key.enter,
        "tab": Key.tab,
        "esc": Key.esc, "escape": Key.esc,
        "backspace": Key.backspace,
        "delete": Key.delete,
        "up": Key.up, "down": Key.down, "left": Key.left, "right": Key.right,
        "pageup": Key.page_up, "pagedown": Key.page_down,
        "home": Key.home, "end": Key.end, "insert": Key.insert,
        "f1": Key.f1, "f2": Key.f2, "f3": Key.f3, "f4": Key.f4,
        "f5": Key.f5, "f6": Key.f6, "f7": Key.f7, "f8": Key.f8,
        "f9": Key.f9, "f10": Key.f10, "f11": Key.f11, "f12": Key.f12,
    }
    
    if key_str in key_map:
        return key_map[key_str]
    
    if len(key_str) == 1:
        return KeyCode.from_char(key_str)
    
    return KeyCode.from_vk(int(key_str)) if key_str.isdigit() else key_str


def button_from_string(button_str: str) -> Button:
    """Convert string button name to pynput Button."""
    button_str = button_str.lower().strip()
    if button_str in ["left", "1"]:
        return Button.left
    elif button_str in ["right", "2"]:
        return Button.right
    elif button_str in ["middle", "3"]:
        return Button.middle
    else:
        return Button.left


def screenshot_to_image_content(screenshot_data: dict[str, Any]) -> Optional[ImageContent]:
    """Convert screenshot data dictionary to MCP ImageContent.
    
    Args:
        screenshot_data: Dictionary with 'format', 'data' (base64), 'width', 'height'
        
    Returns:
        ImageContent if screenshot data is valid, None otherwise
    """
    if not screenshot_data or "error" in screenshot_data:
        return None
    
    # Extract base64 data (with or without data URI prefix)
    data = screenshot_data.get("data", "")
    if not data:
        return None
    
    # Remove data URI prefix if present (data:image/png;base64,)
    if data.startswith("data:image"):
        data = data.split(",", 1)[1]
    
    # Determine MIME type from format or default to PNG
    format_str = screenshot_data.get("format", "base64_png").lower()
    if "png" in format_str:
        mime_type = "image/png"
    elif "jpeg" in format_str or "jpg" in format_str:
        mime_type = "image/jpeg"
    else:
        mime_type = "image/png"  # Default to PNG
    
    return ImageContent(
        type="image",
        data=data,
        mimeType=mime_type
    )

