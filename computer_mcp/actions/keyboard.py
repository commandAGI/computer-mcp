"""Keyboard actions."""

from typing import Any

from pynput.keyboard import Controller, KeyCode

from computer_mcp.core.platform import IS_DARWIN, IS_LINUX, IS_WINDOWS
from computer_mcp.core.utils import key_from_string


def type_text(text: str, controller: Controller | None = None) -> dict[str, Any]:
    """Type the specified text.
    
    Args:
        text: Text to type
        controller: Keyboard controller instance (creates one if None)
    
    Returns:
        Dictionary with action result
    """
    if controller is None:
        controller = Controller()
    
    controller.type(text)
    return {"success": True, "action": "type", "text": text}


def key_down(key: str, controller: Controller | None = None) -> dict[str, Any]:
    """Press and hold a key.
    
    Args:
        key: Key to press (e.g., 'ctrl', 'a', 'space')
        controller: Keyboard controller instance (creates one if None)
    
    Returns:
        Dictionary with action result
    """
    if controller is None:
        controller = Controller()
    
    key_obj = key_from_string(key)
    controller.press(key_obj)
    return {"success": True, "action": "key_down", "key": key}


def key_up(key: str, controller: Controller | None = None) -> dict[str, Any]:
    """Release a key.
    
    Args:
        key: Key to release (e.g., 'ctrl', 'a', 'space')
        controller: Keyboard controller instance (creates one if None)
    
    Returns:
        Dictionary with action result
    """
    if controller is None:
        controller = Controller()
    
    key_obj = key_from_string(key)
    controller.release(key_obj)
    return {"success": True, "action": "key_up", "key": key}


def key_press(key: str, controller: Controller | None = None) -> dict[str, Any]:
    """Press and release a key (convenience method).
    
    Args:
        key: Key to press and release (e.g., 'ctrl', 'a', 'space')
        controller: Keyboard controller instance (creates one if None)
    
    Returns:
        Dictionary with action result
    """
    if controller is None:
        controller = Controller()
    
    key_obj = key_from_string(key)
    controller.press(key_obj)
    controller.release(key_obj)
    return {"success": True, "action": "key_press", "key": key}


