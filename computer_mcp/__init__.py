"""Computer MCP - Cross-platform computer automation and control.

This module provides a stateless API for computer control.
"""

__version__ = "0.0.3"

from pynput.keyboard import Controller as KeyboardController
from pynput.mouse import Controller as MouseController

from computer_mcp.actions import (
    keyboard as keyboard_actions,
    mouse as mouse_actions,
    screenshot as screenshot_actions,
    window as window_actions,
    focused_app as focused_app_actions,
    accessibility_tree as accessibility_tree_actions,
    config as config_actions,
)

# Create default controllers
_default_mouse_controller = MouseController()
_default_keyboard_controller = KeyboardController()


# Mouse actions
def click(button: str = "left") -> dict:
    """Perform a mouse click at the current cursor position.
    
    Args:
        button: Mouse button ("left", "right", "middle")
    
    Returns:
        Dictionary with action result
    """
    return mouse_actions.click(button, _default_mouse_controller)


def double_click(button: str = "left") -> dict:
    """Perform a double mouse click at the current cursor position.
    
    Args:
        button: Mouse button ("left", "right", "middle")
    
    Returns:
        Dictionary with action result
    """
    return mouse_actions.double_click(button, _default_mouse_controller)


def triple_click(button: str = "left") -> dict:
    """Perform a triple mouse click at the current cursor position.
    
    Args:
        button: Mouse button ("left", "right", "middle")
    
    Returns:
        Dictionary with action result
    """
    return mouse_actions.triple_click(button, _default_mouse_controller)


def button_down(button: str = "left") -> dict:
    """Press and hold a mouse button.
    
    Args:
        button: Mouse button ("left", "right", "middle")
    
    Returns:
        Dictionary with action result
    """
    return mouse_actions.button_down(button, _default_mouse_controller)


def button_up(button: str = "left") -> dict:
    """Release a mouse button.
    
    Args:
        button: Mouse button ("left", "right", "middle")
    
    Returns:
        Dictionary with action result
    """
    return mouse_actions.button_up(button, _default_mouse_controller)


def drag(start: dict, end: dict, button: str = "left") -> dict:
    """Drag mouse from start to end position.
    
    Args:
        start: Start position with "x" and "y" keys
        end: End position with "x" and "y" keys
        button: Mouse button to use ("left", "right", "middle")
    
    Returns:
        Dictionary with action result
    """
    return mouse_actions.drag(start, end, button, _default_mouse_controller)


def move_mouse(x: int, y: int) -> dict:
    """Move the mouse cursor to specified coordinates.
    
    Args:
        x: X coordinate
        y: Y coordinate
    
    Returns:
        Dictionary with action result
    """
    return mouse_actions.move_mouse(x, y, _default_mouse_controller)


# Keyboard actions
def type_text(text: str) -> dict:
    """Type the specified text.
    
    Args:
        text: Text to type
    
    Returns:
        Dictionary with action result
    """
    return keyboard_actions.type_text(text, _default_keyboard_controller)


def key_down(key: str) -> dict:
    """Press and hold a key.
    
    Args:
        key: Key to press (e.g., 'ctrl', 'a', 'space')
    
    Returns:
        Dictionary with action result
    """
    return keyboard_actions.key_down(key, _default_keyboard_controller)


def key_up(key: str) -> dict:
    """Release a key.
    
    Args:
        key: Key to release (e.g., 'ctrl', 'a', 'space')
    
    Returns:
        Dictionary with action result
    """
    return keyboard_actions.key_up(key, _default_keyboard_controller)


def key_press(key: str) -> dict:
    """Press and release a key (convenience method).
    
    Args:
        key: Key to press and release (e.g., 'ctrl', 'a', 'space')
    
    Returns:
        Dictionary with action result
    """
    return keyboard_actions.key_press(key, _default_keyboard_controller)


# Screenshot actions
def get_screenshot() -> dict:
    """Capture a screenshot of the display.
    
    Returns:
        Dictionary with screenshot data (format, data, width, height) or error
    """
    return screenshot_actions.get_screenshot()


# Window actions (expose main functions)
def list_windows() -> dict:
    """List all visible windows.
    
    Returns:
        Dictionary with windows list
    """
    return window_actions.list_windows()


def switch_to_window(hwnd: int | None = None, title: str | None = None) -> dict:
    """Switch focus to a window by handle or title pattern.
    
    Args:
        hwnd: Window handle
        title: Window title pattern (alternative to hwnd)
    
    Returns:
        Dictionary with action result
    """
    return window_actions.switch_to_window(hwnd, title)


def move_window(hwnd: int, x: int, y: int, width: int | None = None, height: int | None = None) -> dict:
    """Move and/or resize a window.
    
    Args:
        hwnd: Window handle
        x: X coordinate
        y: Y coordinate
        width: Window width (optional)
        height: Window height (optional)
    
    Returns:
        Dictionary with action result
    """
    return window_actions.move_window(hwnd, x, y, width, height)


