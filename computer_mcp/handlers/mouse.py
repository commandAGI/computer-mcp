"""Mouse action handlers."""

import time
from typing import Any, Union

from mcp.types import ImageContent, TextContent

from computer_mcp.core.response import format_response
from computer_mcp.core.state import ComputerState
from computer_mcp.core.utils import button_from_string


def handle_click(
    arguments: dict[str, Any],
    state: ComputerState,
    mouse_controller
) -> list[Union[TextContent, ImageContent]]:
    """Handle click action."""
    button = button_from_string(arguments.get("button", "left"))
    mouse_controller.click(button)
    result = {"success": True, "action": "click", "button": arguments.get("button", "left")}
    return format_response(result, state)


def handle_double_click(
    arguments: dict[str, Any],
    state: ComputerState,
    mouse_controller
) -> list[Union[TextContent, ImageContent]]:
    """Handle double_click action."""
    button = button_from_string(arguments.get("button", "left"))
    mouse_controller.click(button, 2)
    result = {"success": True, "action": "double_click", "button": arguments.get("button", "left")}
    return format_response(result, state)


def handle_triple_click(
    arguments: dict[str, Any],
    state: ComputerState,
    mouse_controller
) -> list[Union[TextContent, ImageContent]]:
    """Handle triple_click action."""
    button = button_from_string(arguments.get("button", "left"))
    mouse_controller.click(button, 3)
    result = {"success": True, "action": "triple_click", "button": arguments.get("button", "left")}
    return format_response(result, state)


def handle_button_down(
    arguments: dict[str, Any],
    state: ComputerState,
    mouse_controller
) -> list[Union[TextContent, ImageContent]]:
    """Handle button_down action."""
    button = button_from_string(arguments.get("button", "left"))
    mouse_controller.press(button)
    result = {"success": True, "action": "button_down", "button": arguments.get("button", "left")}
    return format_response(result, state)


def handle_button_up(
    arguments: dict[str, Any],
    state: ComputerState,
    mouse_controller
) -> list[Union[TextContent, ImageContent]]:
    """Handle button_up action."""
    button = button_from_string(arguments.get("button", "left"))
    mouse_controller.release(button)
    result = {"success": True, "action": "button_up", "button": arguments.get("button", "left")}
    return format_response(result, state)


def handle_drag(
    arguments: dict[str, Any],
    state: ComputerState,
    mouse_controller
) -> list[Union[TextContent, ImageContent]]:
    """Handle drag action."""
    start = arguments["start"]
    end = arguments["end"]
    button = button_from_string(arguments.get("button", "left"))
    
    # Move to start, press button, move to end, release button
    mouse_controller.position = (start["x"], start["y"])
    mouse_controller.press(button)
    time.sleep(0.01)  # Small delay
    mouse_controller.position = (end["x"], end["y"])
    time.sleep(0.01)
    mouse_controller.release(button)
    
    result = {"success": True, "action": "drag", "start": start, "end": end, "button": arguments.get("button", "left")}
    return format_response(result, state)


def handle_mouse_move(
    arguments: dict[str, Any],
    state: ComputerState,
    mouse_controller
) -> list[Union[TextContent, ImageContent]]:
    """Handle mouse_move action."""
    x = arguments["x"]
    y = arguments["y"]
    mouse_controller.position = (x, y)
    result = {"success": True, "action": "mouse_move", "x": x, "y": y}
    return format_response(result, state)