# Window-targeted keyboard functions
if IS_WINDOWS:
    def type_text_to_window(text: str, hwnd: int) -> dict[str, Any]:
        """Type text to a specific window on Windows."""
        try:
            import win32gui
            import win32con
            import win32api
            
            if not win32gui.IsWindow(hwnd):
                return {"error": "Invalid window handle"}
            
            # Post WM_CHAR messages for each character
            for char in text:
                if char == '\n':
                    # Handle newline as Enter key
                    win32gui.PostMessage(hwnd, win32con.WM_KEYDOWN, win32con.VK_RETURN, 0)
                    win32gui.PostMessage(hwnd, win32con.WM_KEYUP, win32con.VK_RETURN, 0)
                else:
                    # Convert char to virtual key code if needed, or use WM_CHAR
                    vk = win32api.VkKeyScan(char)
                    if vk != -1:
                        # Low-order byte is the virtual key, high-order byte has shift state
                        vk_code = vk & 0xFF
                        shift_state = (vk >> 8) & 0xFF
                        
                        # Post WM_CHAR message for the character (handles Unicode properly)
                        win32gui.PostMessage(hwnd, win32con.WM_CHAR, ord(char), 0)
            
            return {"success": True, "action": "type", "text": text, "hwnd": hwnd}
        except ImportError:
            return {"error": "pywin32 not installed", "note": "Install pywin32 for Windows window keyboard support"}
        except Exception as e:
            return {"error": f"Failed to type to window: {str(e)}"}
    
    def key_down_to_window(key: str, hwnd: int) -> dict[str, Any]:
        """Press a key down to a specific window on Windows."""
        try:
            import win32gui
            import win32con
            from pynput.keyboard import Key
            
            if not win32gui.IsWindow(hwnd):
                return {"error": "Invalid window handle"}
            
            key_obj = key_from_string(key)
            
            # Map pynput keys to Windows virtual key codes
            vk_map = {
                Key.enter: win32con.VK_RETURN,
                Key.tab: win32con.VK_TAB,
                Key.space: win32con.VK_SPACE,
                Key.backspace: win32con.VK_BACK,
                Key.delete: win32con.VK_DELETE,
                Key.esc: win32con.VK_ESCAPE,
                Key.up: win32con.VK_UP,
                Key.down: win32con.VK_DOWN,
                Key.left: win32con.VK_LEFT,
                Key.right: win32con.VK_RIGHT,
                Key.ctrl: win32con.VK_CONTROL,
                Key.alt: win32con.VK_MENU,
                Key.shift: win32con.VK_SHIFT,
                Key.cmd: win32con.VK_LWIN,
            }
            
            if isinstance(key_obj, Key):
                vk = vk_map.get(key_obj)
                if vk is None:
                    return {"error": f"Key '{key}' not supported for window targeting"}
                win32gui.PostMessage(hwnd, win32con.WM_KEYDOWN, vk, 0)
            elif isinstance(key_obj, KeyCode) and key_obj.char:
                # Character key - use WM_CHAR for printable characters
                win32gui.PostMessage(hwnd, win32con.WM_CHAR, ord(key_obj.char), 0)
            else:
                return {"error": f"Key '{key}' not supported for window targeting"}
            
            return {"success": True, "action": "key_down", "key": key, "hwnd": hwnd}
        except ImportError:
            return {"error": "pywin32 not installed", "note": "Install pywin32 for Windows window keyboard support"}
        except Exception as e:
            return {"error": f"Failed to press key to window: {str(e)}"}
    
    def key_up_to_window(key: str, hwnd: int) -> dict[str, Any]:
        """Release a key to a specific window on Windows."""
        try:
            import win32gui
            import win32con
            from pynput.keyboard import Key
            
            if not win32gui.IsWindow(hwnd):
                return {"error": "Invalid window handle"}
            
            key_obj = key_from_string(key)
            
            # Map pynput keys to Windows virtual key codes
            vk_map = {
                Key.enter: win32con.VK_RETURN,
                Key.tab: win32con.VK_TAB,
                Key.space: win32con.VK_SPACE,
                Key.backspace: win32con.VK_BACK,
                Key.delete: win32con.VK_DELETE,
                Key.esc: win32con.VK_ESCAPE,
                Key.up: win32con.VK_UP,
                Key.down: win32con.VK_DOWN,
                Key.left: win32con.VK_LEFT,
                Key.right: win32con.VK_RIGHT,
                Key.ctrl: win32con.VK_CONTROL,
                Key.alt: win32con.VK_MENU,
                Key.shift: win32con.VK_SHIFT,
                Key.cmd: win32con.VK_LWIN,
            }
            
            if isinstance(key_obj, Key):
                vk = vk_map.get(key_obj)
                if vk is None:
                    return {"error": f"Key '{key}' not supported for window targeting"}
                win32gui.PostMessage(hwnd, win32con.WM_KEYUP, vk, 0)
            elif isinstance(key_obj, KeyCode) and key_obj.char:
                # For character keys, key_up is typically not needed (WM_CHAR handles it)
                # But we'll post it anyway for consistency
                pass
            else:
                return {"error": f"Key '{key}' not supported for window targeting"}
            
            return {"success": True, "action": "key_up", "key": key, "hwnd": hwnd}
        except ImportError:
            return {"error": "pywin32 not installed", "note": "Install pywin32 for Windows window keyboard support"}
        except Exception as e:
            return {"error": f"Failed to release key to window: {str(e)}"}
    
    def key_press_to_window(key: str, hwnd: int) -> dict[str, Any]:
        """Press and release a key to a specific window on Windows."""
        result_down = key_down_to_window(key, hwnd)
        if "error" in result_down:
            return result_down
        result_up = key_up_to_window(key, hwnd)
        if "error" in result_up:
            return result_up
        return {"success": True, "action": "key_press", "key": key, "hwnd": hwnd}