def resize_window(hwnd: int, width: int, height: int) -> dict:
    """Resize a window.
    
    Args:
        hwnd: Window handle
        width: Window width
        height: Window height
    
    Returns:
        Dictionary with action result
    """
    return window_actions.resize_window(hwnd, width, height)


def minimize_window(hwnd: int) -> dict:
    """Minimize a window.
    
    Args:
        hwnd: Window handle
    
    Returns:
        Dictionary with action result
    """
    return window_actions.minimize_window(hwnd)


def maximize_window(hwnd: int) -> dict:
    """Maximize a window.
    
    Args:
        hwnd: Window handle
    
    Returns:
        Dictionary with action result
    """
    return window_actions.maximize_window(hwnd)


def restore_window(hwnd: int) -> dict:
    """Restore a minimized or maximized window.
    
    Args:
        hwnd: Window handle
    
    Returns:
        Dictionary with action result
    """
    return window_actions.restore_window(hwnd)


def set_window_topmost(hwnd: int, topmost: bool = True) -> dict:
    """Set or remove a window's always-on-top property.
    
    Args:
        hwnd: Window handle
        topmost: Whether window should be always on top
    
    Returns:
        Dictionary with action result
    """
    return window_actions.set_window_topmost(hwnd, topmost)


def get_window_info(hwnd: int) -> dict:
    """Get detailed information about a window.
    
    Args:
        hwnd: Window handle
    
    Returns:
        Dictionary with window information
    """
    return window_actions.get_window_info(hwnd)


def close_window(hwnd: int) -> dict:
    """Close a window.
    
    Args:
        hwnd: Window handle
    
    Returns:
        Dictionary with action result
    """
    return window_actions.close_window(hwnd)


def snap_window_left(hwnd: int) -> dict:
    """Snap window to fill left half of screen.
    
    Args:
        hwnd: Window handle
    
    Returns:
        Dictionary with action result
    """
    return window_actions.snap_window_left(hwnd)


def snap_window_right(hwnd: int) -> dict:
    """Snap window to fill right half of screen.
    
    Args:
        hwnd: Window handle
    
    Returns:
        Dictionary with action result
    """
    return window_actions.snap_window_right(hwnd)


def snap_window_top(hwnd: int) -> dict:
    """Snap window to fill top half of screen.
    
    Args:
        hwnd: Window handle
    
    Returns:
        Dictionary with action result
    """
    return window_actions.snap_window_top(hwnd)


def snap_window_bottom(hwnd: int) -> dict:
    """Snap window to fill bottom half of screen.
    
    Args:
        hwnd: Window handle
    
    Returns:
        Dictionary with action result
    """
    return window_actions.snap_window_bottom(hwnd)


def screenshot_window(hwnd: int) -> dict:
    """Capture screenshot of a specific window.
    
    Args:
        hwnd: Window handle
    
    Returns:
        Dictionary with screenshot data
    """
    return window_actions.screenshot_window(hwnd)


def list_virtual_desktops() -> dict:
    """List all virtual desktops with their IDs and names.
    
    Returns:
        Dictionary with desktops list
    """
    return window_actions.list_virtual_desktops()


def switch_virtual_desktop(desktop_id: int | None = None, name: str | None = None) -> dict:
    """Switch to a virtual desktop by ID or name.
    
    Args:
        desktop_id: Virtual desktop ID (0-indexed)
        name: Virtual desktop name (alternative to desktop_id)
    
    Returns:
        Dictionary with action result
    """
    return window_actions.switch_virtual_desktop(desktop_id, name)


def move_window_to_virtual_desktop(hwnd: int, desktop_id: int) -> dict:
    """Move a window to a different virtual desktop.
    
    Args:
        hwnd: Window handle
        desktop_id: Target virtual desktop ID
    
    Returns:
        Dictionary with action result
    """
    return window_actions.move_window_to_virtual_desktop(hwnd, desktop_id)


# Focused app and accessibility
def get_focused_app() -> dict:
    """Get current focused application.
    
    Returns:
        Dictionary with focused app information
    """
    return focused_app_actions.get_focused_app()


def get_accessibility_tree() -> dict:
    """Get accessibility tree.
    
    Returns:
        Dictionary with accessibility tree data
    """
    return accessibility_tree_actions.get_accessibility_tree()


# Configuration
def set_config(**kwargs) -> dict:
    """Update configuration settings.
    
    Args:
        **kwargs: Configuration options (observe_screen, observe_mouse_position, etc.)
    
    Returns:
        Dictionary with updated configuration
    """
    return config_actions.set_config(**kwargs)
