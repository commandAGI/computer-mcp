"""Mouse actions."""

import time
from typing import Any

from pynput.mouse import Button, Controller

from computer_mcp.core.utils import button_from_string


def click(button: str = "left", controller: Controller | None = None) -> dict[str, Any]:
    """Perform a mouse click.
    
    Args:
        button: Mouse button ("left", "right", "middle")
        controller: Mouse controller instance (creates one if None)
    
    Returns:
        Dictionary with action result
    """
    if controller is None:
        controller = Controller()
    
    btn = button_from_string(button)
    controller.click(btn)
    return {"success": True, "action": "click", "button": button}


def double_click(button: str = "left", controller: Controller | None = None) -> dict[str, Any]:
    """Perform a double mouse click.
    
    Args:
        button: Mouse button ("left", "right", "middle")
        controller: Mouse controller instance (creates one if None)
    
    Returns:
        Dictionary with action result
    """
    if controller is None:
        controller = Controller()
    
    btn = button_from_string(button)
    controller.click(btn, 2)
    return {"success": True, "action": "double_click", "button": button}


def triple_click(button: str = "left", controller: Controller | None = None) -> dict[str, Any]:
    """Perform a triple mouse click.
    
    Args:
        button: Mouse button ("left", "right", "middle")
        controller: Mouse controller instance (creates one if None)
    
    Returns:
        Dictionary with action result
    """
    if controller is None:
        controller = Controller()
    
    btn = button_from_string(button)
    controller.click(btn, 3)
    return {"success": True, "action": "triple_click", "button": button}


def button_down(button: str = "left", controller: Controller | None = None) -> dict[str, Any]:
    """Press and hold a mouse button.
    
    Args:
        button: Mouse button ("left", "right", "middle")
        controller: Mouse controller instance (creates one if None)
    
    Returns:
        Dictionary with action result
    """
    if controller is None:
        controller = Controller()
    
    btn = button_from_string(button)
    controller.press(btn)
    return {"success": True, "action": "button_down", "button": button}


def button_up(button: str = "left", controller: Controller | None = None) -> dict[str, Any]:
    """Release a mouse button.
    
    Args:
        button: Mouse button ("left", "right", "middle")
        controller: Mouse controller instance (creates one if None)
    
    Returns:
        Dictionary with action result
    """
    if controller is None:
        controller = Controller()
    
    btn = button_from_string(button)
    controller.release(btn)
    return {"success": True, "action": "button_up", "button": button}


def drag(start: dict[str, int], end: dict[str, int], button: str = "left", controller: Controller | None = None) -> dict[str, Any]:
    """Drag mouse from start to end position.
    
    Args:
        start: Start position with "x" and "y" keys
        end: End position with "x" and "y" keys
        button: Mouse button to use ("left", "right", "middle")
        controller: Mouse controller instance (creates one if None)
    
    Returns:
        Dictionary with action result
    """
    if controller is None:
        controller = Controller()
    
    btn = button_from_string(button)
    
    # Move to start, press button, move to end, release button
    controller.position = (start["x"], start["y"])
    controller.press(btn)
    time.sleep(0.01)  # Small delay
    controller.position = (end["x"], end["y"])
    time.sleep(0.01)
    controller.release(btn)
    
    return {"success": True, "action": "drag", "start": start, "end": end, "button": button}


def move_mouse(x: int, y: int, controller: Controller | None = None) -> dict[str, Any]:
    """Move the mouse cursor to specified coordinates.
    
    Args:
        x: X coordinate
        y: Y coordinate
        controller: Mouse controller instance (creates one if None)
    
    Returns:
        Dictionary with action result
    """
    if controller is None:
        controller = Controller()
    
    controller.position = (x, y)
    return {"success": True, "action": "mouse_move", "x": x, "y": y}

