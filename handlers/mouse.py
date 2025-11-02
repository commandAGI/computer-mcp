"""Mouse action handlers."""

import json
import time
from typing import Any

from mcp.types import TextContent

from core.state import ComputerState
from core.utils import button_from_string


def handle_click(
    arguments: dict[str, Any],
    state: ComputerState,
    mouse_controller
) -> list[TextContent]:
    """Handle click action."""
    button = button_from_string(arguments.get("button", "left"))
    mouse_controller.click(button)
    result_state = state.get_state()
    result = {"success": True, "action": "click", "button": arguments.get("button", "left")}
    result.update(result_state)
    return [TextContent(type="text", text=json.dumps(result))]


def handle_double_click(
    arguments: dict[str, Any],
    state: ComputerState,
    mouse_controller
) -> list[TextContent]:
    """Handle double_click action."""
    button = button_from_string(arguments.get("button", "left"))
    mouse_controller.click(button, 2)
    result_state = state.get_state()
    result = {"success": True, "action": "double_click", "button": arguments.get("button", "left")}
    result.update(result_state)
    return [TextContent(type="text", text=json.dumps(result))]


def handle_triple_click(
    arguments: dict[str, Any],
    state: ComputerState,
    mouse_controller
) -> list[TextContent]:
    """Handle triple_click action."""
    button = button_from_string(arguments.get("button", "left"))
    mouse_controller.click(button, 3)
    result_state = state.get_state()
    result = {"success": True, "action": "triple_click", "button": arguments.get("button", "left")}
    result.update(result_state)
    return [TextContent(type="text", text=json.dumps(result))]


def handle_button_down(
    arguments: dict[str, Any],
    state: ComputerState,
    mouse_controller
) -> list[TextContent]:
    """Handle button_down action."""
    button = button_from_string(arguments.get("button", "left"))
    mouse_controller.press(button)
    result_state = state.get_state()
    result = {"success": True, "action": "button_down", "button": arguments.get("button", "left")}
    result.update(result_state)
    return [TextContent(type="text", text=json.dumps(result))]


def handle_button_up(
    arguments: dict[str, Any],
    state: ComputerState,
    mouse_controller
) -> list[TextContent]:
    """Handle button_up action."""
    button = button_from_string(arguments.get("button", "left"))
    mouse_controller.release(button)
    result_state = state.get_state()
    result = {"success": True, "action": "button_up", "button": arguments.get("button", "left")}
    result.update(result_state)
    return [TextContent(type="text", text=json.dumps(result))]


def handle_drag(
    arguments: dict[str, Any],
    state: ComputerState,
    mouse_controller
) -> list[TextContent]:
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
    
    result_state = state.get_state()
    result = {"success": True, "action": "drag", "start": start, "end": end, "button": arguments.get("button", "left")}
    result.update(result_state)
    return [TextContent(type="text", text=json.dumps(result))]


def handle_mouse_move(
    arguments: dict[str, Any],
    state: ComputerState,
    mouse_controller
) -> list[TextContent]:
    """Handle mouse_move action."""
    x = arguments["x"]
    y = arguments["y"]
    mouse_controller.position = (x, y)
    result_state = state.get_state()
    result = {"success": True, "action": "mouse_move", "x": x, "y": y}
    result.update(result_state)
    return [TextContent(type="text", text=json.dumps(result))]

