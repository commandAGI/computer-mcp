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


def key_to_string(key) -> str:
    """Convert pynput Key or KeyCode to string representation.
    
    Args:
        key: pynput Key or KeyCode object
        
    Returns:
        String representation of the key
    """
    if isinstance(key, Key):
        # Handle special keys
        if key == Key.ctrl or key == Key.ctrl_l or key == Key.ctrl_r:
            return "ctrl"
        elif key == Key.alt or key == Key.alt_l or key == Key.alt_r:
            return "alt"
        elif key == Key.shift or key == Key.shift_l or key == Key.shift_r:
            return "shift"
        elif key == Key.cmd or key == Key.cmd_l or key == Key.cmd_r:
            return "cmd"
        elif hasattr(key, 'name'):
            return key.name.lower()
        else:
            return str(key).lower().replace('key.', '')
    elif isinstance(key, KeyCode):
        if key.char:
            return key.char.lower()
        else:
            # For keys without char, use vk code
            return f"<{key.vk}>"
    return str(key).lower()


def normalize_hotkey_string(hotkey: str) -> str:
    """Normalize a hotkey string for comparison.
    
    Args:
        hotkey: Hotkey string (e.g., "ctrl+c", "Alt+Shift+F4")
        
    Returns:
        Normalized hotkey string (lowercase, sorted modifiers)
    """
    parts = [p.strip().lower() for p in hotkey.split("+")]
    if len(parts) <= 1:
        return parts[0] if parts else ""
    
    # Separate modifiers from main key
    modifiers = []
    main_key = None
    
    modifier_keys = {"ctrl", "control", "alt", "shift", "cmd", "command", "win", "windows", "meta"}
    
    for part in parts:
        if part in modifier_keys:
            # Normalize modifier names
            if part in ("control",):
                modifiers.append("ctrl")
            elif part in ("command", "win", "windows", "meta"):
                modifiers.append("cmd")
            else:
                modifiers.append(part)
        else:
            main_key = part
    
    # Sort modifiers for consistent comparison
    modifier_order = ["ctrl", "alt", "shift", "cmd"]
    modifiers.sort(key=lambda x: modifier_order.index(x) if x in modifier_order else 999)
    
    if main_key:
        return "+".join(modifiers + [main_key])
    else:
        # Only modifiers, no main key
        return "+".join(modifiers)


def is_hotkey_disallowed(key_str: str, held_keys: set, disallowed_hotkeys: list[str]) -> bool:
    """Check if a hotkey combination is disallowed.
    
    Args:
        key_str: String representation of the key being pressed
        held_keys: Set of currently held pynput Key/KeyCode objects
        disallowed_hotkeys: List of disallowed hotkey strings (e.g., ["ctrl+c", "alt+f4"])
        
    Returns:
        True if the hotkey is disallowed, False otherwise
    """
    if not disallowed_hotkeys:
        return False
    
    # Convert held keys to strings
    held_key_strings = set()
    for key in held_keys:
        held_key_strings.add(key_to_string(key))
    
    # Build the hotkey string from held keys + current key
    modifier_keys = {"ctrl", "alt", "shift", "cmd"}
    modifiers = []
    main_key = None
    
    # Add modifiers from held keys
    for held_key_str in held_key_strings:
        if held_key_str in modifier_keys:
            modifiers.append(held_key_str)
    
    # Check if the current key is a modifier
    current_key_lower = key_str.lower().strip()
    if current_key_lower in modifier_keys:
        # If it's just a modifier, only check if modifier-only hotkeys are disallowed
        modifiers.append(current_key_lower)
    else:
        main_key = current_key_lower
    
    # Normalize the current hotkey
    if modifiers and main_key:
        # Sort modifiers and combine with main key
        sorted_modifiers = sorted(modifiers, key=lambda x: ["ctrl", "alt", "shift", "cmd"].index(x) if x in ["ctrl", "alt", "shift", "cmd"] else 999)
        current_hotkey = normalize_hotkey_string("+".join(sorted_modifiers + [main_key]))
    elif modifiers:
        sorted_modifiers = sorted(modifiers, key=lambda x: ["ctrl", "alt", "shift", "cmd"].index(x) if x in ["ctrl", "alt", "shift", "cmd"] else 999)
        current_hotkey = normalize_hotkey_string("+".join(sorted_modifiers))
    else:
        current_hotkey = normalize_hotkey_string(main_key or current_key_lower)
    
    # Check against disallowed hotkeys
    for disallowed in disallowed_hotkeys:
        normalized_disallowed = normalize_hotkey_string(disallowed)
        if normalized_disallowed == current_hotkey:
            return True
    
    return False


