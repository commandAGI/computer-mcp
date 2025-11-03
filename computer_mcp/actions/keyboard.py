"""Keyboard actions."""

from typing import Any

from pynput.keyboard import Controller

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