elif IS_DARWIN:
    def type_text_to_window(text: str, window_id: int) -> dict[str, Any]:
        """Type text to a specific window on macOS."""
        try:
            import subprocess
            
            # Escape text for AppleScript
            escaped_text = text.replace('\\', '\\\\').replace('"', '\\"')
            
            script = f'''
            tell application "System Events"
                repeat with proc in application processes
                    try
                        set targetWindow to window id {window_id} of proc
                        set frontmost of proc to true
                        set frontmost of targetWindow to true
                        keystroke "{escaped_text}"
                        exit repeat
                    end try
                end repeat
            end tell
            '''
            
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=5,
                check=False
            )
            
            if result.returncode == 0:
                return {"success": True, "action": "type", "text": text, "window_id": window_id}
            else:
                return {"error": f"Failed to type to window: {result.stderr}"}
        except Exception as e:
            return {"error": f"Failed to type to window: {str(e)}"}
    
    def key_down_to_window(key: str, window_id: int) -> dict[str, Any]:
        """Press a key down to a specific window on macOS."""
        try:
            import subprocess
            
            # Map key names to AppleScript key codes
            key_map = {
                "enter": "return",
                "return": "return",
                "tab": "tab",
                "space": "space",
                "backspace": "delete",
                "delete": "delete",
                "esc": "escape",
                "escape": "escape",
                "up": "up arrow",
                "down": "down arrow",
                "left": "left arrow",
                "right": "right arrow",
            }
            
            key_name = key_map.get(key.lower(), key.lower())
            # Quote key name if it contains spaces (like "up arrow")
            if " " in key_name:
                key_name_script = f'"{key_name}"'
            else:
                key_name_script = key_name
            
            script = f'''
            tell application "System Events"
                repeat with proc in application processes
                    try
                        set targetWindow to window id {window_id} of proc
                        set frontmost of proc to true
                        set frontmost of targetWindow to true
                        key down {key_name_script}
                        exit repeat
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
                return {"success": True, "action": "key_down", "key": key, "window_id": window_id}
            else:
                return {"error": f"Failed to press key to window: {result.stderr}"}
        except Exception as e:
            return {"error": f"Failed to press key to window: {str(e)}"}
    
    def key_up_to_window(key: str, window_id: int) -> dict[str, Any]:
        """Release a key to a specific window on macOS."""
        try:
            import subprocess
            
            # Map key names to AppleScript key codes
            key_map = {
                "enter": "return",
                "return": "return",
                "tab": "tab",
                "space": "space",
                "backspace": "delete",
                "delete": "delete",
                "esc": "escape",
                "escape": "escape",
                "up": "up arrow",
                "down": "down arrow",
                "left": "left arrow",
                "right": "right arrow",
            }
            
            key_name = key_map.get(key.lower(), key.lower())
            # Quote key name if it contains spaces (like "up arrow")
            if " " in key_name:
                key_name_script = f'"{key_name}"'
            else:
                key_name_script = key_name
            
            script = f'''
            tell application "System Events"
                repeat with proc in application processes
                    try
                        set targetWindow to window id {window_id} of proc
                        set frontmost of proc to true
                        set frontmost of targetWindow to true
                        key up {key_name_script}
                        exit repeat
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
                return {"success": True, "action": "key_up", "key": key, "window_id": window_id}
            else:
                return {"error": f"Failed to release key to window: {result.stderr}"}
        except Exception as e:
            return {"error": f"Failed to release key to window: {str(e)}"}
    
    def key_press_to_window(key: str, window_id: int) -> dict[str, Any]:
        """Press and release a key to a specific window on macOS."""
        try:
            import subprocess
            
            # Map key names to AppleScript key codes
            key_map = {
                "enter": "return",
                "return": "return",
                "tab": "tab",
                "space": "space",
                "backspace": "delete",
                "delete": "delete",
                "esc": "escape",
                "escape": "escape",
                "up": "up arrow",
                "down": "down arrow",
                "left": "left arrow",
                "right": "right arrow",
            }
            
            key_name = key_map.get(key.lower(), key.lower())
            # Quote key name if it contains spaces (like "up arrow")
            if " " in key_name:
                key_name_script = f'"{key_name}"'
            else:
                key_name_script = key_name
            
            script = f'''
            tell application "System Events"
                repeat with proc in application processes
                    try
                        set targetWindow to window id {window_id} of proc
                        set frontmost of proc to true
                        set frontmost of targetWindow to true
                        keystroke {key_name_script}
                        exit repeat
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
                return {"success": True, "action": "key_press", "key": key, "window_id": window_id}
            else:
                return {"error": f"Failed to press key to window: {result.stderr}"}
        except Exception as e:
            return {"error": f"Failed to press key to window: {str(e)}"}

elif IS_LINUX:
    def type_text_to_window(text: str, window_id: int) -> dict[str, Any]:
        """Type text to a specific window on Linux."""
        try:
            import subprocess
            
            # Activate window first
            subprocess.run(
                ["xdotool", "windowactivate", str(window_id)],
                capture_output=True,
                timeout=1,
                check=False
            )
            
            # Type text
            subprocess.run(
                ["xdotool", "type", "--window", str(window_id), text],
                capture_output=True,
                timeout=5,
                check=False
            )
            
            return {"success": True, "action": "type", "text": text, "window_id": window_id}
        except FileNotFoundError:
            return {"error": "xdotool not installed", "note": "Install xdotool: sudo apt install xdotool"}
        except Exception as e:
            return {"error": f"Failed to type to window: {str(e)}"}
    
    def key_down_to_window(key: str, window_id: int) -> dict[str, Any]:
        """Press a key down to a specific window on Linux."""
        try:
            import subprocess
            
            # Activate window first
            subprocess.run(
                ["xdotool", "windowactivate", str(window_id)],
                capture_output=True,
                timeout=1,
                check=False
            )
            
            # Key down
            subprocess.run(
                ["xdotool", "keydown", "--window", str(window_id), key],
                capture_output=True,
                timeout=1,
                check=False
            )
            
            return {"success": True, "action": "key_down", "key": key, "window_id": window_id}
        except FileNotFoundError:
            return {"error": "xdotool not installed", "note": "Install xdotool: sudo apt install xdotool"}
        except Exception as e:
            return {"error": f"Failed to press key to window: {str(e)}"}
    
    def key_up_to_window(key: str, window_id: int) -> dict[str, Any]:
        """Release a key to a specific window on Linux."""
        try:
            import subprocess
            
            # Activate window first
            subprocess.run(
                ["xdotool", "windowactivate", str(window_id)],
                capture_output=True,
                timeout=1,
                check=False
            )
            
            # Key up
            subprocess.run(
                ["xdotool", "keyup", "--window", str(window_id), key],
                capture_output=True,
                timeout=1,
                check=False
            )
            
            return {"success": True, "action": "key_up", "key": key, "window_id": window_id}
        except FileNotFoundError:
            return {"error": "xdotool not installed", "note": "Install xdotool: sudo apt install xdotool"}
        except Exception as e:
            return {"error": f"Failed to release key to window: {str(e)}"}
    
    def key_press_to_window(key: str, window_id: int) -> dict[str, Any]:
        """Press and release a key to a specific window on Linux."""
        try:
            import subprocess
            
            # Activate window first
            subprocess.run(
                ["xdotool", "windowactivate", str(window_id)],
                capture_output=True,
                timeout=1,
                check=False
            )
            
            # Key press
            subprocess.run(
                ["xdotool", "key", "--window", str(window_id), key],
                capture_output=True,
                timeout=1,
                check=False
            )
            
            return {"success": True, "action": "key_press", "key": key, "window_id": window_id}
        except FileNotFoundError:
            return {"error": "xdotool not installed", "note": "Install xdotool: sudo apt install xdotool"}
        except Exception as e:
            return {"error": f"Failed to press key to window: {str(e)}"}

else:
    # Unsupported platform
    def type_text_to_window(text: str, window_id: int) -> dict[str, Any]:
        import platform
        return {"error": f"Window keyboard targeting not supported on {platform.system()}"}
    
    def key_down_to_window(key: str, window_id: int) -> dict[str, Any]:
        import platform
        return {"error": f"Window keyboard targeting not supported on {platform.system()}"}
    
    def key_up_to_window(key: str, window_id: int) -> dict[str, Any]:
        import platform
        return {"error": f"Window keyboard targeting not supported on {platform.system()}"}
    
    def key_press_to_window(key: str, window_id: int) -> dict[str, Any]:
        import platform
        return {"error": f"Window keyboard targeting not supported on {platform.system()}"}