def _find_window_by_title(title_pattern: str) -> int | None:
    """Find window handle by title pattern (platform-specific)."""
    import sys
    
    if sys.platform == "win32":
        try:
            import win32gui
            
            def enum_callback(hwnd, windows):
                try:
                    if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
                        window_title = win32gui.GetWindowText(hwnd)
                        if title_pattern.lower() in window_title.lower():
                            windows.append(hwnd)
                except Exception:
                    pass
                return True
            
            windows = []
            win32gui.EnumWindows(enum_callback, windows)
            return windows[0] if windows else None
        except Exception:
            return None
    elif sys.platform == "darwin":
        try:
            import subprocess
            script = f'''
            tell application "System Events"
                repeat with proc in application processes
                    try
                        repeat with win in windows of proc
                            set winTitle to name of win
                            if "{title_pattern}" is in winTitle then
                                set winID to id of win
                                return winID
                            end if
                        end repeat
                    end try
                end repeat
            end tell
            '''
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=2,
                check=False
            )
            if result.returncode == 0:
                win_id_str = result.stdout.strip()
                if win_id_str and win_id_str.isdigit():
                    return int(win_id_str)
            return None
        except Exception:
            return None
    else:
        # Linux - use xdotool
        try:
            import subprocess
            result = subprocess.run(
                ["xdotool", "search", "--name", title_pattern],
                capture_output=True,
                text=True,
                timeout=2,
                check=False
            )
            if result.returncode == 0:
                win_ids = result.stdout.strip().split("\n")
                if win_ids and win_ids[0]:
                    return int(win_ids[0])
            return None
        except Exception:
            return None


def get_window_bounds(window_identifier: int | str) -> tuple[int, int, int, int] | None:
    """Get window bounds (left, top, right, bottom) from hwnd or title.
    
    Args:
        window_identifier: Window handle (int) or window title pattern (str)
        
    Returns:
        Tuple of (left, top, right, bottom) if found, None otherwise
    """
    import sys
    
    if isinstance(window_identifier, int):
        # Use hwnd directly
        hwnd = window_identifier
    else:
        # Find window by title pattern
        hwnd = _find_window_by_title(window_identifier)
        if hwnd is None:
            return None
    
    if sys.platform == "win32":
        try:
            import win32gui
            rect = win32gui.GetWindowRect(hwnd)
            return rect  # Returns (left, top, right, bottom)
        except Exception:
            return None
    elif sys.platform == "darwin":
        try:
            import subprocess
            script = f'''
            tell application "System Events"
                repeat with proc in application processes
                    try
                        set targetWindow to window id {hwnd} of proc
                        set winBounds to bounds of targetWindow
                        return winBounds
                    end try
                end repeat
            end tell
            '''
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=2,
                check=False
            )
            if result.returncode == 0:
                bounds_str = result.stdout.strip()
                bounds = [int(x.strip()) for x in bounds_str.replace("{", "").replace("}", "").split(",")]
                if len(bounds) >= 4:
                    # macOS bounds are (left, top, right, bottom)
                    return tuple(bounds[:4])
            return None
        except Exception:
            return None
    else:
        # Linux
        try:
            import subprocess
            # Get window geometry using xdotool
            result = subprocess.run(
                ["xdotool", "getwindowgeometry", str(hwnd)],
                capture_output=True,
                text=True,
                timeout=2,
                check=False
            )
            if result.returncode == 0:
                # Parse xdotool output to get position and size
                # Format: "Window 12345\n  Position: 100,200\n  Size: 800,600"
                lines = result.stdout.strip().split("\n")
                pos_line = [l for l in lines if "Position:" in l]
                size_line = [l for l in lines if "Size:" in l]
                if pos_line and size_line:
                    pos_str = pos_line[0].split("Position:")[1].strip()
                    size_str = size_line[0].split("Size:")[1].strip()
                    x, y = map(int, pos_str.split(","))
                    width, height = map(int, size_str.split("x"))
                    return (x, y, x + width, y + height)
            return None
        except Exception:
            return None


def constrain_mouse_coordinates(
    x: int, 
    y: int, 
    window_identifier: int | str | None
) -> tuple[int, int]:
    """Constrain mouse coordinates to window bounds.
    
    Args:
        x: X coordinate
        y: Y coordinate
        window_identifier: Window handle (int), title pattern (str), or None (no constraint)
        
    Returns:
        Tuple of (constrained_x, constrained_y)
    """
    if window_identifier is None:
        return (x, y)
    
    bounds = get_window_bounds(window_identifier)
    if bounds is None:
        # Window not found, return original coordinates but log warning?
        return (x, y)
    
    left, top, right, bottom = bounds
    
    # Clamp coordinates to window bounds
    constrained_x = max(left, min(right - 1, x))
    constrained_y = max(top, min(bottom - 1, y))
    
    return (constrained_x, constrained_y)


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

